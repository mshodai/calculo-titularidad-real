"""La salida: los dos regímenes y la comparación entre ellos (especificación §9).

`informe` calcula los dos regímenes sobre una entrada ya cargada, y `texto` y
`como_json` lo presentan. El informe es un cálculo bajo lecturas declaradas,
no una determinación jurídica, y la redacción lo dice: los titulares son
«titulares según las lecturas aplicadas», cada aviso lleva el caso que la
norma no resuelve, y al final se listan las lecturas de las que depende.
"""

import json
from dataclasses import dataclass
from fractions import Fraction

from titularidad import amlr, espana
from titularidad.formato import porcentaje
from titularidad.modelo import MAGNITUDES, Incidencia, ResultadoCarga

ESPANA = "España"
AMLR = "AMLR"

ADVERTENCIA = (
    "Resultado de un cálculo bajo las lecturas que declara la especificación (docs/especificacion-calculo.md), "
    "no una determinación jurídica. Donde la norma no resuelve un caso, se indica con su número (N…), y otra "
    "lectura podría dar otro resultado. Las decisiones de la especificación se citan como C…."
)

# Casos que la norma no resuelve (§12), en una línea.
CASOS_NO_RESUELTOS = {
    "N1": "España: método para la participación indirecta",
    "N2": "España: si el art. 42 sirve para medir el porcentaje que alguien «controla»",
    "N3": "AMLR: si el art. 54 sustituye al 52.1 o se añade a él",
    "N4": "AMLR: cadenas con varios tramos de control",
    "N5": "AMLR 54.a: si se suma la participación directa propia",
    "N6": "mezcla de capital y votos dentro de una cadena",
    "N7": "ciclos de participación",
    "N8": "AMLR: control a través de varias entidades controladas",
    "N9": "AMLR: si lo que tiene un nominatario es propiedad del nominador",
    "N12": "AMLR: si la autocartera se descuenta al decidir el control",
    "N13": "España: a quién se atribuye el capital de una participación por cuenta de otro",
    "N14": "España: cómo se mide la «filial participada mayoritariamente» del RD 9.4",
}

# Aviso → casos no resueltos que señala, por régimen (§9 y §12).
CASOS_POR_AVISO = {
    "POS-T": {ESPANA: ("N1", "N2"), AMLR: ("N4", "N5")},
    "T-NO-CONVERGE": {ESPANA: ("N1", "N2"), AMLR: ("N4", "N5")},
    "POS-AGREGADO": {AMLR: ("N8",)},
    "POS-MEZCLA": {ESPANA: ("N6",), AMLR: ("N6",)},
    "POS-FORMAL": {ESPANA: ("N13",), AMLR: ("N9",)},
    "CICLO-SENS": {ESPANA: ("N7",), AMLR: ("N7", "N12")},  # N12 es del AMLR: en España la autocartera la
                                                          # descuenta la base de la Dir. 22.5
    "CICLO-CERRADO": {ESPANA: ("N7",), AMLR: ("N7",)},
    "ART54-SENS": {AMLR: ("N3",)},
    "EXENCION-SENS": {ESPANA: ("N14",)},
}

# Avisos que no corresponden a un caso de la norma: de qué vienen.
ORIGEN_DE_OTROS_AVISOS = {
    "POS-HUECO": "estructura incompleta: faltan titulares en la entrada (C4)",
    "H1": "estructura incompleta: faltan titulares en la entrada (C4)",
    "H2": "estructura incompleta: faltan titulares en la entrada (C4)",
    "UMBRAL-EXACTO": "límite de los datos: porcentajes con 4 decimales (modelo, D23; C28)",
    "UMBRAL-EXACTO-NO-COMPROBADO": "límite de los datos: porcentajes con 4 decimales (modelo, D23; C28)",
    "DOMINIO-INESTABLE": "el dominio del art. 42 no se estabiliza con estos datos (§3.4)",
    "AMLR-NO-APLICABLE": "fecha de aplicación del AMLR (art. 90, C7)",
    "COTIZADA": "información: lo que llega por cotizadas no se recorre (RD 9.4, C5)",
    "CARGO-EJECUTIVO-ENTIDAD": "cargo ejecutivo ocupado por una entidad (C23)",
}

