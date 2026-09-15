"""Régimen español (especificación §5, §8.1 y §9).

Es titular real la persona física que supera el 25 % en alguna de estas dos
pruebas (C19):
- E1 (L1, «posean»): own_m(P, S) > 25 en capital o en votos (C17);
- E2 (L2, «controlen»): votos agregados del art. 42 sobre la base de la
  Dir. 22.5, va(P, S) · 100 / base(S) > 25 (C12 y C18).

Si no hay ninguno, se aplica el supuesto supletorio del art. 4.2.b bis (C22).
Antes de calcular: «fuera de alcance» si S no es una sociedad (C31), y
«exceptuada» si cotiza (C5) o es filial de una cotizada (C30).

Los avisos son los del §9 que corresponden a España: POS-T, POS-MEZCLA,
POS-FORMAL, POS-HUECO, H1, H2, CICLO-SENS, UMBRAL-EXACTO, CICLO-CERRADO,
T-NO-CONVERGE, DOMINIO-INESTABLE, COTIZADA y EXENCION-SENS.

Todo con fracciones exactas (C6). Los puntos que la especificación no decide
están marcados con «AMBIGÜEDAD:».
"""

import operator
from dataclasses import dataclass
from fractions import Fraction

from titularidad.control import dominio_espana
from titularidad.formato import por_magnitud as _por_magnitud
from titularidad.formato import porcentaje as _texto
from titularidad.modelo import MAGNITUDES, EntidadJuridica, Entrada, Incidencia
from titularidad.propagacion import (
    NO_IDENTIFICADO,
    OPACA,
    Atribucion,
    cadenas_simples,
    enumerar_cadenas,
    marcas_por_cuenta_de,
    preparar,
    producto_mixto,
    serie_completa,
    transparencia,
)

UMBRAL = Fraction(25)  # Ley 4.2.b: «superior al 25 por ciento»
MAYORIA = Fraction(50)  # C10 y C30
CIEN = Fraction(100)
COTIZADA = "COTIZADA"

DETERMINADO = "determinado"
SUPLETORIO = "supletorio (condicional)"
NO_DETERMINABLE = "no determinable"
FUERA_DE_ALCANCE = "fuera de alcance"
EXCEPTUADA = "exceptuada"


@dataclass(frozen=True)
class Titular:
    """Un titular real y lo que lo explica (§9)."""

    persona: str
    pruebas: frozenset  # «E1» y/o «E2»
    participacion: dict  # E1: own_m(P, S) por magnitud
    agregado: Fraction | None  # E2: va(P, S) · 100 / base(S); None si no se pudo calcular
    controla: bool  # S ∈ Dep(P): la salida indica que P controla S (CCom 42.1.a)
    por_cuenta_de: tuple[Atribucion, ...]  # la marca «por cuenta de» (C2)
    cadenas: dict  # por magnitud, las cadenas sin repeticiones (C8)


@dataclass(frozen=True)
class ResultadoEspana:
    estado: str
    motivo: str
    titulares: tuple[Titular, ...]
    posibles: tuple[Incidencia, ...]  # POS-T, POS-MEZCLA, POS-FORMAL, POS-HUECO
    administradores: tuple[str, ...]  # supuesto supletorio (C22)
    avisos: tuple[Incidencia, ...]


