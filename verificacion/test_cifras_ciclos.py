"""Verificación provisional de las cifras de ciclos de la documentación.

Recalcula con fracciones exactas las cifras que aparecen en:

- docs/modelo-datos.md, §4.2: ejemplo S/H con P, Q y R, métodos A, B y C.
- docs/especificacion-calculo.md, §6.3: el ejemplo completo del modelo de
  datos (§10 de modelo-datos.md), que se lee de su bloque JSON para no
  mantener una copia aparte.

Además comprueba que cada cifra redondeada aparece en el documento que la
cita, de modo que si alguien edita una cifra sin recalcularla, esto falla.

Es provisional: implementa solo lo necesario para esas cifras (métodos A, B y
C de la especificación §6.2, C2 para `por_cuenta_de`, y la relación de control
del AMLR, C11, para el aviso ART54-SENS de C27). Cuando exista la
implementación, estas comprobaciones deben pasar a ser tests de ella y este
fichero debe borrarse.

Uso, desde la raíz del repositorio:

    python3 -m unittest discover -s verificacion -v
"""

import json
import re
import unittest
from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
MAGNITUDES = ("capital", "votos")


# --- Preparación del grafo (especificación §2) ------------------------------


def leer_ejemplo_modelo():
    texto = (DOCS / "modelo-datos.md").read_text(encoding="utf-8")
    bloques = re.findall(r"```json\n(.*?)\n```", texto, re.DOTALL)
    return json.loads(next(b for b in bloques if '"entidad_objetivo"' in b))


def preparar(entrada):
    """Devuelve (tipos, h) con h[m][(titular, participada)] en porcentaje.

    Aplica C1 (solo ancestros del objetivo), C2 (por_cuenta_de se atribuye al
    principal), C3 (aristas paralelas se suman) y C4 (huecos como titulares
    virtuales NO_IDENTIFICADO(X)).
    """
    tipos = {n["id"]: n["tipo"] for n in entrada["nodos"]}
    h = {m: {} for m in MAGNITUDES}
    for p in entrada["participaciones"]:
        titular = p.get("por_cuenta_de") or p["titular"]
        for m in MAGNITUDES:
            clave = (titular, p["participada"])
            h[m][clave] = h[m].get(clave, 0) + Fraction(str(p[m]))

    objetivo = entrada["entidad_objetivo"]
    ancestros, pendientes = {objetivo}, [objetivo]
    while pendientes:
        y = pendientes.pop()
        for x, z in h["capital"]:
            if z == y and x not in ancestros:
                ancestros.add(x)
                pendientes.append(x)
    for m in MAGNITUDES:
        h[m] = {k: v for k, v in h[m].items() if k[0] in ancestros and k[1] in ancestros}

    for x in [n for n in ancestros if tipos[n] == "entidad_juridica"]:
        for m in MAGNITUDES:
            resto = 100 - sum(v for (_, y), v in h[m].items() if y == x)
            if resto > 0:
                virtual = f"NO_IDENTIFICADO({x})"
                tipos[virtual] = "virtual"
                h[m][(virtual, x)] = resto
    return tipos, h


def grafo_simple(aristas):
    """Grafo de un ejemplo sin JSON: capital y votos iguales."""
    h = {m: {} for m in MAGNITUDES}
    for titular, participada, valor in aristas:
        for m in MAGNITUDES:
            h[m][(titular, participada)] = Fraction(valor)
    return h


# --- Métodos de cálculo (especificación §3.1, §3.4 y §6.2) -------------------


def resolver(matriz, vector):
    """Eliminación de Gauss con fracciones exactas."""
    n = len(vector)
    a = [fila[:] + [b] for fila, b in zip(matriz, vector)]
    for col in range(n):
        piv = next(f for f in range(col, n) if a[f][col] != 0)
        a[col], a[piv] = a[piv], a[col]
        for f in range(n):
            if f != col and a[f][col] != 0:
                factor = a[f][col] / a[col][col]
                a[f] = [x - factor * y for x, y in zip(a[f], a[col])]
    return [a[i][n] / a[i][i] for i in range(n)]


def metodo_b(h_m, origen, objetivo):
    """own_m(origen, objetivo): todas las cadenas, como sistema lineal (C8)."""
    entidades = sorted({y for _, y in h_m} - {origen})
    indice = {e: i for i, e in enumerate(entidades)}
    n = len(entidades)
    matriz = [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]
    vector = [h_m.get((origen, y), Fraction(0)) for y in entidades]
    for (z, y), v in h_m.items():
        if z in indice and y in indice:
            matriz[indice[y]][indice[z]] -= v / 100
    return resolver(matriz, vector)[indice[objetivo]]