# Lecturas aplicadas en cada régimen (§5.3, §4.2, §2, §6.2): siempre intervienen.
LECTURAS = {
    ESPANA: (
        "Titular real: más del 25 % por multiplicación (L1, C17) o por votos agregados del art. 42 sobre la "
        "base de la Dir. 22.5 (L2, C12 y C18); se aplica la unión de las dos (C19).",
        "Control: dominio por mayoría estricta de votos (C10), con la agregación del art. 42 (C12).",
    ),
    AMLR: (
        "Titular real: 25 % o más por alguna de las pruebas A1 a A4; se aplica la unión de pruebas (C14).",
        "Control: más del 50 % del capital o de los votos, directo o indirecto, en cada nivel (C11).",
    ),
}
LECTURAS_COMUNES = (
    "Participación indirecta: cadenas multiplicadas y sumadas; con ciclos, la serie completa (C8, C20).",
    "Participaciones por cuenta de otro: se atribuyen al principal (C2).",
    "Lo que no llega a una persona física identificada: titulares virtuales, que nunca son titulares reales (C4).",
)

# Por qué una prueba de un régimen no tiene equivalente en el otro.
MOTIVO_SOLO_AMLR = {
    "A2": "controla la entidad por participación (53.2.c: capital o votos); en España el control es "
          "dominio por votos (art. 42)",
    "A3": "el art. 54.a le atribuye entera la participación directa de las entidades que controla; en España "
          "eso solo pasa si las domina por votos (L2)",
    "A4": "el art. 54.b le basta con el 25 % de una entidad que controla la sociedad; España no tiene esa "
          "regla (la lectura extensiva L3 solo avisa, C19)",
}
MOTIVO_SOLO_ESPANA = {
    "E2": "la agregación del art. 42 (L2) le atribuye enteros los votos de las sociedades que domina; en el "
          "AMLR no cumple ninguna de las pruebas A1 a A4",
}


@dataclass(frozen=True)
class Fila:
    """Una persona en la comparación."""

    persona: str
    espana: str  # «titular», «posible» o «no»
    detalle_espana: tuple[str, ...]  # pruebas (E1, E2) o códigos POS
    amlr: str
    detalle_amlr: tuple[str, ...]  # pruebas (A1 a A4) o códigos POS

    @property
    def difiere(self) -> bool:
        return (self.espana == "titular") != (self.amlr == "titular")


@dataclass(frozen=True)
class Informe:
    objetivo: str
    fecha: object
    errores: tuple[Incidencia, ...]  # de la validación: si hay, no se calcula
    avisos_entrada: tuple[Incidencia, ...]
    espana: espana.ResultadoEspana | None
    amlr: amlr.ResultadoAmlr | None
    filas: tuple[Fila, ...]
    diferencias: tuple[str, ...]


# --- Cálculo ------------------------------------------------------------------------------


def informe(carga: ResultadoCarga) -> Informe:
    """Calcula los dos regímenes y los compara. Si la entrada no es válida, solo lleva los errores."""
    if carga.entrada is None:
        return Informe("", None, carga.errores, carga.avisos, None, None, (), ())
    entrada = carga.entrada
    r_es, r_amlr = espana.calcular_espana(entrada), amlr.calcular_amlr(entrada)
    filas = _filas(r_es, r_amlr)
    return Informe(entrada.entidad_objetivo, entrada.fecha_referencia, (), carga.avisos, r_es, r_amlr, filas,
                   _diferencias(r_es, r_amlr, filas))


def _estado_por_persona(titulares, posibles, pruebas_de):
    estado = {t.persona: ("titular", pruebas_de(t)) for t in titulares}
    for p in posibles:
        for persona in p.ids:
            resultado, codigos = estado.get(persona, ("posible", ()))
            if resultado == "posible":
                estado[persona] = ("posible", tuple(sorted(set(codigos) | {p.codigo})))
    return estado


