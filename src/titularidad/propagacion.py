"""Propagación de participaciones sobre el grafo (especificación §2, §3.1, §3.4 y §6).

Es el motor de cálculo, sin reglas de régimen: no aplica umbrales de
titularidad ni decide quién es titular real. Para capital y votos por separado
(C9) da:

- `preparar`: el grafo sobre el que se calcula, con C2 (por cuenta de otro), C3
  (aristas paralelas), C4 (huecos como titulares virtuales) y C1 (solo lo que
  llega a la entidad objetivo). Los ciclos que no convergen se tratan según el
  §6.4.
- `serie_completa`: método B, own_m(X, Y) resolviendo el sistema del §3.1.
- `cadenas_simples` y `enumerar_cadenas`: método A, solo cadenas que no repiten
  entidad.
- `base_directiva`: método C, votos agregados sobre la base de la Dir. 22.5
  (§3.4).
- `propagar`: los tres métodos sobre la entidad objetivo, con sus avisos.

Todo se calcula con fracciones exactas (C6). Los puntos que la especificación
no decide están marcados con «AMBIGÜEDAD:».
"""

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction

from titularidad.grafo import componentes_fuertes
from titularidad.modelo import MAGNITUDES, EntidadJuridica, Entrada, Incidencia, PersonaFisica, tolerancia_redondeo

CIEN = Fraction(100)
NO_IDENTIFICADO = "NO_IDENTIFICADO"
OPACA = "OPACA"


class FueraDeAlcance(ValueError):
    """La entidad objetivo no es una sociedad: no se calcula (especificación, C31)."""


@dataclass(frozen=True, order=True)
class Virtual:
    """Titular virtual (C4): se propaga como uno más, pero nunca es titular real.

    Es un tipo aparte, y no un texto, para que no pueda coincidir con el id de
    un nodo de la entrada.
    """

    clase: str
    entidad: str

    def __str__(self):
        return f"{self.clase}({self.entidad})"


@dataclass(frozen=True)
class Atribucion:
    """Arista `por_cuenta_de` atribuida al principal en una magnitud (C2).

    Es la marca «por cuenta de» que debe llevar la salida.
    """

    arista: str
    titular_formal: str
    principal: str
    participada: str
    magnitud: str


@dataclass(frozen=True)
class CicloCerrado:
    """Grupo de entidades cuya serie no converge en una magnitud (§6.4).

    `con_titulares_externos` es False en el caso normal (se tienen entre sí al
    100 %) y True en el caso límite: hay titulares de fuera, pero el exceso de
    redondeo de D15 impide que la serie converja.
    """

    magnitud: str
    entidades: tuple[str, ...]
    con_titulares_externos: bool


@dataclass(frozen=True)
class Grafo:
    """Grafo preparado. `h[m][(titular, participada)]` es h_m del §3.1, en %."""

    objetivo: str
    nodos: tuple[str, ...]  # todos los nodos de la entrada
    personas: frozenset[str]  # las personas físicas: las únicas que pueden ser titulares reales
    h: dict[str, dict[tuple, Fraction]]
    atribuciones: tuple[Atribucion, ...]
    ciclos_cerrados: tuple[CicloCerrado, ...]
    avisos: tuple[Incidencia, ...]

    def entidades(self, magnitud):
        """Entidades del subgrafo: las que tienen algún titular en esa magnitud."""
        return {y for _, y in self.h[magnitud]}

    def titulares(self, magnitud):
        """Todo lo que es origen de alguna arista: personas, entidades y virtuales."""
        return {z for z, _ in self.h[magnitud]}

    def virtuales(self):
        return {z for m in MAGNITUDES for z in self.titulares(m) if isinstance(z, Virtual)}


# --- Preparación (§2) ----------------------------------------------------------


