"""Régimen AMLR (especificación §4, §8.2 y §9).

Es titular real la persona física que cumple alguna de las pruebas del §4.5
en alguna magnitud: la unión de pruebas de C14.
- A1 (51.a y 52.1): own_m(P, S) ≥ 25.
- A2 (51.b y 53.2): P controla S.
- A3 (54.a y C15): suman ≥ 25 las participaciones directas en S de las
  entidades que P controla.
- A4 (54.b y C16): own_m(P, K) ≥ 25 en una entidad K que controla S.

Si no hay ninguno, el supuesto supletorio del 22.2: los cargos de dirección
de alto nivel, que no son titulares reales (C23). «Fuera de alcance» si S no
es una sociedad (C31). La cotización no cambia el cálculo (C5).

Los avisos son los del §9 que corresponden al AMLR: POS-T (N4/N5),
POS-AGREGADO, POS-MEZCLA, POS-FORMAL, POS-HUECO, H1, H2, H3, CICLO-SENS,
ART54-SENS, UMBRAL-EXACTO, CICLO-CERRADO, T-NO-CONVERGE, MEZCLA-NO-CONVERGE y
AMLR-NO-APLICABLE.

Todo con fracciones exactas (C6). Los puntos que la especificación no decide
están marcados con «AMBIGÜEDAD:».
"""

import operator
from dataclasses import dataclass
from datetime import date
from fractions import Fraction

from titularidad.control import Control, control_agregado, control_amlr, entidades, participaciones, valor
from titularidad.formato import por_magnitud, porcentaje
from titularidad.modelo import MAGNITUDES, EntidadJuridica, Entrada, Incidencia
from titularidad.propagacion import (
    NO_IDENTIFICADO,
    OPACA,
    Atribucion,
    Grafo,
    atribuir_huecos,
    enumerar_cadenas,
    marcas_por_cuenta_de,
    preparar,
    producto_mixto,
    serie_sobre,
    transparencia,
)

UMBRAL = Fraction(25)  # 52.1: «25 % o más»
MAYORIA = Fraction(50)
APLICABLE_DESDE = date(2027, 7, 10)  # art. 90

DETERMINADO = "determinado"
SIN_TITULAR = "sin titular real identificado (provisional)"
NO_DETERMINABLE = "no determinable"
FUERA_DE_ALCANCE = "fuera de alcance"


# --- Las pruebas A1 a A4 (§4.5) ------------------------------------------------------


@dataclass(frozen=True)
class Pruebas:
    """Las pruebas que cumple una persona, con sus valores (§4.5, paso 5)."""

    a1: dict  # magnitud → own_m(P, S)
    a2: bool
    a3: dict  # magnitud → suma de h_m(D, S) de las D que P controla
    a4: dict  # K → {magnitud → own_m(P, K)}, con K que controla S

    @property
    def cumplidas(self) -> frozenset:
        return frozenset(nombre for nombre, cumple in
                         (("A1", self.a1), ("A2", self.a2), ("A3", self.a3), ("A4", self.a4)) if cumple)

    def __bool__(self):
        return bool(self.cumplidas)


def pruebas(grafo: Grafo, own: dict, control: Control, persona: str, estricto: bool = False) -> Pruebas:
    """A1 a A4 para `persona`. Con `estricto`, «≥ 25» pasa a «> 25» (repetición de C28).

    A4 pide que K sea de clase `sociedad`. Las que no lo son se detienen como
    OPACA al preparar el grafo (C4): ninguna persona llega a ellas, así que la
    condición se cumple sola.
    """
    alcanza = operator.gt if estricto else operator.ge
    s = grafo.objetivo
    otras = entidades(grafo) - {s}

    a1 = {m: valor(own, m, persona, s) for m in MAGNITUDES if alcanza(valor(own, m, persona, s), UMBRAL)}
    controladas = control.controladas(persona) & otras
    sumas = {m: sum((grafo.h[m].get((d, s), Fraction(0)) for d in controladas), Fraction(0)) for m in MAGNITUDES}
    a3 = {m: v for m, v in sumas.items() if alcanza(v, UMBRAL)}
    a4 = {}
    for k in sorted(otras):
        if control.controla(k, s):
            en_k = {m: valor(own, m, persona, k) for m in MAGNITUDES if alcanza(valor(own, m, persona, k), UMBRAL)}
            if en_k:
                a4[k] = en_k
    return Pruebas(a1, control.controla(persona, s), a3, a4)


# --- Resultado ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Titular:
    persona: str
    pruebas: Pruebas
    por_cuenta_de: tuple[Atribucion, ...]  # la marca «por cuenta de» (C2)
    cadenas: dict  # por magnitud, las cadenas sin repeticiones (C8)