def _filas(r_es, r_amlr):
    es = _estado_por_persona(r_es.titulares, r_es.posibles, lambda t: tuple(sorted(t.pruebas)))
    am = _estado_por_persona(r_amlr.titulares, r_amlr.posibles, lambda t: tuple(sorted(t.pruebas.cumplidas)))
    return tuple(Fila(p, *es.get(p, ("no", ())), *am.get(p, ("no", ()))) for p in sorted(set(es) | set(am)))


def _diferencias(r_es, r_amlr, filas):
    """En qué difieren los dos regímenes, persona a persona, con la regla que lo explica."""
    diferencias = []
    if r_es.estado != r_amlr.estado:
        diferencias.append(f"Estado: en España «{r_es.estado}» ({r_es.motivo}); en el AMLR «{r_amlr.estado}».")
    t_es = {t.persona: t for t in r_es.titulares}
    t_am = {t.persona: t for t in r_amlr.titulares}
    for fila in filas:
        p = fila.persona
        if p in t_am and p not in t_es:
            if r_es.estado in (espana.EXCEPTUADA, espana.FUERA_DE_ALCANCE):
                diferencias.append(f"«{p}» cumple {_lista(fila.detalle_amlr)} en el AMLR; en España no se "
                                   f"calcula («{r_es.estado}»).")
                continue
            motivos = [MOTIVO_SOLO_AMLR[a] for a in fila.detalle_amlr if a in MOTIVO_SOLO_AMLR]
            a1 = t_am[p].pruebas.a1
            if a1 and all(v <= 25 for v in a1.values()):
                motivos.insert(0, "alcanza exactamente el 25 %: el AMLR pide «25 % o más» y España «superior al 25»")
            elif a1:
                motivos.insert(0, f"llega a {_valores(a1)} en el AMLR y no pasa del 25 % en España")
            posible = f" En España queda como posible ({_lista(fila.detalle_espana)})." if fila.espana == "posible" else ""
            diferencias.append(f"«{p}» cumple {_lista(fila.detalle_amlr)} en el AMLR y no es titular en España: "
                               + "; ".join(motivos) + "." + posible)
        elif p in t_es and p not in t_am:
            motivos = [MOTIVO_SOLO_ESPANA[e] for e in fila.detalle_espana if e in MOTIVO_SOLO_ESPANA]
            posible = f" En el AMLR queda como posible ({_lista(fila.detalle_amlr)})." if fila.amlr == "posible" else ""
            diferencias.append(f"«{p}» cumple {_lista(fila.detalle_espana)} en España y no es titular en el AMLR: "
                               + ("; ".join(motivos) or "no cumple ninguna de las pruebas A1 a A4") + "." + posible)
        elif p in t_es and p in t_am:
            controla_es, controla_am = t_es[p].controla, t_am[p].pruebas.a2
            if controla_es != controla_am:
                donde, no = ("España (CCom 42.1.a)", "el AMLR") if controla_es else ("el AMLR (53.2.c)", "España")
                diferencias.append(f"«{p}» es titular en los dos, con distinto criterio: controla la entidad en "
                                   f"{donde} y no en {no}.")
    return tuple(diferencias)


# --- Texto ---------------------------------------------------------------------------------