def preparar(entrada: Entrada, c2_en=MAGNITUDES, detener=None) -> Grafo:
    """Construye el grafo sobre el que se calcula.

    `c2_en` son las magnitudes en las que las aristas `por_cuenta_de` se
    atribuyen al principal (C2). Por defecto, las dos. La lectura contraria de
    C29 es `()` en el AMLR y `("votos",)` en España.

    `detener` asigna a una entidad la clase de un titular virtual que recibe
    todo lo que le llega, sin recorrer sus titulares. Es el mecanismo de
    `OPACA` (C4), que se aplica solo, y el que necesitará el régimen español
    para `COTIZADA` (C5). El motor no decide qué entidades son cotizadas.

    Lanza FueraDeAlcance si la entidad objetivo no es una sociedad (C31).
    """
    objetivo = entrada.entidad_objetivo
    if entrada.nodos[objetivo].clase != "sociedad":
        raise FueraDeAlcance(
            f"La entidad objetivo «{objetivo}» es de clase «{entrada.nodos[objetivo].clase}»: "
            "v0.1 no tiene sus reglas y el resultado es «fuera de alcance» (C31)"
        )
    detener = dict(detener or {})
    for id_nodo, nodo in entrada.nodos.items():
        if isinstance(nodo, EntidadJuridica) and nodo.clase != "sociedad":
            detener.setdefault(id_nodo, OPACA)  # C4, solo entidades intermedias

    h, atribuciones, cerrados, avisos = {}, [], [], []
    for magnitud in MAGNITUDES:
        # Orden del §2 de la especificación: C2 y C3, lo que no se recorre,
        # C1, huecos, ciclos cerrados y C1 otra vez. C1 va después de C2: si
        # no, un principal sin participaciones propias quedaría fuera.
        aristas, atribuidas = _aristas(entrada, magnitud, magnitud in c2_en)
        _detener(aristas, detener)
        aristas = _subgrafo(aristas, objetivo)
        _huecos(aristas, entrada, magnitud, detener)
        for ciclo in _tratar_ciclos(aristas, magnitud):
            cerrados.append(ciclo)
            avisos.append(_aviso_ciclo(ciclo))
        h[magnitud] = _subgrafo(aristas, objetivo)
        atribuciones += [a for a in atribuidas if (a.principal, a.participada) in h[magnitud]]

    return Grafo(
        objetivo=objetivo,
        nodos=tuple(entrada.nodos),
        personas=frozenset(n for n, nodo in entrada.nodos.items() if isinstance(nodo, PersonaFisica)),
        h=h,
        atribuciones=tuple(atribuciones),
        ciclos_cerrados=tuple(cerrados),
        avisos=tuple(avisos),
    )


def _aristas(entrada, magnitud, con_c2):
    """h_m tras C2 (atribución al principal) y C3 (suma de aristas paralelas)."""
    h = defaultdict(Fraction)
    atribuciones = []
    for p in entrada.participaciones:
        valor = getattr(p, magnitud)
        if valor is None:
            # AMBIGÜEDAD: la especificación no dice qué hace el cálculo con una
            # magnitud desconocida (null, D5). Se trata como si la arista no
            # tuviera esa magnitud, así que su parte acaba en el hueco de la
            # participada (C4), como en la validación (AVI-02).
            continue
        titular = p.titular
        if con_c2 and p.por_cuenta_de is not None:
            titular = p.por_cuenta_de
            atribuciones.append(Atribucion(p.id, p.titular, p.por_cuenta_de, p.participada, magnitud))
        h[(titular, p.participada)] += Fraction(valor)
    return dict(h), atribuciones


def _detener(h, detener):
    """C4, OPACA (y C5, si el régimen lo pide): no se recorren sus titulares."""
    for (titular, participada) in list(h):
        if participada in detener:
            del h[(titular, participada)]
    for entidad, clase in detener.items():
        h[(Virtual(clase, entidad), entidad)] = CIEN


def _subgrafo(h, objetivo):
    """C1: solo las aristas de los nodos con un camino hasta el objetivo."""
    predecesores = defaultdict(set)
    for titular, participada in h:
        predecesores[participada].add(titular)
    alcanzados, pendientes = {objetivo}, [objetivo]
    while pendientes:
        for titular in predecesores[pendientes.pop()]:
            if titular not in alcanzados:
                alcanzados.add(titular)
                pendientes.append(titular)
    return {arista: v for arista, v in h.items() if arista[1] in alcanzados}


def _huecos(h, entrada, magnitud, detener):
    """C4: NO_IDENTIFICADO(X) con lo que falta para 100, fuera de la tolerancia de D15.

    Se mira toda entidad de la cadena, también las que no tienen titulares y
    solo aparecen como titular de otra (como E-FONDO en el ejemplo del modelo).
    """
    en_la_cadena = {n for arista in h for n in arista} | {entrada.entidad_objetivo}
    for entidad in en_la_cadena:
        if not isinstance(entrada.nodos.get(entidad), EntidadJuridica) or entidad in detener:
            continue
        suma = sum((v for (_, y), v in h.items() if y == entidad), Fraction(0))
        # D15 cuenta las aristas de la entrada con valor, antes de C2 y C3.
        n = sum(1 for p in entrada.participaciones if p.participada == entidad and getattr(p, magnitud) is not None)
        if suma < CIEN - Fraction(tolerancia_redondeo(n)):
            h[(Virtual(NO_IDENTIFICADO, entidad), entidad)] = CIEN - suma