@dataclass(frozen=True)
class ResultadoAmlr:
    estado: str
    motivo: str
    titulares: tuple[Titular, ...]
    posibles: tuple[Incidencia, ...]  # POS-T, POS-AGREGADO, POS-MEZCLA, POS-FORMAL, POS-HUECO
    cargos_direccion: tuple[str, ...]  # supuesto supletorio (C23): no son titulares reales
    avisos: tuple[Incidencia, ...]
    notas: tuple[str, ...]  # información que no es un aviso


def calcular_amlr(entrada: Entrada) -> ResultadoAmlr:
    s = entrada.entidad_objetivo
    objetivo = entrada.nodos[s]
    if objetivo.clase != "sociedad":
        return ResultadoAmlr(FUERA_DE_ALCANCE, f"«{s}» es de clase «{objetivo.clase}»: v0.1 no tiene las reglas del "
                             "AMLR 52.4 para esas entidades (C31)", (), (), (), (), ())

    avisos, posibles, notas = [], [], []
    if entrada.fecha_referencia < APLICABLE_DESDE:
        avisos.append(Incidencia("AMLR-NO-APLICABLE", f"La fecha de referencia ({entrada.fecha_referencia}) es "
                                 "anterior al 10-07-2027: el AMLR todavía no es aplicable (art. 90, C7)"))
    if objetivo.cotizacion is not None:
        # AMBIGÜEDAD: el §2.5 dice que, si S cotiza, «la salida lo indica como
        # información», sin código de aviso. Va como nota.
        notas.append(f"«{s}» cotiza. En el AMLR eso no cambia el cálculo: el art. 65.a exime de las obligaciones "
                     "de los arts. 63 y 64, no de la definición de los arts. 51 a 55 (C5)")

    grafo = preparar(entrada)
    own = participaciones(grafo, "B")
    control = control_amlr(grafo, own)
    personas = sorted(grafo.personas)
    cumple = {p: pruebas(grafo, own, control, p) for p in personas}
    titulares = {p for p in personas if cumple[p]}
    no_titulares = [p for p in personas if p not in titulares]
    avisos += grafo.avisos

    # CICLO-SENS (§6.2): A1 a A4 con own_m y la relación de control del método A.
    own_a = participaciones(grafo, "A")
    control_a = control_amlr(grafo, own_a)
    titulares_a = {p for p in personas if pruebas(grafo, own_a, control_a, p)}
    if titulares_a != titulares:
        cambian = tuple(sorted(titulares_a ^ titulares))
        avisos.append(Incidencia("CICLO-SENS", "Con el método A de ciclos cambia quién es titular real en el AMLR: "
                                 f"{', '.join(cambian)} (N7/N12)", cambian))

    avisos += _art54_sens(grafo, control, cumple, titulares)
    avisos += _umbral_exacto(grafo, own, control, titulares)

    # Huecos (§9): H1, POS-HUECO y H2. Solo cuentan NO_IDENTIFICADO y OPACA.
    huecos = {m: sum((valor(own, m, v, s) for v in grafo.huecos()), Fraction(0)) for m in MAGNITUDES}
    if any(u >= UMBRAL for u in huecos.values()):
        avisos.append(Incidencia("H1", "Lo que llega a S desde titulares sin identificar alcanza el 25 %: "
                                 f"{por_magnitud(huecos)}. Puede haber un titular real sin identificar"))
    if grafo.huecos():
        posibles += _pos_hueco(grafo, own, huecos, no_titulares)
    if any(i.codigo == "POS-HUECO" for i in posibles):
        avisos.append(Incidencia("H2", "Hay posibles titulares reales en los huecos de la estructura (POS-HUECO)"))
    # H3 (C33): lo no identificado cumpliría una prueba de control, aunque lo que llega a S no alcance el umbral.
    for v in sorted(grafo.virtuales(), key=str):
        if v.clase in (NO_IDENTIFICADO, OPACA):
            de_control = sorted(pruebas(grafo, own, control, v).cumplidas & {"A2", "A3", "A4"})
            if de_control:
                avisos.append(Incidencia("H3", f"«{v}» cumpliría {', '.join(de_control)}. Quien esté detrás de lo "
                                         "que no está identificado podría ser titular real", (str(v),)))

    posibles += _pos_t(grafo, no_titulares, avisos)
    posibles += _pos_agregado(grafo, own, control, no_titulares)
    posibles += _pos_mezcla(grafo, no_titulares, avisos)
    posibles += _pos_formal(entrada, no_titulares)

    if titulares:
        resultado = tuple(
            Titular(p, cumple[p], marcas_por_cuenta_de(grafo, own, p),
                    {m: enumerar_cadenas(grafo, m, p) for m in MAGNITUDES})
            for p in sorted(titulares))
        return ResultadoAmlr(DETERMINADO, "Con la unión de pruebas (C14), hay titulares reales por alguna de A1 a A4", resultado, tuple(posibles), (),
                             tuple(avisos), tuple(notas))
    return _sin_titular(entrada, tuple(posibles), avisos, tuple(notas))