def metodo_a(h_m, origen, objetivo):
    """Suma de cadenas que no repiten entidad (prueba de sensibilidad)."""

    def recorrer(nodo, visitados, producto):
        if nodo == objetivo:
            return producto
        total = Fraction(0)
        for (x, y), v in h_m.items():
            if x == nodo and y not in visitados and v:
                total += recorrer(y, visitados | {y}, producto * v / 100)
        return total

    return recorrer(origen, {origen}, Fraction(100))


def dominio(h_votos):
    """Dep, votos agregados y base de la Dir. 22.5 (especificación §3.4, C12).

    Rondas completas desde Dep vacío. Los votos neutralizados de Y (los de Y y
    sus dependientes) salen de la base y no cuentan en los votos agregados.
    Si un estado se repite sin estabilizarse, se lanza DominioInestable.
    """
    nodos = {n for arista in h_votos for n in arista}
    entidades = {y for _, y in h_votos}

    def funciones(dep):
        def neutralizados(y):
            return {y} | dep[y]

        def base(y):
            return 100 - sum(h_votos.get((z, y), 0) for z in neutralizados(y))

        def va(x, y):
            return sum(h_votos.get((z, y), 0) for z in ({x} | dep[x]) - neutralizados(y))

        return va, base

    dep = {n: frozenset() for n in nodos}
    vistos = set()
    while True:
        va, base = funciones(dep)
        nuevo = {
            x: frozenset(y for y in entidades - {x} if base(y) > 0 and va(x, y) * 100 / base(y) > 50)
            for x in nodos
        }
        if nuevo == dep:
            return dep, va, base
        estado = frozenset(nuevo.items())
        if estado in vistos:
            raise DominioInestable()
        vistos.add(estado)
        dep = nuevo


class DominioInestable(Exception):
    """El cálculo de dominio no se estabiliza (aviso DOMINIO-INESTABLE)."""


def metodo_c(h_votos, origen, objetivo):
    """Votos agregados sobre la base ajustada: va · 100 / base."""
    _, va, base = dominio(h_votos)
    return va(origen, objetivo) * 100 / base(objetivo)


def control(h, metodo=metodo_b):
    """Relación C del AMLR (especificación §3.3, C11).

    X controla Y si own_m(X, Y) > 50 en alguna magnitud, cerrado por
    transitividad. Con metodo=metodo_a es la prueba de sensibilidad de §6.2.
    """
    aristas = {a for m in MAGNITUDES for a in h[m]}
    nodos = {n for a in aristas for n in a}
    entidades = {y for _, y in aristas}
    c = {(x, y) for x in nodos for y in entidades - {x} if any(metodo(h[m], x, y) > 50 for m in MAGNITUDES)}
    while True:
        nuevo = c | {(x, y) for x, z in c for z2, y in c if z == z2 and x != y}
        if nuevo == c:
            return c
        c = nuevo


def sin_control(h, c):
    """El grafo sin las aristas Z → Y en las que C(Z, Y): base de own^O (C27)."""
    return {m: {k: v for k, v in h[m].items() if k not in c} for m in MAGNITUDES}


# --- Utilidades de comprobación ---------------------------------------------


def a_texto(valor):
    """Fracción en porcentaje a texto con 2 decimales y coma, como en los docs."""
    with localcontext() as ctx:
        ctx.prec = 50
        d = Decimal(valor.numerator) / Decimal(valor.denominator)
    return f"{d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}".replace(".", ",")


class ComprobacionDocumento(unittest.TestCase):
    documento = None

    def assertEnDocumento(self, *cifras):
        texto = (DOCS / self.documento).read_text(encoding="utf-8")
        for cifra in cifras:
            self.assertIn(a_texto(cifra), texto, f"{a_texto(cifra)} no aparece en {self.documento}")


# --- docs/modelo-datos.md §4.2 -------------------------------------------------


class ModeloDatosSeccion42(ComprobacionDocumento):
    """S: P 45, Q 35, H 20. H: S 60, R 40. Ciclo S → H → S."""

    documento = "modelo-datos.md"
    h = grafo_simple([("P", "S", 45), ("Q", "S", 35), ("H", "S", 20), ("S", "H", 60), ("R", "H", 40)])

    def test_metodo_a(self):
        valores = [metodo_a(self.h["votos"], x, "S") for x in "PQR"]
        self.assertEqual(valores, [45, 35, 8])
        self.assertEqual(sum(valores), 88)

    def test_metodo_b(self):
        valores = [metodo_b(self.h["votos"], x, "S") for x in "PQR"]
        self.assertEqual(valores, [Fraction(4500, 88), Fraction(3500, 88), Fraction(800, 88)])
        self.assertEqual(sum(valores), 100)
        self.assertEnDocumento(*valores)

    def test_metodo_c(self):
        valores = [metodo_c(self.h["votos"], x, "S") for x in "PQR"]
        self.assertEqual(valores, [Fraction(225, 4), Fraction(175, 4), 0])
        self.assertEnDocumento(*valores[:2])