def _tratar_ciclos(h, magnitud):
    """§6.4: detecta los grupos de entidades cuya serie no converge y los trata como hueco.

    La especificación pide detectarlos por la estructura: «ninguna tiene
    titulares de fuera del grupo, ni reales ni huecos», más el caso límite del
    redondeo. Aquí se hace con una comprobación exacta que cubre los dos: la
    serie de un grupo converge si y solo si I − A (A = participaciones internas
    / 100) tiene todos los pivotes positivos al eliminar sin pivotaje (es una
    M-matriz no singular). Si solo hay titulares internos al 100 %, un pivote es
    0; si el exceso de redondeo lo impide, un pivote es negativo.
    """
    for grupo in grupos_sin_convergencia(h):
        externos = any(v > 0 for (z, y), v in h.items() if y in grupo and z not in grupo)
        # AMBIGÜEDAD: el §6.4 dice que esas entidades «se tratan como un hueco
        # (NO_IDENTIFICADO)», pero no cómo. Se quitan las aristas internas del
        # grupo y cada entidad recibe NO_IDENTIFICADO(X) con lo que no tienen
        # sus titulares de fuera. Lo que el grupo tiene en otras entidades
        # llega a ellas a través de esos huecos.
        for (titular, participada) in list(h):
            if titular in grupo and participada in grupo:
                del h[(titular, participada)]
        for entidad in grupo:
            hueco = Virtual(NO_IDENTIFICADO, entidad)
            h.pop((hueco, entidad), None)
            fuera = sum((v for (_, y), v in h.items() if y == entidad), Fraction(0))
            if fuera < CIEN:
                h[(hueco, entidad)] = CIEN - fuera
        yield CicloCerrado(magnitud, tuple(sorted(grupo)), externos)


def grupos_sin_convergencia(h) -> list[set]:
    """Grupos de entidades en ciclo cuya serie no converge, con la comprobación
    exacta que describe `_tratar_ciclos`. Vacío si la serie converge en todo h."""
    entidades = {y for _, y in h}
    sucesores = defaultdict(list)
    reflexivas = set()
    for (titular, participada), valor in h.items():
        if valor > 0 and titular in entidades:
            sucesores[titular].append(participada)
            if titular == participada:
                reflexivas.add(titular)
    grupos = []
    for componente in componentes_fuertes(sorted(entidades), sucesores):
        grupo = set(componente)
        if len(grupo) == 1 and componente[0] not in reflexivas:
            continue
        if not _converge(h, sorted(grupo)):
            grupos.append(grupo)
    return grupos


def _converge(h, grupo):
    indice = {entidad: i for i, entidad in enumerate(grupo)}
    n = len(grupo)
    a = [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]
    for (titular, participada), valor in h.items():
        if titular in indice and participada in indice:
            a[indice[participada]][indice[titular]] -= valor / CIEN
    for k in range(n):
        if a[k][k] <= 0:
            return False
        for i in range(k + 1, n):
            factor = a[i][k] / a[k][k]
            if factor:
                a[i] = [x - factor * y for x, y in zip(a[i], a[k])]
    return True


def _aviso_ciclo(ciclo):
    motivo = (
        "hay titulares de fuera, pero el exceso de redondeo (D15) impide que la serie converja"
        if ciclo.con_titulares_externos
        else "sin titulares externos"
    )
    return Incidencia(
        "CICLO-CERRADO",
        f"Ciclo cerrado en «{ciclo.magnitud}» entre {', '.join(ciclo.entidades)}: {motivo}. "
        "Se trata como hueco (§6.4)",
        ciclo.entidades,
    )


# --- Método B: serie completa (§3.1, C8) ---------------------------------------


def serie_completa(grafo: Grafo, magnitud: str) -> dict:
    """own_m(X, Y) para cada origen X del subgrafo y cada entidad Y.

    Resuelve, para cada X, el sistema del §3.1 ignorando las aristas que
    entran en X. Los orígenes sin aristas de entrada (personas y virtuales)
    comparten matriz y se resuelven juntos.
    """
    return serie_sobre(grafo.h[magnitud])


