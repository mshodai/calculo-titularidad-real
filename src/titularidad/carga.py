"""Lectura y validación de la entrada, según docs/modelo-datos.md v0.1.

`cargar` lee el JSON y devuelve un ResultadoCarga con la entrada validada (o
None si hay errores) y los errores y avisos del §6.2 del modelo. No calcula
nada: los avisos sobre el grafo (ciclos, huecos, nodos sin conexión) solo
describen la estructura.

Los puntos que el modelo deja sin decidir para la implementación están
marcados con «AMBIGÜEDAD:».
"""

import json
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from titularidad.modelo import (
    CLASES,
    MAGNITUDES,
    TIPOS_CARGO,
    VERSION_MODELO,
    Cargo,
    Cotizacion,
    Documento,
    EntidadJuridica,
    Entrada,
    Identificacion,
    Incidencia,
    Participacion,
    PersonaFisica,
    ResultadoCarga,
)

CIEN = Decimal(100)
RESOLUCION = Decimal("0.0001")  # D4: 4 decimales
MAX_DECIMALES = 4

_FECHA = re.compile(r"\d{4}-\d{2}-\d{2}")
_PAIS = re.compile(r"[A-Z]{2}")


def cargar(texto: str) -> ResultadoCarga:
    """Lee y valida una entrada en JSON."""
    return _Carga().ejecutar(texto)


def cargar_fichero(ruta) -> ResultadoCarga:
    return cargar(Path(ruta).read_text(encoding="utf-8"))


# --- Lectura del JSON --------------------------------------------------------


def _leer_json(texto):
    """Devuelve (datos, claves repetidas).

    Los números se leen como Decimal, nunca como float (D4). NaN e Infinity,
    que el módulo json acepta por defecto, se rechazan.
    """
    repetidas = []

    def objeto(pares):
        resultado = {}
        for clave, valor in pares:
            if clave in resultado:
                repetidas.append(clave)
            resultado[clave] = valor
        return resultado

    def constante(nombre):
        raise ValueError(f"{nombre} no es un número JSON válido")

    datos = json.loads(
        texto,
        parse_float=Decimal,
        parse_int=Decimal,
        parse_constant=constante,
        object_pairs_hook=objeto,
    )
    return datos, repetidas


def _decimales(valor: Decimal) -> int:
    """Decimales significativos del valor, sin contar los ceros finales.

    Se calcula sobre la tupla del Decimal, sin normalize(), que redondearía a
    la precisión del contexto y daría por buenos valores con más decimales.
    """
    _, digitos, exponente = valor.as_tuple()
    if not any(digitos):
        return 0
    digitos = list(digitos)
    while exponente < 0 and digitos[-1] == 0:
        digitos.pop()
        exponente += 1
    return max(0, -exponente)


# --- Validación --------------------------------------------------------------