def calcular_espana(entrada: Entrada) -> ResultadoEspana:
    s = entrada.entidad_objetivo
    objetivo = entrada.nodos[s]
    if objetivo.clase != "sociedad":
        return _sin_calculo(FUERA_DE_ALCANCE, f"«{s}» es de clase «{objetivo.clase}»: v0.1 no tiene las reglas "
                            "del RD 8 para esas entidades (C31)")
    if _cotiza(objetivo):
        return _sin_calculo(EXCEPTUADA, f"«{s}» cotiza con requisitos de información: Ley 4.2.b, párr. 3 (C5)")

    cotizadas = {n: COTIZADA for n, nodo in entrada.nodos.items() if n != s and _cotiza(nodo)}
    # C30 se mide sin detener las cotizadas: si no, la participación de una
    # cotizada a través de otra cotizada se perdería.
    base = preparar(entrada)
    filial = _filial_de_cotizada(base, cotizadas)
    if filial:
        cotizada, valor = filial
        return _sin_calculo(EXCEPTUADA, f"«{s}» es filial participada mayoritariamente de la cotizada «{cotizada}», "
                            f"con el {_texto(valor)} % del capital: RD 9.4 (C30)")

    grafo = preparar(entrada, detener=cotizadas)
    ev = _evaluar(grafo)
    avisos = list(grafo.avisos) + list(ev.avisos_dominio) + list(_exencion_sens(base, cotizadas))
    avisos += _aviso_cotizadas(grafo, ev.own)
    posibles = []

    # CICLO-SENS (§6.2): E1 con el método A. E2 usa el método C, que no cambia.
    simples = {m: cadenas_simples(grafo, m) for m in MAGNITUDES}
    titulares_a = {p for p in ev.personas if _supera_e1(lambda m, x: simples[m].get(x, 0), p)} | ev.por_e2
    if titulares_a != ev.titulares:
        cambian = tuple(sorted(titulares_a ^ ev.titulares))
        avisos.append(Incidencia("CICLO-SENS", "Con el método A de ciclos cambia quién es titular real en "
                                 f"España: {', '.join(cambian)} (N7/N12)", cambian))

    avisos += _umbral_exacto(grafo, base, cotizadas, ev)

    # Huecos (§9): H1, POS-HUECO y H2. Solo cuentan NO_IDENTIFICADO y OPACA.
    huecos = {m: sum((ev.en_s(m, v) for v in grafo.virtuales() if v.clase in (NO_IDENTIFICADO, OPACA)), Fraction(0))
              for m in MAGNITUDES}
    if any(u > UMBRAL for u in huecos.values()):
        avisos.append(Incidencia("H1", "Lo que llega a S desde titulares sin identificar pasa del 25 %: "
                                 + _por_magnitud(huecos) + ". Puede haber un titular real sin identificar"))
    for p in ev.no_titulares():
        # Solo en las magnitudes en que P participa en S (§9): si no, cualquiera
        # podría estar detrás del hueco, y eso ya lo dice H1.
        con_hueco = {m: ev.en_s(m, p) + huecos[m] for m in MAGNITUDES if ev.en_s(m, p) > 0}
        if any(v > UMBRAL for v in con_hueco.values()):
            posibles.append(Incidencia("POS-HUECO", f"«{p}» pasaría del 25 % si participara en lo que no está "
                                       f"identificado: {_por_magnitud(con_hueco)} (estructura incompleta)", (p,)))
    if any(i.codigo == "POS-HUECO" for i in posibles):
        avisos.append(Incidencia("H2", "Hay posibles titulares reales en los huecos de la estructura (POS-HUECO)"))

    posibles += _pos_t(grafo, ev, avisos)
    posibles += _pos_mezcla(grafo, ev)
    posibles += _pos_formal(entrada, cotizadas, ev)

    titulares = tuple(_titular(grafo, ev, p) for p in sorted(ev.titulares))
    if titulares:
        # AMBIGÜEDAD: si el dominio no se estabiliza, E2 queda como no
        # determinable (§3.4), pero la especificación no dice qué estado tiene
        # el resultado cuando alguien sí es titular por E1. Se da
        # «determinado» con los titulares de E1 y el aviso DOMINIO-INESTABLE:
        # puede haber más titulares por E2.
        return ResultadoEspana(DETERMINADO, "Hay titulares reales por E1 o E2 (C19)", titulares,
                               tuple(posibles), (), tuple(avisos))
    return _supletorio(entrada, ev, tuple(posibles), tuple(avisos))


# --- Evaluación de E1 y E2 -------------------------------------------------------


@dataclass(frozen=True)
class _Evaluacion:
    objetivo: str
    personas: tuple[str, ...]
    own: dict  # own[m][X][Y], método B
    dominio: object
    avisos_dominio: tuple
    por_e2: frozenset
    titulares: frozenset

    def en_s(self, magnitud, x):
        return self.own[magnitud].get(x, {}).get(self.objetivo, Fraction(0))

    def no_titulares(self):
        return [p for p in self.personas if p not in self.titulares]