def texto(inf: Informe) -> str:
    if inf.errores:
        lineas = ["La entrada no es válida: no se calcula.", ""]
        lineas += [f"  {e.codigo}  {e.mensaje}" for e in inf.errores]
        return "\n".join(lineas) + "\n"

    lineas = [f"Titularidad real de «{inf.objetivo}» a {inf.fecha}", "", _envolver(ADVERTENCIA, 0), ""]

    lineas += ["ESTADO", f"  {ESPANA:<7} {inf.espana.estado}", f"  {AMLR:<7} {inf.amlr.estado}"]
    if inf.espana.estado != inf.amlr.estado:
        lineas.append("  ≠ Los dos regímenes llegan a estados distintos.")
    lineas.append("")

    lineas += ["COMPARACIÓN (según las lecturas aplicadas)"]
    if inf.filas:
        lineas += _tabla(inf.filas)
        distintas = sum(f.difiere for f in inf.filas)
        if distintas:
            total = len(inf.filas)
            lineas.append(f"  ≠ Resultado distinto en cada régimen para {distintas} de {total} "
                          f"{'persona' if total == 1 else 'personas'}.")
        else:
            lineas.append("  Los dos regímenes coinciden en quién es titular real.")
    else:
        lineas.append("  Nadie aparece como titular ni como posible titular en ningún régimen.")
    lineas.append("")

    lineas.append("EN QUÉ DIFIEREN")
    lineas += [_envolver(d, 2, "- ") for d in inf.diferencias] or ["  En nada de lo que se calcula."]
    lineas.append("")

    lineas += _seccion_espana(inf.espana) + [""] + _seccion_amlr(inf.amlr) + [""]
    lineas += _seccion_lecturas(inf)
    if inf.avisos_entrada:
        lineas += ["", "AVISOS DE LA VALIDACIÓN DE LA ENTRADA (modelo de datos, §6.2)"]
        lineas += [_envolver(f"{a.codigo}  {a.mensaje}", 2) for a in inf.avisos_entrada]
    return "\n".join(lineas) + "\n"


def _tabla(filas):
    ancho = max(len("Persona"), *(len(f.persona) for f in filas))
    celdas = [(f.persona, _celda(f.espana, f.detalle_espana), _celda(f.amlr, f.detalle_amlr), "≠" if f.difiere else "")
              for f in filas]
    ancho_es = max(len(ESPANA), *(len(c[1]) for c in celdas))
    lineas = [f"  {'Persona':<{ancho}}  {ESPANA:<{ancho_es}}  {AMLR}"]
    lineas += [f"  {p:<{ancho}}  {es:<{ancho_es}}  {am:<{max(len(c[2]) for c in celdas)}}  {marca}".rstrip()
               for p, es, am, marca in celdas]
    return lineas


def _celda(estado, detalle):
    if estado == "titular":
        return f"titular ({', '.join(detalle)})"
    if estado == "posible":
        return f"posible ({', '.join(detalle)})"
    return "—"


def _seccion_espana(r):
    lineas = ["ESPAÑA · Ley 10/2010, art. 4.2.b y b bis"]
    lineas.append(_envolver(f"Estado: {r.estado}. {r.motivo}.", 2))
    if r.titulares:
        lineas.append("  Titulares reales según las lecturas aplicadas:")
        for t in r.titulares:
            partes = []
            if "E1" in t.pruebas:
                partes.append(f"E1 (L1) {_valores(t.participacion)}")
            if "E2" in t.pruebas:
                partes.append(f"E2 (L2) {porcentaje(t.agregado)} %")
            if t.controla:
                partes.append("controla la entidad (CCom 42.1.a)")
            lineas.append(_envolver(f"{t.persona}: " + "; ".join(partes) + _marca(t.por_cuenta_de), 4))
    if r.administradores:
        lineas.append(_envolver("Administradores a los que se presume el control (Ley 4.2.b bis, C22): "
                                + ", ".join(r.administradores), 2))
    lineas += _incidencias("Posibles titulares", r.posibles, ESPANA)
    lineas += _incidencias("Avisos", r.avisos, ESPANA)
    return lineas


