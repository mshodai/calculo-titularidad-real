"""Relación de control sobre el grafo preparado (especificación §3.2 a §3.4).

Solo las primitivas del §3. Las pruebas de titularidad de cada régimen y sus
avisos están en amlr.py (§4) y espana.py (§5). Dos definiciones, separadas:

- **AMLR** (C11): X controla Y si own_capital(X, Y) > 50 u own_votos(X, Y) > 50
  (53.2.c, «50 % más una de las acciones o los derechos de voto»), o si
  controla una entidad que controla Y (53.2.b, control en cada nivel). Es el
  cierre transitivo. `control_amlr` lo calcula con el método B o, para la
  prueba de sensibilidad (N12), con el A. `control_agregado` es C⁺ (C26, N8).
- **España** (C10 y C12): Y es dependiente de X si los votos agregados de X
  superan el 50 % de la base de la Dir. 22.5. Solo votos. Es el dominio del
  §3.4, que calcula `propagacion.base_directiva`.

Todo con fracciones exactas (C6).
"""

import operator
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction

from titularidad.modelo import MAGNITUDES, Incidencia
from titularidad.propagacion import Dominio, Grafo, base_directiva, cadenas_simples, serie_completa

MAYORIA = Fraction(50)  # C10: control si se supera estrictamente el 50


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


def valor(own, magnitud, x, y):
    """own_m(X, Y), o 0 si el par no aparece."""
    return own[magnitud].get(x, {}).get(y, Fraction(0))


def entidades(grafo):
    return grafo.entidades("capital") | grafo.entidades("votos")


def _origenes(grafo):
    return grafo.titulares("capital") | grafo.titulares("votos")


# --- AMLR: C11 y C⁺ ------------------------------------------------------------


def control_amlr(grafo: Grafo, own: dict, inclusivo: bool = False) -> Control:
    """C11: own_m(X, Y) > 50 en capital o en votos, cerrado por transitividad.

    Con `inclusivo`, el umbral pasa a ≥ 50: la repetición de C28 (UMBRAL-EXACTO).
    """
    supera = operator.ge if inclusivo else operator.gt
    por_participacion = {}
    for x in _origenes(grafo):
        for y in entidades(grafo) - {x}:
            magnitudes = tuple(m for m in MAGNITUDES if supera(valor(own, m, x, y), MAYORIA))
            if magnitudes:
                por_participacion[(x, y)] = magnitudes
    return Control(_cierre(por_participacion), por_participacion)


def control_agregado(grafo: Grafo, control: Control) -> Control:
    """C⁺ (C26): C más «lo que tienen en Y X y las entidades que controla, sumado entero».

    Por rondas desde C hasta que no cambia. Cada ronda solo añade pares, así
    que termina. Solo sirve para avisar (POS-AGREGADO, N8).
    """
    pares = set(control.pares)
    todas, origenes = entidades(grafo), _origenes(grafo)
    while True:
        nuevos = set()
        for x in origenes:
            grupo = {x} | {y for a, y in pares if a == x}
            for y in todas - grupo:
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
    avisos_espana: tuple[Incidencia, ...]

    def domina(self, x, y) -> bool | None:
        """España: si Y es dependiente de X. None si el dominio no se estabiliza."""
        if not self.espana.estable:
            return None
        return y in self.espana.dependientes.get(x, frozenset())


def calcular_control(grafo: Grafo) -> ResultadoControl:
    c_b = control_amlr(grafo, participaciones(grafo, "B"))
    c_a = control_amlr(grafo, participaciones(grafo, "A"))
    dominio, avisos_espana = dominio_espana(grafo)
    return ResultadoControl(c_b, c_a, control_agregado(grafo, c_b), dominio, avisos_espana)