def _evaluar(grafo, inclusivo=False):
    """E1 y E2 para cada persona física. Con `inclusivo`, los umbrales pasan a ≥ (C28)."""
    supera = operator.ge if inclusivo else operator.gt
    s = grafo.objetivo
    own = {m: serie_completa(grafo, m) for m in MAGNITUDES}
    dominio, avisos = dominio_espana(grafo, inclusivo)
    personas = tuple(sorted(grafo.personas))
    por_e1 = {p for p in personas if _supera_e1(lambda m, x: own[m].get(x, {}).get(s, 0), p, supera)}
    por_e2 = set()
    # Si base(S) = 0, la proporción no se puede calcular (propagacion,
    # base_directiva) y nadie cumple E2: todos los votos de S son de S misma o
    # de sus dependientes.
    if dominio.estable and dominio.base(s) > 0:
        por_e2 = {p for p in personas if supera(dominio.proporcion(p, s), UMBRAL)}
    return _Evaluacion(s, personas, own, dominio, avisos, frozenset(por_e2), frozenset(por_e1 | por_e2))


def _supera_e1(valor, persona, supera=operator.gt):
    return any(supera(valor(m, persona), UMBRAL) for m in MAGNITUDES)


def _titular(grafo, ev, p):
    s = grafo.objetivo
    participacion = {m: ev.en_s(m, p) for m in MAGNITUDES}
    pruebas = set()
    if any(v > UMBRAL for v in participacion.values()):
        pruebas.add("E1")
    if p in ev.por_e2:
        pruebas.add("E2")
    agregado = None
    controla = False
    if ev.dominio.estable and ev.dominio.base(s) > 0:
        agregado = ev.dominio.proporcion(p, s)
        controla = s in ev.dominio.dependientes.get(p, frozenset())
    marcas = marcas_por_cuenta_de(grafo, ev.own, p)
    cadenas = {m: enumerar_cadenas(grafo, m, p) for m in MAGNITUDES}
    return Titular(p, frozenset(pruebas), participacion, agregado, controla, marcas, cadenas)


# --- Excepciones: cotizadas (C5) y filiales de cotizadas (C30) ---------------------


def _cotiza(nodo):
    return (isinstance(nodo, EntidadJuridica) and nodo.cotizacion is not None
            and nodo.cotizacion.requisitos_informacion_ue_o_equivalentes is True)


def _filial_de_cotizada(base, cotizadas, inclusivo=False):
    """C30: (cotizada, own_capital) si S es filial participada mayoritariamente de una cotizada."""
    supera = operator.ge if inclusivo else operator.gt
    own = serie_completa(base, "capital")
    for cotizada in sorted(cotizadas):
        valor = own.get(cotizada, {}).get(base.objetivo, Fraction(0))
        if supera(valor, MAYORIA):
            return cotizada, valor
    return None


def _exencion_sens(base, cotizadas):
    """EXENCION-SENS (N14): S sería filial midiendo con los votos o con una cadena de mayorías directas."""
    s = base.objetivo
    votos = serie_completa(base, "votos")
    for cotizada in sorted(cotizadas):
        por_votos = votos.get(cotizada, {}).get(s, 0) > MAYORIA
        if por_votos or _cadena_de_mayorias(base.h["capital"], cotizada, s):
            lectura = "con los votos" if por_votos else "con una cadena de mayorías directas de capital"
            yield Incidencia("EXENCION-SENS", f"«{s}» no es filial de «{cotizada}» según C30, pero lo sería {lectura}: "
                             "la identificación podría no ser preceptiva (RD 9.4, N14)", (cotizada,))


def _cadena_de_mayorias(h, origen, destino):
    """Si hay un camino de `origen` a `destino` con más del 50 % del capital directo en cada tramo."""
    vistos, pendientes = {origen}, [origen]
    while pendientes:
        nodo = pendientes.pop()
        for (titular, participada), valor in h.items():
            if titular == nodo and valor > MAYORIA and participada not in vistos:
                if participada == destino:
                    return True
                vistos.add(participada)
                pendientes.append(participada)
    return False


