"""Relación de control (src/titularidad/control.py): solo las primitivas del §3.

Las cifras de referencia son las ya verificadas: la relación C11 del ejemplo
del modelo y del §4.2 se compara con verificacion.control, y el dominio
español con verificacion.dominio. Las pruebas A1 a A4 y los avisos del AMLR
están en test_amlr.py.
"""

import json
from fractions import Fraction

import pytest

from ayudas import entrada, verificacion
from titularidad.carga import cargar
from titularidad.control import calcular_control, control_amlr, participaciones
from titularidad.propagacion import preparar

V = verificacion()
S = "E-OBJETIVO"


def como_texto(control):
    return {(str(x), str(y)) for x, y in control.pares}


# --- El ejemplo del modelo -------------------------------------------------------


@pytest.fixture(scope="module")
def modelo():
    grafo = preparar(cargar(json.dumps(V.leer_ejemplo_modelo())).entrada)
    return grafo, calcular_control(grafo)


def test_modelo_amlr_igual_que_la_verificacion(modelo):
    """C11 con el método B y con el A: los mismos pares que verificacion.control."""
    _, resultado = modelo
    _, h = V.preparar(V.leer_ejemplo_modelo())
    assert como_texto(resultado.amlr) == V.control(h)
    assert como_texto(resultado.amlr_metodo_a) == V.control(h, V.metodo_a)
    # §6.3: «Con el método A tampoco cambia la relación de control».
    assert resultado.amlr_metodo_a.pares == resultado.amlr.pares


def test_modelo_carlos_controla_beta(modelo):
    """§6.3: 62,77 % de capital y 64,52 % de votos, contando lo que llega por E-OBJETIVO."""
    grafo, resultado = modelo
    own = participaciones(grafo, "B")
    assert own["capital"]["P-CARLOS"]["E-BETA"] == Fraction(2950, 47)
    assert own["votos"]["P-CARLOS"]["E-BETA"] == Fraction(2000, 31)
    assert resultado.amlr.por_participacion[("P-CARLOS", "E-BETA")] == ("capital", "votos")


def test_modelo_nadie_controla_el_objetivo_en_el_amlr(modelo):
    _, resultado = modelo
    assert not {x for x, y in resultado.amlr.pares if y == S}


def test_modelo_control_agregado(modelo):
    """C⁺ añade que P-ANA controla E-OBJETIVO: su 25 % de votos y el 35 % de E-HOLDING."""
    _, resultado = modelo
    assert resultado.amlr_agregado.pares - resultado.amlr.pares == {("P-ANA", S)}


def test_modelo_espana_igual_que_la_verificacion(modelo):
    _, resultado = modelo
    _, h = V.preparar(V.leer_ejemplo_modelo())
    dep, _, _ = V.dominio(h["votos"])
    nuestros = {str(x): {str(y) for y in ys} for x, ys in resultado.espana.dependientes.items()}
    assert nuestros == {x: set(ys) for x, ys in dep.items()}
    assert resultado.domina("P-ANA", S)  # §6.3: P-ANA controla E-OBJETIVO en España
    assert resultado.domina("P-CARLOS", "E-BETA") is False  # §6.3: con el 50 % no domina
    assert resultado.avisos_espana == ()


# --- Ejemplo del §4.2 del modelo de datos ------------------------------------------


def test_seccion_42_control_segun_el_metodo():
    """Modelo §4.2: «P controla S con los métodos B y C, y no con el A»."""
    grafo = preparar(entrada([("a1", "P", "S", 45, 45), ("a2", "Q", "S", 35, 35), ("a3", "H", "S", 20, 20),
                              ("a4", "S", "H", 60, 60), ("a5", "R", "H", 40, 40)]))
    resultado = calcular_control(grafo)
    assert resultado.amlr.controla("P", "S")
    assert not resultado.amlr_metodo_a.controla("P", "S")
    assert resultado.domina("P", "S")