def serie_sobre(h: dict) -> dict:
    """El método B sobre unos pesos cualesquiera, en %.

    Sirve para las lecturas que solo avisan y cambian los pesos de las
    aristas: la transparencia del control (§3.5) y el producto mixto (§7).
    Quien la llame debe comprobar antes la convergencia con
    `grupos_sin_convergencia`.
    """
    entidades = sorted({y for _, y in h})
    titulares = {z for z, _ in h}
    externos = sorted(titulares - set(entidades), key=str)
    resultado = {}

    if externos:
        soluciones = _resolver(h, entidades, [[h.get((x, y), 0) for y in entidades] for x in externos])
        for x, solucion in zip(externos, soluciones):
            resultado[x] = dict(zip(entidades, solucion))
    for x in entidades:
        if x not in titulares:
            continue
        resto = [y for y in entidades if y != x]
        (solucion,) = _resolver(h, resto, [[h.get((x, y), 0) for y in resto]])
        resultado[x] = dict(zip(resto, solucion))
    return resultado


def _resolver(h, incognitas, vectores):
    """Resuelve (I − A)·own = b para varios b, con A[y][z] = h(z, y) / 100."""
    indice = {y: i for i, y in enumerate(incognitas)}
    n, k = len(incognitas), len(vectores)
    filas = [[Fraction(int(i == j)) for j in range(n)] + [Fraction(v[i]) for v in vectores] for i in range(n)]
    for (titular, participada), valor in h.items():
        if titular in indice and participada in indice:
            filas[indice[participada]][indice[titular]] -= valor / CIEN
    for col in range(n):
        pivote = next(f for f in range(col, n) if filas[f][col] != 0)
        filas[col], filas[pivote] = filas[pivote], filas[col]
        for f in range(n):
            if f != col and filas[f][col] != 0:
                factor = filas[f][col] / filas[col][col]
                filas[f] = [x - factor * y for x, y in zip(filas[f], filas[col])]
    return [[filas[i][n + j] / filas[i][i] for i in range(n)] for j in range(k)]


# --- Método A: cadenas simples (§6.2, prueba de sensibilidad) ------------------


def enumerar_cadenas(grafo: Grafo, magnitud: str, origen, destino=None):
    """Cadenas de `origen` a `destino` que no repiten entidad, con su producto en %.

    Es también la explicación que pide C8: «las cadenas sin repeticiones».
    """
    # AMBIGÜEDAD: C8 pide listar además «lo que aporta cada ciclo», pero no
    # dice cómo repartir la diferencia entre el método B y el A cuando hay
    # varios ciclos que se cruzan. Solo se puede dar el total (B − A), y el
    # reparto por ciclo queda sin implementar.
    destino = grafo.objetivo if destino is None else destino
    sucesores = defaultdict(list)
    for (titular, participada), valor in grafo.h[magnitud].items():
        if valor:
            sucesores[titular].append((participada, valor))
    cadenas = []

    def recorrer(nodo, camino, producto):
        if nodo == destino:
            cadenas.append((tuple(camino), producto))
            return
        for siguiente, valor in sucesores[nodo]:
            if siguiente not in camino:
                recorrer(siguiente, camino + [siguiente], producto * valor / CIEN)

    recorrer(origen, [origen], CIEN)
    return cadenas


def cadenas_simples(grafo: Grafo, magnitud: str, destino=None) -> dict:
    """Método A: suma de las cadenas que no repiten entidad, para cada origen."""
    destino = grafo.objetivo if destino is None else destino
    return {
        x: sum((p for _, p in enumerar_cadenas(grafo, magnitud, x, destino)), Fraction(0))
        for x in grafo.titulares(magnitud)
        if x != destino
    }


# --- Método C: base de la Dir. 22.5 (§3.4, C12) --------------------------------