def _aviso_cotizadas(grafo, own):
    """COTIZADA (§9): lo que llega a S a través de cotizadas, a título informativo."""
    llegan = {m: {v: own[m].get(v, {}).get(grafo.objetivo, Fraction(0)) for v in grafo.virtuales() if v.clase == COTIZADA}
              for m in MAGNITUDES}
    ids = tuple(sorted({v.entidad for m in MAGNITUDES for v, x in llegan[m].items() if x > 0}))
    if not ids:
        return []
    total = {m: sum(llegan[m].values(), Fraction(0)) for m in MAGNITUDES}
    return [Incidencia("COTIZADA", f"Llega a S a través de cotizadas ({', '.join(ids)}): {_por_magnitud(total)}. "
                       "Sus titulares no se recorren (RD 9.4, C5)", ids)]


# --- UMBRAL-EXACTO (C28) -----------------------------------------------------------


def _umbral_exacto(grafo, base, cotizadas, ev):
    """Se repite con todas las comparaciones con 25 y 50 en «≥». En España
    todas son «>», así que la otra repetición («justo por debajo») es el
    propio cálculo."""
    if not ev.dominio.estable:
        return []  # E2 ya no es determinable: no hay con qué comparar
    if _filial_de_cotizada(base, cotizadas, inclusivo=True):
        inclusivos = frozenset()  # sería «exceptuada»: nadie es titular real
    else:
        inclusiva = _evaluar(grafo, inclusivo=True)
        if not inclusiva.dominio.estable:
            # AMBIGÜEDAD: C28 dice que, si el dominio no se estabiliza en la
            # repetición, «esa repetición queda sin hacer y la salida lo
            # indica», pero no le da código. Se usa UMBRAL-EXACTO-NO-COMPROBADO.
            return [Incidencia("UMBRAL-EXACTO-NO-COMPROBADO", "No se ha podido comprobar UMBRAL-EXACTO: con los "
                               "umbrales en «≥» el dominio no se estabiliza (C28)")]
        inclusivos = inclusiva.titulares
    if inclusivos == ev.titulares:
        return []
    cambian = tuple(sorted(inclusivos ^ ev.titulares))
    return [Incidencia("UMBRAL-EXACTO", "Leyendo justo por encima los valores que coinciden con un umbral, cambia "
                       f"quién es titular real: {', '.join(cambian)} (C28, modelo D23)", cambian)]


# --- Posibles titulares reales -------------------------------------------------------


def _pos_t(grafo, ev, avisos):
    """POS-T (N1/N2): la lectura extensiva L3, eff_m(P, S) > 25 (§3.5, C13).

    En España una arista pesa 1 si el titular domina directamente la
    participada: h_votos · 100 / base > 50, con la base de la Dir. 22.5.
    """
    if not ev.dominio.estable:
        # AMBIGÜEDAD: sin un dominio estable no hay base de la Dir. 22.5, y la
        # definición española de arista de control (C13) la necesita. Se deja
        # sin calcular; ya hay aviso DOMINIO-INESTABLE.
        return []
    control = set()
    for (titular, participada), valor in grafo.h["votos"].items():
        base = ev.dominio.base(participada)
        # AMBIGÜEDAD: C13 no dice qué pasa con las aristas de quienes tienen
        # votos neutralizados (la propia entidad y sus dependientes, §3.4).
        # Se entiende que no son de control: sus votos no cuentan en la base.
        neutralizado = titular == participada or titular in ev.dominio.dependientes.get(participada, frozenset())
        if base > 0 and not neutralizado and valor * CIEN / base > MAYORIA:
            control.add((titular, participada))
    eff = transparencia(grafo, control)
    if eff is None:
        avisos.append(Incidencia("T-NO-CONVERGE", "La lectura extensiva no se puede calcular: hay un ciclo formado "
                                 "solo por aristas de control (§3.5)"))
        return []
    return [Incidencia("POS-T", f"«{p}» sería titular real con la lectura extensiva L3: "
                       + _por_magnitud({m: eff[m].get(p, {}).get(grafo.objetivo, 0) for m in MAGNITUDES})
                       + " (N1/N2)", (p,))
            for p in ev.no_titulares()
            if any(eff[m].get(p, {}).get(grafo.objetivo, 0) > UMBRAL for m in MAGNITUDES)]