def _seccion_amlr(r):
    lineas = ["AMLR · Reglamento (UE) 2024/1624, arts. 51 a 54"]
    lineas.append(_envolver(f"Estado: {r.estado}. {r.motivo}.", 2))
    if r.titulares:
        lineas.append("  Titulares reales según las lecturas aplicadas:")
        for t in r.titulares:
            pr = t.pruebas
            partes = []
            if pr.a1:
                partes.append(f"A1 (52.1) {_valores(pr.a1)}")
            if pr.a2:
                partes.append("A2 (53.2) controla la entidad")
            if pr.a3:
                partes.append(f"A3 (54.a) {_valores(pr.a3)} de las entidades que controla")
            for k, valores in pr.a4.items():
                partes.append(f"A4 (54.b) {_valores(valores)} de «{k}», que controla la entidad")
            lineas.append(_envolver(f"{t.persona}: " + "; ".join(partes) + _marca(t.por_cuenta_de), 4))
    if r.cargos_direccion:
        lineas.append(_envolver("Cargos de dirección de alto nivel (22.2 y 63.4, C23). No son titulares reales: "
                                + ", ".join(r.cargos_direccion), 2))
    lineas += _incidencias("Posibles titulares", r.posibles, AMLR)
    lineas += _incidencias("Avisos", r.avisos, AMLR)
    lineas += [_envolver(f"Nota: {n}", 2) for n in r.notas]
    return lineas


def _incidencias(titulo, incidencias, regimen):
    if not incidencias:
        return []
    lineas = [f"  {titulo}:"]
    for i in incidencias:
        lineas.append(_envolver(f"{i.codigo}  {i.mensaje}", 4))
        lineas.append(_envolver(f"→ {origen(i.codigo, regimen)}", 6))
    return lineas


def _seccion_lecturas(inf):
    lineas = ["LECTURAS DE LAS QUE DEPENDE ESTE RESULTADO"]
    for regimen in (ESPANA, AMLR):
        lineas += [_envolver(f"{regimen}: {l}", 2, "- ") for l in LECTURAS[regimen]]
    lineas += [_envolver(l, 2, "- ") for l in LECTURAS_COMUNES]
    casos = sorted({n for regimen, r in ((ESPANA, inf.espana), (AMLR, inf.amlr)) for i in r.posibles + r.avisos
                    for n in CASOS_POR_AVISO.get(i.codigo, {}).get(regimen, ())}, key=lambda n: int(n[1:]))
    if casos:
        lineas.append("  Casos que la norma no resuelve y que afectan a esta entrada:")
        lineas += [_envolver(f"{n}: {CASOS_NO_RESUELTOS[n]}", 4) for n in casos]
    else:
        lineas.append(_envolver("Ningún aviso de esta entrada depende de un caso que la norma no resuelva, "
                                "pero el resultado sigue dependiendo de las lecturas de arriba.", 2))
    return lineas


def origen(codigo: str, regimen: str) -> str:
    """El caso no resuelto al que corresponde un aviso, o de qué viene si no es un caso de la norma."""
    casos = CASOS_POR_AVISO.get(codigo, {}).get(regimen)
    if casos:
        return "; ".join(f"{n}: {CASOS_NO_RESUELTOS[n]}" for n in casos)
    return ORIGEN_DE_OTROS_AVISOS.get(codigo, "validación de la entrada (modelo de datos, §6.2)")


def _marca(atribuciones):
    if not atribuciones:
        return ""
    aristas = sorted({f"{a.arista} (titular formal: {a.titular_formal})" for a in atribuciones})
    return f". Por cuenta de otro: {', '.join(aristas)}, atribuido al principal (C2)"


def _valores(por_magnitud):
    return ", ".join(f"{m} {porcentaje(v)} %" for m, v in por_magnitud.items())


def _lista(codigos):
    return ", ".join(codigos)


def _envolver(texto_, sangria, prefijo=""):
    """Parte las líneas largas a 100 caracteres, con sangría."""
    palabras, lineas, actual = texto_.split(), [], " " * sangria + prefijo
    base = len(actual)
    for palabra in palabras:
        if len(actual) + len(palabra) + 1 > 100 and len(actual) > base:
            lineas.append(actual.rstrip())
            actual = " " * (sangria + len(prefijo))
        actual += palabra + " "
    lineas.append(actual.rstrip())
    return "\n".join(lineas)


# --- JSON ----------------------------------------------------------------------------------


