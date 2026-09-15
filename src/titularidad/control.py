"""Relación de control sobre el grafo preparado (especificación §3.2 a §3.4).

Dos definiciones, separadas:

- **AMLR** (C11): X controla Y si own_capital(X, Y) > 50 u own_votos(X, Y) > 50
  (53.2.c, «50 % más una de las acciones o los derechos de voto»), o si
  controla una entidad que controla Y (53.2.b, control en cada nivel). Es el
  cierre transitivo. `control_amlr` lo calcula con el método B o, para la
  prueba de sensibilidad (N12), con el A. `control_agregado` es C⁺ (C26, N8).
- **España** (C10 y C12): Y es dependiente de X si los votos agregados de X
  superan el 50 % de la base de la Dir. 22.5. Solo votos. Es el dominio del
  §3.4, que ya calcula `propagacion.base_directiva`.

Los avisos POS-AGREGADO y CICLO-SENS no dependen de la relación, sino de quién
es titular real con ella (§3.3 y §6.2). Por eso aquí están también las
pruebas A1 a A4 del AMLR (§4.5), que el cálculo de titularidad reutilizará.

Todo con fracciones exactas (C6).
"""

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction

from titularidad.modelo import MAGNITUDES, Incidencia
from titularidad.propagacion import Dominio, Grafo, base_directiva, cadenas_simples, serie_completa

MAYORIA = Fraction(50)  # C10: control si se supera estrictamente el 50
UMBRAL_AMLR = Fraction(25)  # 52.1: «25 % o más»
PRUEBAS_DE_CONTROL = frozenset({"A2", "A3", "A4"})


@dataclass(frozen=True)
class Control:
    """Relación de control del AMLR.

    `pares` es la relación completa. `por_participacion` son los pares de la
    regla 1 de C11, con las magnitudes en que se pasa del 50 %: sirve para
    explicar el resultado, y para ver cuándo dos personas controlan la misma
    entidad, una por capital y otra por votos (N11).
    """

    pares: frozenset
    por_participacion: dict

    def controla(self, x, y) -> bool:
        return (x, y) in self.pares

    def controladas(self, x) -> set:
        return {y for a, y in self.pares if a == x}


# --- Participaciones de todos los pares ----------------------------------------


def participaciones(grafo: Grafo, metodo: str = "B") -> dict:
    """own_m(X, Y) de todos los pares, con el método B (§3.1) o el A (§6.2).

    Devuelve own[m][X][Y]; los pares que no aparecen valen 0.
    """
    if metodo == "B":
        return {m: serie_completa(grafo, m) for m in MAGNITUDES}
    if metodo != "A":
        raise ValueError(f"Método desconocido: {metodo}")
    own = {}
    for m in MAGNITUDES:
        por_origen = defaultdict(dict)
        for y in grafo.entidades(m):
            for x, valor in cadenas_simples(grafo, m, destino=y).items():
                por_origen[x][y] = valor
        own[m] = dict(por_origen)
    return own


def _own(own, magnitud, x, y):
    return own[magnitud].get(x, {}).get(y, Fraction(0))


def _entidades(grafo):
    return grafo.entidades("capital") | grafo.entidades("votos")


def _origenes(grafo):
    return grafo.titulares("capital") | grafo.titulares("votos")


# --- AMLR: C11 y C⁺ ------------------------------------------------------------


def control_amlr(grafo: Grafo, own: dict) -> Control:
    """C11: own_m(X, Y) > 50 en capital o en votos, cerrado por transitividad."""
    por_participacion = {}
    for x in _origenes(grafo):
        for y in _entidades(grafo) - {x}:
            magnitudes = tuple(m for m in MAGNITUDES if _own(own, m, x, y) > MAYORIA)
            if magnitudes:
                por_participacion[(x, y)] = magnitudes
    return Control(_cierre(por_participacion), por_participacion)


def control_agregado(grafo: Grafo, control: Control) -> Control:
    """C⁺ (C26): C más «lo que tienen en Y X y las entidades que controla, sumado entero».

    Por rondas desde C hasta que no cambia. Cada ronda solo añade pares, así
    que termina. Solo sirve para avisar (POS-AGREGADO, N8).
    """
    pares = set(control.pares)
    entidades, origenes = _entidades(grafo), _origenes(grafo)
    while True:
        nuevos = set()
        for x in origenes:
            grupo = {x} | {y for a, y in pares if a == x}
            for y in entidades - grupo:
                if any(sum(grafo.h[m].get((z, y), 0) for z in grupo) > MAYORIA for m in MAGNITUDES):
                    nuevos.add((x, y))
        if not nuevos - pares:
            return Control(frozenset(pares), control.por_participacion)
        pares = set(_cierre(pares | nuevos))