def _pos_mezcla(grafo, ev):
    """POS-MEZCLA (N6): en cada arista, el mayor de capital y votos (C21)."""
    own = producto_mixto(grafo)
    if own is None:
        return []
    s = grafo.objetivo
    return [Incidencia("POS-MEZCLA", f"«{p}» pasaría del 25 % mezclando capital y votos en la cadena: "
                       f"{_texto(own[p][s])} % (N6)", (p,))
            for p in ev.no_titulares() if own.get(p, {}).get(s, 0) > UMBRAL]


def _pos_formal(entrada, cotizadas, ev):
    """POS-FORMAL (N13): con el capital de las aristas `por_cuenta_de` en el titular formal (C29)."""
    if not any(p.por_cuenta_de for p in entrada.participaciones):
        return []
    formal = preparar(entrada, c2_en=("votos",), detener=cotizadas)
    capital = serie_completa(formal, "capital")
    s = entrada.entidad_objetivo
    return [Incidencia("POS-FORMAL", f"«{p}» sería titular real si el capital que se tiene por cuenta de otro se "
                       f"atribuyera al titular formal: {_texto(capital[p][s])} % (N13)", (p,))
            for p in ev.no_titulares() if capital.get(p, {}).get(s, 0) > UMBRAL]


# --- Supuesto supletorio (§8.1, C22) -------------------------------------------------


def _supletorio(entrada, ev, posibles, avisos):
    s = entrada.nodos[entrada.entidad_objetivo]
    administradores, sin_representante = [], []
    for cargo in s.cargos:
        if cargo.cargo != "miembro_organo_administracion":
            continue
        if isinstance(entrada.nodos.get(cargo.persona), EntidadJuridica):
            if cargo.representante is None:
                sin_representante.append(cargo.persona)
            else:
                administradores.append(cargo.representante)
        else:
            administradores.append(cargo.persona)

    motivos = []
    codigos = {a.codigo for a in avisos}
    if not ev.dominio.estable:
        # AMBIGÜEDAD: con E2 no determinable, no se puede afirmar que «no
        # exista» nadie por encima del umbral, igual que con un hueco. La
        # especificación no lo dice; se trata como «no determinable».
        motivos.append("E2 no es determinable porque el dominio no se estabiliza (DOMINIO-INESTABLE)")
    if codigos & {"H1", "H2"}:
        motivos.append("hay participaciones sin identificar (H1/H2), así que no se puede afirmar que «no exista» "
                       "una persona por encima del umbral. Ley 4.4, párr. 2: «no establecerán o mantendrán "
                       "relaciones de negocio con personas jurídicas […] cuya estructura de propiedad y de control "
                       "no haya podido determinarse»")
    if not s.cargos:
        motivos.append("la entidad objetivo no tiene cargos (AVI-07)")
    elif not administradores and not sin_representante:
        # AMBIGÜEDAD: C22 trata el caso sin cargos, pero no el de una entidad
        # con cargos y ninguno de administración (solo directivos). Tampoco
        # hay a quién presumir el control: se trata igual, «no determinable».
        motivos.append("la entidad objetivo no tiene miembros del órgano de administración")
    if sin_representante:
        motivos.append(f"el cargo de {', '.join(sin_representante)} lo ocupa una entidad sin representante (AVI-09)")

    if motivos:
        return ResultadoEspana(NO_DETERMINABLE, "; ".join(motivos), (), posibles, tuple(administradores), avisos)
    motivo = ("Nadie supera el 25 % por E1 ni por E2: se presume que controlan los administradores (Ley 4.2.b bis). "
              "Es condicional: v0.1 no evalúa el control por otros medios y la presunción admite prueba en contrario")
    if any(i.codigo == "POS-T" for i in posibles):
        motivo += ". Con la lectura extensiva (POS-T) habría titulares reales"
    return ResultadoEspana(SUPLETORIO, motivo, (), posibles, tuple(administradores), avisos)


# --- Utilidades ------------------------------------------------------------------------


def _sin_calculo(estado, motivo):
    return ResultadoEspana(estado, motivo, (), (), (), ())