@dataclass(frozen=True)
class Dominio:
    """Resultado del cálculo de dominio del §3.4, solo con votos.

    Si no se estabiliza, `estable` es False y no hay dependientes: E2 queda
    como no determinable (DOMINIO-INESTABLE).
    """

    h: dict
    dependientes: dict
    estable: bool

    def base(self, y):
        """base(Y) = 100 − votos neutralizados de Y (los de Y y sus dependientes)."""
        neutralizados = {y} | self.dependientes.get(y, frozenset())
        return CIEN - sum((self.h.get((z, y), 0) for z in neutralizados), Fraction(0))

    def agregados(self, x, y):
        """va(X, Y): votos de X y sus dependientes en Y, sin los neutralizados de Y."""
        neutralizados = {y} | self.dependientes.get(y, frozenset())
        propios = ({x} | self.dependientes.get(x, frozenset())) - neutralizados
        return sum((self.h.get((z, y), 0) for z in propios), Fraction(0))

    def proporcion(self, x, y):
        """va(X, Y) · 100 / base(Y), o None si no se puede calcular."""
        base = self.base(y)
        if not self.estable or base <= 0:
            return None
        return self.agregados(x, y) * CIEN / base


def base_directiva(grafo: Grafo, inclusivo: bool = False) -> Dominio:
    """Método C: Dep(X) por rondas desde vacío hasta que no cambie (§3.4).

    El umbral de dominio (> 50, C10) es parte de la definición del método: el
    art. 42 que lo aplica solo se usa en España (L2), pero el método C es ese.
    Con `inclusivo`, el umbral pasa a ≥ 50: es la repetición de C28
    (UMBRAL-EXACTO).
    """
    supera = (lambda v: v >= 50) if inclusivo else (lambda v: v > 50)
    h = grafo.h["votos"]
    origenes = {z for z, _ in h}
    entidades = {y for _, y in h}
    dependientes = {x: frozenset() for x in origenes}
    vistos = set()
    while True:
        actual = Dominio(h, dependientes, True)
        # AMBIGÜEDAD: el §3.4 no dice qué pasa si base(Y) = 0, es decir, si
        # todos los votos de Y los tienen ella misma y sus dependientes. Se
        # entiende que entonces nadie domina Y, y la proporción en Y no se
        # puede calcular (None).
        nuevo = {
            x: frozenset(
                y for y in entidades - {x}
                if actual.base(y) > 0 and supera(actual.agregados(x, y) * CIEN / actual.base(y))
            )
            for x in origenes
        }
        if nuevo == dependientes:
            return actual
        estado = frozenset(nuevo.items())
        if estado in vistos:
            return Dominio(h, {}, False)
        vistos.add(estado)
        dependientes = nuevo


# --- Todo junto ----------------------------------------------------------------


@dataclass(frozen=True)
class Propagacion:
    """Participación de cada nodo en la entidad objetivo, por método y magnitud.

    Incluye todos los nodos de la entrada (0 si no llegan al objetivo) y los
    titulares virtuales. `directiva` es None si el dominio no se estabiliza o
    si la base del objetivo es 0.

    Los avisos son solo los comunes a los dos regímenes (CICLO-CERRADO). El
    método C solo lo usa España (L2), así que DOMINIO-INESTABLE lo da el
    módulo de control, entre los avisos españoles.
    """

    serie: dict[str, dict]  # método B: own_m(X, S)
    simples: dict[str, dict]  # método A
    directiva: dict | None  # método C, votos: va(X, S) · 100 / base(S)
    dominio: Dominio
    avisos: tuple[Incidencia, ...]


def propagar(grafo: Grafo) -> Propagacion:
    # AMBIGÜEDAD: el tratamiento de los ciclos cerrados (§6.4) está pensado
    # para el método B, que es el que no converge. Los métodos A y C se
    # calculan sobre el mismo grafo ya tratado, para que los tres comparen lo
    # mismo. Nadie de fuera llega a un ciclo cerrado, así que solo cambia la
    # participación de las entidades del propio ciclo.
    objetivo = grafo.objetivo
    todos = [n for n in grafo.nodos if n != objetivo] + sorted(grafo.virtuales(), key=str)

    serie, simples = {}, {}
    for magnitud in MAGNITUDES:
        own = serie_completa(grafo, magnitud)
        serie[magnitud] = {x: own.get(x, {}).get(objetivo, Fraction(0)) for x in todos}
        a = cadenas_simples(grafo, magnitud)
        simples[magnitud] = {x: a.get(x, Fraction(0)) for x in todos}

    dominio = base_directiva(grafo)
    directiva = None
    if dominio.estable and dominio.base(objetivo) > 0:
        directiva = {x: dominio.proporcion(x, objetivo) for x in todos}

    return Propagacion(serie, simples, directiva, dominio, grafo.avisos)