def como_dict(inf: Informe) -> dict:
    if inf.errores:
        return {"valida": False, "errores": [_incidencia(e) for e in inf.errores]}
    return {
        "valida": True,
        "advertencia": ADVERTENCIA,
        "entidad_objetivo": inf.objetivo,
        "fecha_referencia": str(inf.fecha),
        "espana": _espana(inf.espana),
        "amlr": _amlr(inf.amlr),
        "comparacion": [
            {"persona": f.persona, "espana": {"resultado": f.espana, "detalle": list(f.detalle_espana)},
             "amlr": {"resultado": f.amlr, "detalle": list(f.detalle_amlr)}, "difiere": f.difiere}
            for f in inf.filas
        ],
        "diferencias": list(inf.diferencias),
        "lecturas": {"espana": list(LECTURAS[ESPANA]), "amlr": list(LECTURAS[AMLR]), "comunes": list(LECTURAS_COMUNES)},
        "avisos_entrada": [_incidencia(a) for a in inf.avisos_entrada],
    }


def como_json(inf: Informe) -> str:
    return json.dumps(como_dict(inf), ensure_ascii=False, indent=2)


def _numero(valor):
    """Valor exacto (fracción irreducible) y redondeado a 2 decimales (§9, C6)."""
    if valor is None:
        return None
    valor = Fraction(valor)
    exacto = str(valor.numerator) if valor.denominator == 1 else f"{valor.numerator}/{valor.denominator}"
    return {"exacto": exacto, "redondeado": porcentaje(valor).replace(",", ".")}


def _por_magnitud(valores):
    return {m: _numero(v) for m, v in valores.items()}


def _incidencia(i, regimen=None):
    dato = {"codigo": i.codigo, "ids": [str(x) for x in i.ids], "mensaje": i.mensaje}
    if regimen:
        dato["casos"] = list(CASOS_POR_AVISO.get(i.codigo, {}).get(regimen, ()))
        dato["origen"] = origen(i.codigo, regimen)
    if i.informativo_en:
        dato["informativo_en"] = list(i.informativo_en)
    return dato


def _atribuciones(atribuciones):
    return [{"arista": a.arista, "titular_formal": a.titular_formal, "principal": a.principal,
             "magnitud": a.magnitud} for a in atribuciones]


def _cadenas(cadenas):
    return {m: [{"camino": [str(n) for n in camino], "producto": _numero(producto)} for camino, producto in lista]
            for m, lista in cadenas.items()}


def _espana(r):
    return {
        "estado": r.estado,
        "motivo": r.motivo,
        "titulares": [
            {"persona": t.persona, "pruebas": sorted(t.pruebas),
             "E1": _por_magnitud(t.participacion), "E2": _numero(t.agregado), "controla": t.controla,
             "por_cuenta_de": _atribuciones(t.por_cuenta_de), "cadenas": _cadenas(t.cadenas)}
            for t in r.titulares
        ],
        "posibles": [_incidencia(i, ESPANA) for i in r.posibles],
        "administradores": list(r.administradores),
        "avisos": [_incidencia(i, ESPANA) for i in r.avisos],
    }


def _amlr(r):
    return {
        "estado": r.estado,
        "motivo": r.motivo,
        "titulares": [
            {"persona": t.persona, "pruebas": sorted(t.pruebas.cumplidas),
             "A1": _por_magnitud(t.pruebas.a1), "A2": t.pruebas.a2, "A3": _por_magnitud(t.pruebas.a3),
             "A4": {k: _por_magnitud(v) for k, v in t.pruebas.a4.items()},
             "por_cuenta_de": _atribuciones(t.por_cuenta_de), "cadenas": _cadenas(t.cadenas)}
            for t in r.titulares
        ],
        "posibles": [_incidencia(i, AMLR) for i in r.posibles],
        "cargos_direccion": list(r.cargos_direccion),
        "avisos": [_incidencia(i, AMLR) for i in r.avisos],
        "notas": list(r.notas),
    }