# --- Avisos --------------------------------------------------------------------------------


def _art54_sens(grafo, control, cumple, titulares):
    """ART54-SENS (N3, C27): titular solo por A1, que sin las cadenas con control no alcanza el 25 %."""
    sin_control = {m: {a: v for a, v in grafo.h[m].items() if not control.controla(*a)} for m in MAGNITUDES}
    own_o = {m: serie_sobre(sin_control[m]) for m in MAGNITUDES}
    avisos = []
    for p in sorted(titulares):
        sin_cadenas_mixtas = {m: own_o[m].get(p, {}).get(grafo.objetivo, Fraction(0)) for m in MAGNITUDES}
        if cumple[p].cumplidas == {"A1"} and all(v < UMBRAL for v in sin_cadenas_mixtas.values()):
            avisos.append(Incidencia("ART54-SENS", f"«{p}» es titular real solo por A1; si el art. 54 sustituyera "
                                     "al 52.1 en las cadenas con tramos de control, se quedaría en "
                                     f"{por_magnitud(sin_cadenas_mixtas)} (N3)", (p,)))
    return avisos


def _umbral_exacto(grafo, own, control, titulares):
    """UMBRAL-EXACTO (C28): se repite leyendo los valores iguales a un umbral
    justo por encima (control con ≥ 50; pruebas con ≥ 25, como ya están) y
    justo por debajo (control con > 50, como ya está; pruebas con > 25)."""
    personas = sorted(grafo.personas)
    encima = control_amlr(grafo, own, inclusivo=True)
    titulares_encima = {p for p in personas if pruebas(grafo, own, encima, p)}
    titulares_debajo = {p for p in personas if pruebas(grafo, own, control, p, estricto=True)}
    cambian = tuple(sorted((titulares_encima ^ titulares) | (titulares_debajo ^ titulares)))
    if not cambian:
        return []
    return [Incidencia("UMBRAL-EXACTO", "Leyendo justo por encima o por debajo los valores que coinciden con un "
                       f"umbral, cambia quién es titular real: {', '.join(cambian)} (C28, modelo D23)", cambian)]


def _pruebas_con_huecos(grafo, destinatario):
    """A1 a A4 para `destinatario` si fuera suyo todo lo que no está identificado (C34)."""
    con = atribuir_huecos(grafo, destinatario)
    own = participaciones(con, "B")
    return pruebas(con, own, control_amlr(con, own), destinatario)


def _pos_hueco(grafo, own, huecos, no_titulares):
    """POS-HUECO (C33, C34): P cumpliría alguna prueba si participara en lo que no está identificado.

    Todas las pruebas, no solo A1: con el hueco, P puede controlar una entidad
    de la cadena sin que lo que llega a S alcance el 25 %. Solo se mira a
    quien participa en S (§9): que cualquiera pudiera estar detrás del hueco ya
    lo dicen H1 y H3. A1 cuenta solo en las magnitudes en que P participa en S.
    """
    s = grafo.objetivo
    posibles = []
    for p in no_titulares:
        participa = [m for m in MAGNITUDES if valor(own, m, p, s) > 0]
        if not participa:
            continue
        con = _pruebas_con_huecos(grafo, p)
        cumplidas = sorted(con.cumplidas & {"A2", "A3", "A4"} | ({"A1"} if con.a1.keys() & set(participa) else set()))
        if not cumplidas:
            continue
        mensaje = f"«{p}» cumpliría {', '.join(cumplidas)} si participara en lo que no está identificado"
        if "A1" in cumplidas:
            con_hueco = {m: valor(own, m, p, s) + huecos[m] for m in participa}
            mensaje += f": alcanzaría el 25 % con {por_magnitud(con_hueco)}"
        if cumplidas != ["A1"]:
            mensaje += ". Con lo no identificado controlaría una entidad de la cadena"
        posibles.append(Incidencia("POS-HUECO", mensaje + " (estructura incompleta)", (p,)))
    return posibles


def _pos_t(grafo, no_titulares, avisos):
    """POS-T (N4/N5): lectura extensiva (§3.5, C13). En el AMLR, una arista
    pesa 1 si el titular tiene más del 50 % del capital o de los votos de la
    participada. Las aristas reflexivas no cuentan: nadie se controla a sí
    mismo (C11 compara X con Y distinta)."""
    claves = set(grafo.h["capital"]) | set(grafo.h["votos"])
    de_control = {(z, y) for z, y in claves if z != y
                  and any(grafo.h[m].get((z, y), 0) > MAYORIA for m in MAGNITUDES)}
    eff = transparencia(grafo, de_control)
    if eff is None:
        avisos.append(Incidencia("T-NO-CONVERGE", "La lectura extensiva no se puede calcular: hay un ciclo formado "
                                 "solo por aristas de control (§3.5)"))
        return []
    s = grafo.objetivo
    return [Incidencia("POS-T", f"«{p}» sería titular real con la lectura extensiva: "
                       f"{por_magnitud({m: valor(eff, m, p, s) for m in MAGNITUDES})}. Forma de cadena no "
                       "regulada (N4/N5)", (p,))
            for p in no_titulares if any(valor(eff, m, p, s) >= UMBRAL for m in MAGNITUDES)]