class _Carga:
    def __init__(self):
        self.errores: list[Incidencia] = []
        self.avisos: list[Incidencia] = []
        self.declarados: set[str] = set()  # ids de nodo, aunque el nodo tenga errores
        self.nodos: dict = {}
        self.nulos: dict[int, set[str]] = {}  # posición de la arista → magnitudes a null

    def error(self, codigo, mensaje, *ids):
        self.errores.append(Incidencia(codigo, mensaje, ids))

    def aviso(self, codigo, mensaje, *ids, informativo=False):
        self.avisos.append(Incidencia(codigo, mensaje, ids, informativo))

    def ejecutar(self, texto):
        try:
            datos, repetidas = _leer_json(texto)
        except ValueError as e:
            # AMBIGÜEDAD: el modelo no tiene código para un JSON mal formado.
            # Se usa ERR-01, el error de estructura.
            self.error("ERR-01", f"El JSON no es válido: {e}")
            return self._resultado(None)

        for clave in repetidas:
            # AMBIGÜEDAD: el modelo no trata las claves repetidas en un mismo
            # objeto. El módulo json se quedaría en silencio con la última; se
            # rechazan como ERR-01 por la misma razón que D20 (erratas).
            self.error("ERR-01", f"La clave «{clave}» aparece repetida en un mismo objeto")

        if not self._objeto(
            datos,
            "La raíz",
            ("version_modelo", "fecha_referencia", "entidad_objetivo", "nodos", "participaciones"),
        ):
            return self._resultado(None)

        version = self._texto(datos, "version_modelo", "La raíz")
        if version is not None and version != VERSION_MODELO:
            # AMBIGÜEDAD: el modelo fija «"0.1"» pero no dice qué código lleva
            # otra versión. Se trata como un valor no válido (ERR-01).
            self.error("ERR-01", f"La raíz: «version_modelo» debe ser \"{VERSION_MODELO}\"")
        fecha = self._fecha(datos, "fecha_referencia", "La raíz")
        objetivo = self._texto(datos, "entidad_objetivo", "La raíz")
        lista_nodos = self._campo(datos, "nodos", "La raíz", list, "una lista") or []
        lista_aristas = self._campo(datos, "participaciones", "La raíz", list, "una lista") or []

        self.nodos = self._leer_nodos(lista_nodos)
        aristas = self._leer_aristas(lista_aristas)

        # AMBIGÜEDAD: D21 dice que los nodos sin conexión con el objetivo «se
        # ignoran», pero no si se validan. Se validan todos: un error en uno de
        # ellos (p. ej., una suma de más del 100 %) también rechaza la entrada.
        objetivo_valido = self._comprobar_objetivo(objetivo)
        self._comprobar_referencias(aristas)
        self._comprobar_aristas(aristas)
        self._comprobar_sumas(aristas)
        self._comprobar_cargos()

        self._aviso_ciclos(aristas)
        self._avisos_aristas(aristas)
        if objetivo_valido:
            self._avisos_cadena(objetivo, aristas)

        if self.errores:
            return self._resultado(None)
        entrada = Entrada(
            version_modelo=version,
            fecha_referencia=fecha,
            entidad_objetivo=objetivo,
            nodos=self.nodos,
            participaciones=tuple(p for p, _ in aristas),
        )
        return self._resultado(entrada)

    def _resultado(self, entrada):
        return ResultadoCarga(
            entrada=entrada,
            errores=tuple(sorted(self.errores, key=lambda i: i.codigo)),
            avisos=tuple(sorted(self.avisos, key=lambda i: i.codigo)),
        )

    # --- Campos (ERR-01) -----------------------------------------------------

    def _objeto(self, obj, donde, obligatorios, opcionales=()):
        """Comprueba que `obj` es un objeto con esos campos. Devuelve si lo es."""
        if not isinstance(obj, dict):
            self.error("ERR-01", f"{donde}: debe ser un objeto")
            return False
        for clave in obligatorios:
            if clave not in obj:
                self.error("ERR-01", f"{donde}: falta el campo obligatorio «{clave}»")
        for clave in obj:
            if clave not in obligatorios and clave not in opcionales:
                self.error("ERR-01", f"{donde}: campo desconocido «{clave}»")  # D20
        return True

    def _campo(self, obj, clave, donde, tipo, descripcion, nulo=False):
        """obj[clave] si existe y es del tipo; None si falta o no es válido.

        La falta de un campo obligatorio ya la anota `_objeto`.
        """
        if clave not in obj:
            return None
        valor = obj[clave]
        # AMBIGÜEDAD: el esquema admite null expresamente solo en `capital`,
        # `votos` y `por_cuenta_de`, y dice «objeto o ausente» en
        # `cotizacion`. Se lee que en los demás campos opcionales null no vale
        # y que hay que omitirlos.
        if valor is None and nulo:
            return None
        if not isinstance(valor, tipo):
            self.error("ERR-01", f"{donde}: «{clave}» debe ser {descripcion}")
            return None
        return valor

    def _texto(self, obj, clave, donde, nulo=False):
        return self._campo(obj, clave, donde, str, "un texto", nulo)

    def _fecha(self, obj, clave, donde):
        texto = self._texto(obj, clave, donde)
        if texto is None:
            return None
        try:
            if not _FECHA.fullmatch(texto):
                raise ValueError
            return date.fromisoformat(texto)
        except ValueError:
            self.error("ERR-01", f"{donde}: «{clave}» debe ser una fecha AAAA-MM-DD")
            return None

    def _pais(self, obj, clave, donde):
        texto = self._texto(obj, clave, donde)
        # AMBIGÜEDAD: el esquema pide ISO 3166-1 alfa-2, pero D18 dice que en
        # v0.1 solo se comprueban tipos. Se comprueba la forma (dos letras
        # mayúsculas), no que el código exista: eso exigiría una tabla de países.
        if texto is not None and not _PAIS.fullmatch(texto):
            self.error("ERR-01", f"{donde}: «{clave}» debe ser un código ISO 3166-1 alfa-2")
            return None
        return texto

    # --- Nodos ---------------------------------------------------------------

    def _leer_nodos(self, lista):
        nodos = {}
        for posicion, dato in enumerate(lista):
            donde = f"nodos[{posicion}]"
            if not isinstance(dato, dict):
                self.error("ERR-01", f"{donde}: debe ser un objeto")
                continue
            if isinstance(dato.get("id"), str):
                donde = f"Nodo «{dato['id']}»"
            tipo = dato.get("tipo")
            if tipo == "persona_fisica":
                nodo = self._leer_persona(dato, donde)
            elif tipo == "entidad_juridica":
                nodo = self._leer_entidad(dato, donde)
            else:
                self.error(
                    "ERR-01", f"{donde}: «tipo» debe ser \"persona_fisica\" o \"entidad_juridica\""
                )
                if isinstance(dato.get("id"), str):
                    self.declarados.add(dato["id"])
                continue
            if nodo.id is None:
                continue
            if nodo.id in self.declarados:
                self.error("ERR-02", f"El id de nodo «{nodo.id}» está repetido", nodo.id)
                continue
            self.declarados.add(nodo.id)
            nodos[nodo.id] = nodo
        return nodos

    def _leer_persona(self, dato, donde):
        self._objeto(dato, donde, ("id", "tipo", "nombre"), ("identificacion",))
        identificacion = None
        if "identificacion" in dato:
            identificacion = self._leer_identificacion(dato["identificacion"], donde)
        return PersonaFisica(
            id=self._texto(dato, "id", donde),
            nombre=self._texto(dato, "nombre", donde),
            identificacion=identificacion,
        )

    def _leer_identificacion(self, dato, donde):
        donde = f"{donde}, identificacion"
        # AMBIGÜEDAD: el §3.2 enumera los subcampos de `identificacion` sin dar
        # sus tipos ni cuáles son obligatorios. Se toman todos como opcionales
        # y como texto, salvo `nacionalidades` (lista de textos) y `documento`
        # (objeto). `fecha_nacimiento` no se valida como fecha: D18 dice que en
        # v0.1 solo se comprueban tipos.
        campos = (
            "fecha_nacimiento",
            "lugar_nacimiento",
            "documento",
            "pais_residencia",
            "nacionalidades",
            "domicilio",
            "email",
        )
        if not self._objeto(dato, donde, (), campos):
            return None
        documento = None
        if "documento" in dato:
            doc = dato["documento"]
            donde_doc = f"{donde}, documento"
            if self._objeto(doc, donde_doc, (), ("tipo", "numero", "pais_expedicion")):
                documento = Documento(
                    tipo=self._texto(doc, "tipo", donde_doc),
                    numero=self._texto(doc, "numero", donde_doc),
                    pais_expedicion=self._texto(doc, "pais_expedicion", donde_doc),
                )
        nacionalidades = self._campo(dato, "nacionalidades", donde, list, "una lista") or []
        if not all(isinstance(n, str) for n in nacionalidades):
            self.error("ERR-01", f"{donde}: «nacionalidades» debe ser una lista de textos")
            nacionalidades = []
        return Identificacion(
            fecha_nacimiento=self._texto(dato, "fecha_nacimiento", donde),
            lugar_nacimiento=self._texto(dato, "lugar_nacimiento", donde),
            documento=documento,
            pais_residencia=self._texto(dato, "pais_residencia", donde),
            nacionalidades=tuple(nacionalidades),
            domicilio=self._texto(dato, "domicilio", donde),
            email=self._texto(dato, "email", donde),
        )

    def _leer_entidad(self, dato, donde):
        self._objeto(
            dato,
            donde,
            ("id", "tipo", "denominacion", "clase"),
            ("forma_juridica", "pais", "nif", "euid", "cotizacion", "cargos"),
        )
        clase = self._texto(dato, "clase", donde)
        if clase is not None and clase not in CLASES:
            self.error("ERR-01", f"{donde}: «clase» debe ser uno de {', '.join(CLASES)}")
            clase = None

        cotizacion = None
        if "cotizacion" in dato:
            cot = dato["cotizacion"]
            donde_cot = f"{donde}, cotizacion"
            campos = ("mercado", "requisitos_informacion_ue_o_equivalentes")
            if self._objeto(cot, donde_cot, campos):
                cotizacion = Cotizacion(
                    mercado=self._texto(cot, "mercado", donde_cot),
                    requisitos_informacion_ue_o_equivalentes=self._campo(
                        cot, campos[1], donde_cot, bool, "true o false"
                    ),
                )

        cargos = []
        lista = self._campo(dato, "cargos", donde, list, "una lista") or []
        for posicion, cargo in enumerate(lista):
            leido = self._leer_cargo(cargo, f"{donde}, cargos[{posicion}]")
            if leido is not None:
                cargos.append(leido)

        return EntidadJuridica(
            id=self._texto(dato, "id", donde),
            denominacion=self._texto(dato, "denominacion", donde),
            clase=clase,
            forma_juridica=self._texto(dato, "forma_juridica", donde),
            pais=self._pais(dato, "pais", donde),
            nif=self._texto(dato, "nif", donde),
            euid=self._texto(dato, "euid", donde),
            cotizacion=cotizacion,
            cargos=tuple(cargos),
        )

    def _leer_cargo(self, dato, donde):
        if not self._objeto(dato, donde, ("persona", "cargo", "ejecutivo"), ("representante",)):
            return None
        cargo = self._texto(dato, "cargo", donde)
        if cargo is not None and cargo not in TIPOS_CARGO:
            self.error("ERR-01", f"{donde}: «cargo» debe ser uno de {', '.join(TIPOS_CARGO)}")
            cargo = None
        return Cargo(
            persona=self._texto(dato, "persona", donde),
            cargo=cargo,
            ejecutivo=self._campo(dato, "ejecutivo", donde, bool, "true o false"),
            representante=self._texto(dato, "representante", donde),
        )

    # --- Aristas -------------------------------------------------------------

    def _leer_aristas(self, lista):
        """Devuelve [(Participacion, posición)] de las aristas que son objetos."""
        aristas = []
        ids = set()
        for posicion, dato in enumerate(lista):
            donde = f"participaciones[{posicion}]"
            if isinstance(dato, dict) and isinstance(dato.get("id"), str):
                donde = f"Arista «{dato['id']}»"
            if not self._objeto(
                dato,
                donde,
                ("id", "titular", "participada", "capital", "votos"),
                ("por_cuenta_de", "desde", "fuente"),
            ):
                continue
            arista = Participacion(
                id=self._texto(dato, "id", donde),
                titular=self._texto(dato, "titular", donde),
                participada=self._texto(dato, "participada", donde),
                capital=self._porcentaje(dato, "capital", donde),
                votos=self._porcentaje(dato, "votos", donde),
                por_cuenta_de=self._texto(dato, "por_cuenta_de", donde, nulo=True),
                desde=self._fecha(dato, "desde", donde),
                fuente=self._texto(dato, "fuente", donde),
            )
            self.nulos[posicion] = {m for m in MAGNITUDES if m in dato and dato[m] is None}
            if arista.id is not None:
                if arista.id in ids:
                    self.error("ERR-02", f"El id de arista «{arista.id}» está repetido", arista.id)
                ids.add(arista.id)
            aristas.append((arista, posicion))
        return aristas

    def _porcentaje(self, dato, clave, donde):
        """Porcentaje como Decimal (D4); None si es null o no es válido."""
        valor = self._campo(dato, clave, donde, Decimal, "un número o null", nulo=True)
        if valor is None:
            return None
        # AMBIGÜEDAD: ERR-06 dice «tiene más de 4 decimales» y no aclara si
        # cuentan los ceros finales. Se cuentan los decimales del valor, no los
        # escritos: 25.00000 vale exactamente 25 y se acepta.
        if not (0 <= valor <= CIEN) or _decimales(valor) > MAX_DECIMALES:
            ref = (dato["id"],) if isinstance(dato.get("id"), str) else ()
            self.error(
                "ERR-06",
                f"{donde}: «{clave}» vale {valor}; debe estar en [0, 100] con 4 decimales como máximo",
                *ref,
            )
            return None
        return valor

    # --- Comprobaciones entre objetos ----------------------------------------

    def _comprobar_objetivo(self, objetivo):
        """ERR-03. Devuelve si la entidad objetivo es válida."""
        if objetivo is None:
            return False
        if objetivo not in self.declarados:
            self.error("ERR-03", f"La entidad objetivo «{objetivo}» no existe", objetivo)
            return False
        if not isinstance(self.nodos.get(objetivo), EntidadJuridica):
            if objetivo in self.nodos:
                self.error(
                    "ERR-03", f"La entidad objetivo «{objetivo}» no es una entidad jurídica", objetivo
                )
            return False
        return True

    def _existe(self, id_nodo, donde, campo, *ids):
        """ERR-04 si `id_nodo` no es un nodo declarado."""
        if id_nodo is not None and id_nodo not in self.declarados:
            self.error("ERR-04", f"{donde}: «{campo}» apunta a «{id_nodo}», que no existe", *ids)
            return False
        return id_nodo is not None

    def _comprobar_referencias(self, aristas):
        for arista, posicion in aristas:
            donde = f"Arista «{arista.id}»" if arista.id else f"participaciones[{posicion}]"
            ref = (arista.id,) if arista.id else ()
            self._existe(arista.titular, donde, "titular", *ref)
            self._existe(arista.por_cuenta_de, donde, "por_cuenta_de", *ref)
            if self._existe(arista.participada, donde, "participada", *ref):
                if isinstance(self.nodos.get(arista.participada), PersonaFisica):
                    self.error(
                        "ERR-05",
                        f"{donde}: la participada «{arista.participada}» es una persona física",
                        *ref,
                    )
        for entidad in self._entidades():
            for cargo in entidad.cargos:
                donde = f"Nodo «{entidad.id}», cargo de «{cargo.persona}»"
                self._existe(cargo.persona, donde, "persona", entidad.id)
                self._existe(cargo.representante, donde, "representante", entidad.id)

    def _comprobar_aristas(self, aristas):
        """ERR-07, ERR-08 y ERR-11."""
        combinaciones = set()
        for arista, posicion in aristas:
            donde = f"Arista «{arista.id}»" if arista.id else f"participaciones[{posicion}]"
            ref = (arista.id,) if arista.id else ()
            if self.nulos[posicion] == set(MAGNITUDES):
                self.error("ERR-07", f"{donde}: «capital» y «votos» son los dos null", *ref)

            if arista.titular is not None and arista.participada is not None:
                combinacion = (arista.titular, arista.participada, arista.por_cuenta_de)
                if combinacion in combinaciones:
                    self.error(
                        "ERR-08",
                        f"{donde}: ya hay otra arista de «{arista.titular}» en "
                        f"«{arista.participada}» con el mismo «por_cuenta_de»",
                        *ref,
                    )
                combinaciones.add(combinacion)

            if arista.por_cuenta_de is not None:
                if arista.por_cuenta_de == arista.titular:
                    self.error("ERR-11", f"{donde}: «por_cuenta_de» es igual a «titular»", *ref)
                elif arista.titular is not None and arista.titular == arista.participada:
                    self.error(
                        "ERR-11", f"{donde}: una arista reflexiva no puede llevar «por_cuenta_de»", *ref
                    )

    def _comprobar_sumas(self, aristas):
        """ERR-09 y ERR-10: más del 100 %, salvo el exceso de redondeo (D15)."""
        valores = defaultdict(list)
        for arista, _ in aristas:
            for magnitud in MAGNITUDES:
                valor = getattr(arista, magnitud)
                if valor is not None and arista.participada is not None:
                    valores[(arista.participada, magnitud)].append(valor)
        for (entidad, magnitud), lista in valores.items():
            suma = sum(lista, Decimal(0))
            limite = CIEN + (len(lista) // 2) * RESOLUCION
            if suma > limite:
                codigo = "ERR-09" if magnitud == "capital" else "ERR-10"
                self.error(
                    codigo,
                    f"La suma de «{magnitud}» en «{entidad}» es {suma:f}; con {len(lista)} "
                    f"aristas el máximo admitido es {limite:f}",
                    entidad,
                )

    def _comprobar_cargos(self):
        """ERR-12: un cargo ocupado por una entidad necesita representante persona física."""
        for entidad in self._entidades():
            for cargo in entidad.cargos:
                ocupante = self.nodos.get(cargo.persona)
                if isinstance(ocupante, EntidadJuridica):
                    if cargo.representante is None:
                        self.error(
                            "ERR-12",
                            f"Nodo «{entidad.id}»: el cargo lo ocupa la entidad "
                            f"«{cargo.persona}» y no tiene «representante»",
                            entidad.id,
                        )
                    elif isinstance(self.nodos.get(cargo.representante), EntidadJuridica):
                        self.error(
                            "ERR-12",
                            f"Nodo «{entidad.id}»: el representante «{cargo.representante}» "
                            "no es una persona física",
                            entidad.id,
                        )
                # AMBIGÜEDAD: el modelo no dice qué pasa si un cargo ocupado
                # por una persona física lleva `representante`. No hay regla
                # que lo prohíba, así que se acepta sin aviso.

    def _entidades(self):
        return [n for n in self.nodos.values() if isinstance(n, EntidadJuridica)]

    # --- Avisos --------------------------------------------------------------

    def _aviso_ciclos(self, aristas):
        """AVI-01: un aviso por cada grupo de nodos en ciclo, incluida la arista reflexiva."""
        # AMBIGÜEDAD: el modelo no dice sobre qué aristas se buscan los ciclos
        # ni cómo se agrupan. Se usan las aristas tal como vienen, con su
        # titular formal (sin atribuir las `por_cuenta_de` al principal), todas
        # aunque valgan 0, y también en la parte del grafo no conectada con el
        # objetivo. Se da un aviso por componente fuertemente conexa, con sus
        # nodos, y no uno por cada ciclo elemental, que pueden ser muchísimos.
        sucesores = defaultdict(list)
        reflexivos = set()
        for arista, _ in aristas:
            if arista.titular in self.nodos and arista.participada in self.nodos:
                sucesores[arista.titular].append(arista.participada)
                if arista.titular == arista.participada:
                    reflexivos.add(arista.titular)
        orden = {id_nodo: i for i, id_nodo in enumerate(self.nodos)}
        for componente in _componentes_fuertes(list(self.nodos), sucesores):
            if len(componente) > 1 or componente[0] in reflexivos:
                ids = tuple(sorted(componente, key=orden.get))
                self.aviso("AVI-01", f"Hay un ciclo entre: {', '.join(ids)}", *ids)

    def _avisos_aristas(self, aristas):
        """AVI-04 y AVI-06, que no dependen de la entidad objetivo."""
        for arista, posicion in aristas:
            donde = f"Arista «{arista.id}»" if arista.id else f"participaciones[{posicion}]"
            ref = (arista.id,) if arista.id else ()
            if len(self.nulos[posicion]) == 1:
                (magnitud,) = self.nulos[posicion]
                self.aviso("AVI-04", f"{donde}: «{magnitud}» es null (desconocido)", *ref)
            if arista.por_cuenta_de is not None:
                self.aviso(
                    "AVI-06",
                    f"{donde}: se tiene por cuenta de «{arista.por_cuenta_de}»; "
                    "su tratamiento depende del régimen",
                    *ref,
                )

    def _avisos_cadena(self, objetivo, aristas):
        """AVI-02, AVI-03, AVI-05, AVI-07 y AVI-08."""
        cadena = _cadena(objetivo, [a for a, _ in aristas], self.nodos)

        # AMBIGÜEDAD: «en la cadena» es «tiene un camino de aristas que llega
        # hasta la entidad objetivo» (§6.2). Se incluye la propia entidad
        # objetivo (camino vacío), porque también puede tener un hueco, no tener
        # titulares o no ser una sociedad.
        sumas = defaultdict(lambda: Decimal(0))
        titulares = defaultdict(int)
        for arista, _ in aristas:
            titulares[arista.participada] += 1
            for magnitud in MAGNITUDES:
                valor = getattr(arista, magnitud)
                if valor is not None:
                    sumas[(arista.participada, magnitud)] += valor

        for entidad in self._entidades():
            if entidad.id not in cadena:
                continue
            # AMBIGÜEDAD: «cotiza» se lee como «tiene `cotizacion`», sin mirar
            # `requisitos_informacion_ue_o_equivalentes`, que solo importa para
            # la excepción de la Ley 4.2.b, párr. 3.
            cotiza = entidad.cotizacion is not None
            for magnitud in MAGNITUDES:
                suma = sumas[(entidad.id, magnitud)]
                # AMBIGÜEDAD: D15 da tolerancia de redondeo solo por encima del
                # 100. Por debajo no dice nada, así que tres tercios redondeados
                # (99,9999) dan aviso. Las aristas con la magnitud a null no
                # suman: su parte cuenta como sin identificar, y ya tienen AVI-04.
                if suma < CIEN:
                    self.aviso(
                        "AVI-02",
                        f"«{entidad.id}»: la suma de «{magnitud}» es {suma:f}; "
                        f"quedan {CIEN - suma:f} sin identificar",
                        entidad.id,
                        informativo=cotiza,
                    )
            if titulares[entidad.id] == 0 and not cotiza:
                self.aviso(
                    "AVI-03",
                    f"«{entidad.id}» no tiene titulares y no cotiza: la cadena termina sin "
                    "llegar a una persona física",
                    entidad.id,
                )
            if entidad.clase is not None and entidad.clase != "sociedad":
                self.aviso(
                    "AVI-05",
                    f"«{entidad.id}» es de clase «{entidad.clase}»: fuera del alcance de v0.1",
                    entidad.id,
                )

        destino = self.nodos[objetivo]
        if not destino.cargos:
            self.aviso(
                "AVI-07",
                f"La entidad objetivo «{objetivo}» no tiene cargos: no se puede aplicar "
                "el supuesto supletorio",
                objetivo,
            )

        conectados = set(cadena)
        for cargo in destino.cargos:
            conectados |= {cargo.persona, cargo.representante}
        # AMBIGÜEDAD: los cargos de las demás entidades no conectan a nadie
        # con el objetivo: el §3.3 dice que solo se usan en la entidad objetivo.
        for id_nodo in self.nodos:
            if id_nodo not in conectados:
                self.aviso(
                    "AVI-08",
                    f"«{id_nodo}» no está conectado con la entidad objetivo: se ignora",
                    id_nodo,
                )


def _cadena(objetivo, aristas, nodos):
    """Nodos con un camino de aristas hasta el objetivo, este incluido."""
    # AMBIGÜEDAD: el §6.2 define la conexión con «un camino de aristas», pero
    # no dice si una arista hacia arriba (el objetivo participa en otra
    # entidad sin que esta llegue a él) conecta, ni si el principal de una
    # `por_cuenta_de` está conectado. Se sigue la especificación del cálculo
    # (§2.1, C1): solo cuentan los caminos hacia el objetivo, y el principal
    # cuenta como si fuera titular de la arista, que es lo que hará C2.
    predecesores = defaultdict(set)
    for arista in aristas:
        if arista.participada in nodos:
            for titular in (arista.titular, arista.por_cuenta_de):
                if titular in nodos:
                    predecesores[arista.participada].add(titular)
    cadena, pendientes = {objetivo}, [objetivo]
    while pendientes:
        for titular in predecesores[pendientes.pop()]:
            if titular not in cadena:
                cadena.add(titular)
                pendientes.append(titular)
    return cadena


def _componentes_fuertes(nodos, sucesores):
    """Componentes fuertemente conexas (Tarjan, sin recursión)."""
    indice, bajo, en_pila, pila, componentes = {}, {}, set(), [], []
    for raiz in nodos:
        if raiz in indice:
            continue
        indice[raiz] = bajo[raiz] = len(indice)
        pila.append(raiz)
        en_pila.add(raiz)
        trabajo = [(raiz, iter(sucesores[raiz]))]
        while trabajo:
            nodo, hijos = trabajo[-1]
            for hijo in hijos:
                if hijo not in indice:
                    indice[hijo] = bajo[hijo] = len(indice)
                    pila.append(hijo)
                    en_pila.add(hijo)
                    trabajo.append((hijo, iter(sucesores[hijo])))
                    break
                if hijo in en_pila:
                    bajo[nodo] = min(bajo[nodo], indice[hijo])
            else:
                trabajo.pop()
                if trabajo:
                    padre = trabajo[-1][0]
                    bajo[padre] = min(bajo[padre], bajo[nodo])
                if bajo[nodo] == indice[nodo]:
                    componente = []
                    while True:
                        miembro = pila.pop()
                        en_pila.discard(miembro)
                        componente.append(miembro)
                        if miembro == nodo:
                            break
                    componentes.append(componente)
    return componentes