def _cierre(pares):
    """Cierre transitivo: si X controla Z y Z controla Y, X controla Y (53.2.b)."""
    pares = set(pares)
    while True:
        nuevos = {(x, y) for x, z in pares for z2, y in pares if z == z2 and x != y} - pares
        if not nuevos:
            return frozenset(pares)
        pares |= nuevos


# --- AMLR: pruebas de titularidad del §4.5 ---------------------------------------


def pruebas_amlr(grafo: Grafo, own: dict, control: Control, persona: str) -> frozenset:
    """Las pruebas A1 a A4 del §4.5 que cumple `persona`, en alguna magnitud.

    - A1: own_m(P, S) ≥ 25 (51.a y 52.1).
    - A2: P controla S (51.b y 53.2).
    - A3: suman ≥ 25 las participaciones directas en S de las entidades que P
      controla (54.a y C15).
    - A4: P tiene own_m(P, K) ≥ 25 en una entidad K que controla S (54.b y C16).
      El §4.5 pide que K sea de clase `sociedad`: las que no lo son se detienen
      como OPACA al preparar el grafo (C4), así que ninguna persona llega a
      ellas y la condición se cumple sola.
    """
    s = grafo.objetivo
    entidades = _entidades(grafo) - {s}
    pruebas = set()
    if any(_own(own, m, persona, s) >= UMBRAL_AMLR for m in MAGNITUDES):
        pruebas.add("A1")
    if control.controla(persona, s):
        pruebas.add("A2")
    controladas = control.controladas(persona) & entidades
    for m in MAGNITUDES:
        if sum((grafo.h[m].get((d, s), Fraction(0)) for d in controladas), Fraction(0)) >= UMBRAL_AMLR:
            pruebas.add("A3")
    for k in entidades:
        if control.controla(k, s) and any(_own(own, m, persona, k) >= UMBRAL_AMLR for m in MAGNITUDES):
            pruebas.add("A4")
    return frozenset(pruebas)


# --- España: dominio del art. 42 ---------------------------------------------------


def dominio_espana(grafo: Grafo, inclusivo: bool = False) -> tuple[Dominio, tuple[Incidencia, ...]]:
    """El dominio del §3.4 (C10 y C12) y, si no se estabiliza, DOMINIO-INESTABLE.

    Con `inclusivo`, el umbral es ≥ 50: la repetición de C28 (UMBRAL-EXACTO).
    """
    dominio = base_directiva(grafo, inclusivo)
    if dominio.estable:
        return dominio, ()
    return dominio, (Incidencia(
        "DOMINIO-INESTABLE",
        "El cálculo de dominio del §3.4 no se estabiliza: la agregación de votos (L2) no se "
        "puede calcular y E2 queda como no determinable",
    ),)


# --- Todo junto ------------------------------------------------------------------


@dataclass(frozen=True)
class ResultadoControl:
    amlr: Control  # C11 con el método B: la relación aplicada
    amlr_metodo_a: Control  # C11 con el método A: prueba de sensibilidad (N12)
    amlr_agregado: Control  # C⁺: solo para POS-AGREGADO (N8)
    espana: Dominio  # dominio del art. 42 (C12); si no es estable, E2 no es determinable
    avisos_amlr: tuple[Incidencia, ...]
    avisos_espana: tuple[Incidencia, ...]

    def domina(self, x, y) -> bool | None:
        """España: si Y es dependiente de X. None si el dominio no se estabiliza."""
        if not self.espana.estable:
            return None
        return y in self.espana.dependientes.get(x, frozenset())


def calcular_control(grafo: Grafo) -> ResultadoControl:
    own_b = participaciones(grafo, "B")
    own_a = participaciones(grafo, "A")
    c_b = control_amlr(grafo, own_b)
    c_a = control_amlr(grafo, own_a)
    c_mas = control_agregado(grafo, c_b)
    dominio, avisos_espana = dominio_espana(grafo)

    personas = sorted(grafo.personas)
    avisos_amlr = []
    titulares_b = {p for p in personas if pruebas_amlr(grafo, own_b, c_b, p)}
    titulares_a = {p for p in personas if pruebas_amlr(grafo, own_a, c_a, p)}
    if titulares_a != titulares_b:
        cambian = tuple(sorted(titulares_a ^ titulares_b))
        avisos_amlr.append(Incidencia(
            "CICLO-SENS",
            f"Con el método A de ciclos cambia quién es titular real en el AMLR: {', '.join(cambian)}. "
            "El resultado depende del método de ciclos (N7/N12)",
            cambian,
        ))
    for p in personas:
        if p not in titulares_b and pruebas_amlr(grafo, own_b, c_mas, p) & PRUEBAS_DE_CONTROL:
            avisos_amlr.append(Incidencia(
                "POS-AGREGADO",
                f"«{p}» sería titular real en el AMLR si contara el control agregado a través de "
                "varias entidades controladas (N8)",
                (p,),
            ))

    return ResultadoControl(c_b, c_a, c_mas, dominio, tuple(avisos_amlr), avisos_espana)