# --- Relaciones -----------------------------------------------------------------------


def test_autocartera_decide_el_control_segun_el_metodo():
    """N12: con un 10 % de autocartera en H, el 48 % de P es 53,33 % con el método B y 48 % con el A."""
    grafo = preparar(entrada([("a1", "H", "S", 30, 30), ("a2", "R", "S", 70, 70),
                              ("a3", "P", "H", 48, 48), ("a4", "H", "H", 10, 10), ("a5", "Q", "H", 42, 42)]))
    resultado = calcular_control(grafo)
    assert participaciones(grafo, "B")["capital"]["P"]["H"] == Fraction(160, 3)
    assert resultado.amlr.controla("P", "H")
    assert not resultado.amlr_metodo_a.controla("P", "H")


def test_control_agregado_por_varias_controladas():
    """N8: P controla D1 y D2 (60 % de cada una), que tienen el 30 % de K cada una."""
    grafo = preparar(entrada([
        ("a1", "D1", "K", 30, 30), ("a2", "D2", "K", 30, 30), ("a3", "Y", "K", 40, 40),
        ("a4", "P", "D1", 60, 60), ("a5", "X1", "D1", 40, 40),
        ("a6", "P", "D2", 60, 60), ("a7", "X2", "D2", 40, 40),
        ("a8", "K", "S", 30, 30), ("a9", "R", "S", 70, 70),
    ]))
    resultado = calcular_control(grafo)
    assert not resultado.amlr.controla("P", "K")
    assert resultado.amlr_agregado.controla("P", "K")


def test_cierre_transitivo():
    """Ej. 3: Q controla C, que controla S; así que Q controla S (53.2.b)."""
    grafo = preparar(entrada([("a1", "C", "S", 60, 60), ("a2", "R", "S", 40, 40),
                              ("a3", "P", "C", 30, 30), ("a4", "Q", "C", 70, 70)]))
    resultado = calcular_control(grafo)
    assert resultado.amlr.controla("C", "S") and resultado.amlr.controla("Q", "S")
    assert ("Q", "S") not in resultado.amlr.por_participacion  # por transitividad, no por participación
    assert not resultado.domina("P", "C")


def test_ej4_dos_personas_controlan_la_misma_entidad():
    """N11: P controla A por capital y Q por votos. En España solo domina Q."""
    grafo = preparar(entrada([("a1", "A", "S", 30, 30), ("a2", "R", "S", 70, 70),
                              ("a3", "P", "A", 60, 40), ("a4", "Q", "A", 40, 60)]))
    resultado = calcular_control(grafo)
    assert resultado.amlr.por_participacion[("P", "A")] == ("capital",)
    assert resultado.amlr.por_participacion[("Q", "A")] == ("votos",)
    assert resultado.domina("Q", "A") and not resultado.domina("P", "A")


def test_umbral_inclusivo():
    """C28: con el 50 % justo no hay control; leído justo por encima, sí."""
    grafo = preparar(entrada([("a1", "P", "S", 50, 50), ("a2", "Q", "S", 50, 50)]))
    own = participaciones(grafo, "B")
    assert control_amlr(grafo, own).pares == frozenset()
    assert control_amlr(grafo, own, inclusivo=True).pares == {("P", "S"), ("Q", "S")}


def test_dominio_inestable_es_un_aviso_espanol():
    """Dos sociedades que se tienen al 70 % la una a la otra: el dominio oscila."""
    grafo = preparar(entrada([("a1", "B", "A", 70, 70), ("a2", "P", "A", 30, 30), ("a3", "A", "B", 70, 70),
                              ("a4", "Q", "B", 30, 30), ("a5", "A", "S", 100, 100)]))
    resultado = calcular_control(grafo)
    assert [a.codigo for a in resultado.avisos_espana] == ["DOMINIO-INESTABLE"]
    assert resultado.domina("A", "S") is None
    assert resultado.amlr.controla("A", "S")  # el AMLR no usa el dominio