def _pos_agregado(grafo, own, control, no_titulares):
    """POS-AGREGADO (N8): con el control agregado C⁺ (C26), P cumpliría A2, A3 o A4."""
    agregado = control_agregado(grafo, control)
    return [Incidencia("POS-AGREGADO", f"«{p}» sería titular real si contara el control agregado a través de "
                       "varias entidades controladas (N8)", (p,))
            for p in no_titulares
            if pruebas(grafo, own, agregado, p).cumplidas & {"A2", "A3", "A4"}]


def _pos_mezcla(grafo, no_titulares, avisos):
    """POS-MEZCLA (N6, C21)."""
    own = producto_mixto(grafo)
    if own is None:
        avisos.append(Incidencia("MEZCLA-NO-CONVERGE", "El producto mixto no se puede calcular: la serie no converge "
                                 "(C21). No se ha comprobado la mezcla de magnitudes (N6)"))
        return []
    s = grafo.objetivo
    return [Incidencia("POS-MEZCLA", f"«{p}» alcanzaría el 25 % mezclando capital y votos en la cadena: "
                       f"{porcentaje(own[p][s])} % (N6)", (p,))
            for p in no_titulares if own.get(p, {}).get(s, 0) >= UMBRAL]


def _pos_formal(entrada, no_titulares):
    """POS-FORMAL (N9, C29): con las aristas `por_cuenta_de` en el titular formal, en las dos magnitudes."""
    if not any(p.por_cuenta_de for p in entrada.participaciones):
        return []
    formal = preparar(entrada, c2_en=())
    own = participaciones(formal, "B")
    control = control_amlr(formal, own)
    return [Incidencia("POS-FORMAL", f"«{p}» sería titular real si las participaciones por cuenta de otro se "
                       "atribuyeran al titular formal (N9)", (p,))
            for p in no_titulares if pruebas(formal, own, control, p)]


# --- Supuesto supletorio (§8.2, C23) --------------------------------------------------------


def _sin_titular(entrada, posibles, avisos, notas):
    s = entrada.nodos[entrada.entidad_objetivo]
    ejecutivos = [c for c in s.cargos if c.ejecutivo]
    cargos_direccion = tuple(c.persona for c in ejecutivos
                             if not isinstance(entrada.nodos.get(c.persona), EntidadJuridica))
    for c in ejecutivos:
        if isinstance(entrada.nodos.get(c.persona), EntidadJuridica):
            # AMBIGÜEDAD: C23 dice que los cargos ejecutivos ocupados por una
            # entidad «se excluyen, con un aviso», pero no le da código. Se usa
            # CARGO-EJECUTIVO-ENTIDAD.
            avisos.append(Incidencia("CARGO-EJECUTIVO-ENTIDAD", f"El cargo ejecutivo de «{c.persona}» lo ocupa una "
                                     "entidad: se excluye, porque el 63.4 habla solo de personas físicas (C23)",
                                     (c.persona,)))

    motivos = []
    if {"H1", "H2", "H3"} & {a.codigo for a in avisos}:
        motivos.append("hay participaciones sin identificar (H1/H2/H3): no se puede afirmar que se hayan «agotado "
                       "todos los medios posibles de identificación» (22.2)")
    if not cargos_direccion:
        # AMBIGÜEDAD: C23 no dice qué pasa si S no tiene cargos ejecutivos
        # ocupados por personas físicas. Sin nadie a quien identificar, el
        # supuesto del 22.2 no se puede cumplir; se trata como en España sin
        # cargos (C22, AVI-07): «no determinable».
        motivos.append("la entidad objetivo no tiene cargos de dirección de alto nivel que sean personas físicas")

    if motivos:
        return ResultadoAmlr(NO_DETERMINABLE, "; ".join(motivos), (), posibles, cargos_direccion, tuple(avisos), notas)
    return ResultadoAmlr(SIN_TITULAR, "No se ha identificado titular real (22.2). Se identifican los cargos de "
                         "dirección de alto nivel, que no son titulares reales (considerando 125). Es provisional: "
                         "v0.1 no evalúa el control por otros medios", (), posibles, cargos_direccion, tuple(avisos),
                         notas)