# --- docs/especificacion-calculo.md §6.3 --------------------------------------


class EspecificacionSeccion63(ComprobacionDocumento):
    """Ejemplo del modelo de datos, leído de su bloque JSON."""

    documento = "especificacion-calculo.md"
    tipos, h = preparar(leer_ejemplo_modelo())
    S = "E-OBJETIVO"
    HUECO = "NO_IDENTIFICADO(E-FONDO)"
    TITULARES = ["P-ANA", "P-CARLOS", "P-DIEGO", HUECO]

    def test_por_cuenta_de_se_atribuye_al_principal(self):
        self.assertNotIn(("P-BRUNO", self.S), self.h["capital"])
        self.assertEqual(self.h["capital"][("P-CARLOS", self.S)], 18)

    def test_metodo_b_capital(self):
        valores = [metodo_b(self.h["capital"], x, self.S) for x in self.TITULARES]
        self.assertEqual(valores, [Fraction(3800, 94), Fraction(2400, 94), Fraction(1200, 94), Fraction(2000, 94)])
        self.assertEqual(sum(valores), 100)
        self.assertEnDocumento(*valores)

    def test_metodo_b_votos(self):
        valores = [metodo_b(self.h["votos"], x, self.S) for x in self.TITULARES]
        self.assertEqual(valores, [Fraction(4600, 93), Fraction(2700, 93), Fraction(2000, 93), 0])
        self.assertEqual(sum(valores), 100)
        self.assertEnDocumento(*valores[:3])

    def test_metodo_a(self):
        capital = [metodo_a(self.h["capital"], x, self.S) for x in self.TITULARES]
        votos = [metodo_a(self.h["votos"], x, self.S) for x in self.TITULARES]
        self.assertEqual(capital, [38, 24, 12, 20])
        self.assertEqual(votos, [46, 27, 20, 0])

    def test_aviso_de_hueco_de_diego(self):
        diego = metodo_b(self.h["capital"], "P-DIEGO", self.S)
        hueco = metodo_b(self.h["capital"], self.HUECO, self.S)
        self.assertEqual(diego + hueco, Fraction(3200, 94))
        self.assertEnDocumento(diego + hueco)

    def test_agregacion_espanola(self):
        dep, va, base = dominio(self.h["votos"])
        self.assertEqual(base(self.S), 100)
        self.assertEqual(va("P-ANA", self.S), 60)
        self.assertIn(self.S, dep["P-ANA"])
        self.assertEqual(va("P-CARLOS", self.S), 20)

    def test_en_el_amlr_nadie_controla_el_objetivo(self):
        for x in self.TITULARES:
            for m in MAGNITUDES:
                self.assertLessEqual(metodo_b(self.h[m], x, self.S), 50)
        self.assertLessEqual(self.h["votos"][("E-HOLDING", self.S)], 50)

    def test_aviso_art54_de_carlos(self):
        c = control(self.h)
        self.assertFalse({x for x, y in c if y == self.S})  # ni A2 ni A4
        directos = {z for z, y in self.h["capital"] if y == self.S and self.tipos[z] == "entidad_juridica"}
        self.assertFalse({y for x, y in c if x == "P-CARLOS"} & directos)  # ni A3

        self.assertIn(("P-CARLOS", "E-BETA"), c)
        beta = [metodo_b(self.h[m], "P-CARLOS", "E-BETA") for m in MAGNITUDES]
        self.assertEqual(beta, [Fraction(2950, 47), Fraction(2000, 31)])

        sin = sin_control(self.h, c)
        valores = [metodo_b(sin[m], "P-CARLOS", self.S) for m in MAGNITUDES]
        self.assertEqual(valores, [Fraction(1800, 94), Fraction(2000, 93)])
        self.assertTrue(all(v < 25 for v in valores))
        self.assertEnDocumento(*beta, *valores)

    def test_metodo_a_no_cambia_el_control(self):
        self.assertEqual(control(self.h, metodo_a), control(self.h))


if __name__ == "__main__":
    unittest.main()
