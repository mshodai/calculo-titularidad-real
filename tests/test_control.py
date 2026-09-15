"""Relación de control (src/titularidad/control.py).

Las cifras de referencia son las ya verificadas: la relación C11 del ejemplo
del modelo y del §4.2 se compara con verificacion.control, y el dominio
español con verificacion.dominio. Los ejemplos del §10 de la especificación
se comprueban con las pruebas que el documento les atribuye.
"""

import json
from fractions import Fraction

import pytest

from ayudas import entrada, verificacion
from titularidad.carga import cargar
from titularidad.control import calcular_control, control_amlr, participaciones, pruebas_amlr
from titularidad.propagacion import preparar

V = verificacion()
S = "E-OBJETIVO"


def como_texto(control):
    return {(str(x), str(y)) for x, y in control.pares}


def pruebas(grafo, resultado, persona):
    return pruebas_amlr(grafo, participaciones(grafo, "B"), resultado.amlr, persona)


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


def test_modelo_pruebas_del_amlr(modelo):
    """§6.3: P-ANA por A1 y A3; P-CARLOS por A1; P-DIEGO y P-BRUNO no."""
    grafo, resultado = modelo
    assert pruebas(grafo, resultado, "P-ANA") == {"A1", "A3"}
    assert pruebas(grafo, resultado, "P-CARLOS") == {"A1"}
    assert pruebas(grafo, resultado, "P-DIEGO") == set()
    assert pruebas(grafo, resultado, "P-BRUNO") == set()


def test_modelo_control_agregado_sin_posible_titular(modelo):
    """C⁺ añade que P-ANA controla E-OBJETIVO (25 % suyo + 35 % de E-HOLDING en votos),
    pero P-ANA ya es titular real: no hay POS-AGREGADO."""
    _, resultado = modelo
    assert resultado.amlr_agregado.pares - resultado.amlr.pares == {("P-ANA", S)}
    assert resultado.avisos_amlr == ()


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
    # P es titular real por A1 (45 %) con los dos métodos: el cambio en la
    # relación no cambia quién es titular, así que no hay CICLO-SENS.
    assert resultado.avisos_amlr == ()


# --- Avisos ------------------------------------------------------------------------


def test_ciclo_sens_la_autocartera_decide_el_control():
    """N12: con un 10 % de autocartera en H, el 48 % de P es 53,33 % con el método B
    (controla H y, por A3, es titular real) y 48 % con el A (no lo es)."""
    grafo = preparar(entrada([("a1", "H", "S", 30, 30), ("a2", "R", "S", 70, 70),
                              ("a3", "P", "H", 48, 48), ("a4", "H", "H", 10, 10), ("a5", "Q", "H", 42, 42)]))
    resultado = calcular_control(grafo)
    assert participaciones(grafo, "B")["capital"]["P"]["H"] == Fraction(160, 3)
    assert resultado.amlr.controla("P", "H")
    assert not resultado.amlr_metodo_a.controla("P", "H")
    assert [(a.codigo, a.ids) for a in resultado.avisos_amlr] == [("CICLO-SENS", ("P",))]


def test_pos_agregado():
    """N8: P controla D1 y D2 (60 % de cada una), que tienen el 30 % de K cada una.
    Ninguna controla K sola; juntas, sí. K tiene el 30 % de S."""
    grafo = preparar(entrada([
        ("a1", "D1", "K", 30, 30), ("a2", "D2", "K", 30, 30), ("a3", "Y", "K", 40, 40),
        ("a4", "P", "D1", 60, 60), ("a5", "X1", "D1", 40, 40),
        ("a6", "P", "D2", 60, 60), ("a7", "X2", "D2", 40, 40),
        ("a8", "K", "S", 30, 30), ("a9", "R", "S", 70, 70),
    ]))
    resultado = calcular_control(grafo)
    assert not resultado.amlr.controla("P", "K")
    assert resultado.amlr_agregado.controla("P", "K")
    assert pruebas(grafo, resultado, "P") == set()  # own(P, S) = 10,8 %
    assert [(a.codigo, a.ids) for a in resultado.avisos_amlr] == [("POS-AGREGADO", ("P",))]


def test_dominio_inestable_es_un_aviso_espanol():
    """Dos sociedades que se tienen al 70 % la una a la otra: el dominio oscila."""
    grafo = preparar(entrada([("a1", "B", "A", 70, 70), ("a2", "P", "A", 30, 30), ("a3", "A", "B", 70, 70),
                              ("a4", "Q", "B", 30, 30), ("a5", "A", "S", 100, 100)]))
    resultado = calcular_control(grafo)
    assert [a.codigo for a in resultado.avisos_espana] == ["DOMINIO-INESTABLE"]
    assert resultado.domina("A", "S") is None
    assert resultado.avisos_amlr == ()  # el AMLR no usa el dominio
    assert resultado.amlr.controla("A", "S")


# --- Ejemplos del §10 de la especificación ------------------------------------------


def test_ej2_control_arriba_participacion_abajo():
    grafo = preparar(entrada([("a1", "H", "S", 30, 30), ("a2", "X", "S", 70, 70),
                              ("a3", "P", "H", 60, 60), ("a4", "Q", "H", 40, 40)]))
    resultado = calcular_control(grafo)
    assert pruebas(grafo, resultado, "P") == {"A3"}
    assert pruebas(grafo, resultado, "Q") == set()
    assert resultado.domina("P", "H")


def test_ej2_variante_con_acumulacion():
    """54.a: P controla A1 y A2, con el 15 % de S cada una: 15 + 15 = 30 ≥ 25."""
    grafo = preparar(entrada([("a1", "A1", "S", 15, 15), ("a2", "A2", "S", 15, 15), ("a3", "X", "S", 70, 70),
                              ("a4", "P", "A1", 60, 60), ("a5", "Q1", "A1", 40, 40),
                              ("a6", "P", "A2", 60, 60), ("a7", "Q2", "A2", 40, 40)]))
    assert pruebas(grafo, calcular_control(grafo), "P") == {"A3"}


def test_ej3_participacion_arriba_control_abajo():
    grafo = preparar(entrada([("a1", "C", "S", 60, 60), ("a2", "R", "S", 40, 40),
                              ("a3", "P", "C", 30, 30), ("a4", "Q", "C", 70, 70)]))
    resultado = calcular_control(grafo)
    assert resultado.amlr.controla("C", "S") and resultado.amlr.controla("Q", "S")
    assert pruebas(grafo, resultado, "P") == {"A4"}
    assert {"A1", "A2"} <= pruebas(grafo, resultado, "Q")
    assert not resultado.domina("P", "C")


def test_ej4_dos_personas_controlan_la_misma_entidad():
    """N11: P controla A por capital y Q por votos. En España solo domina Q."""
    grafo = preparar(entrada([("a1", "A", "S", 30, 30), ("a2", "R", "S", 70, 70),
                              ("a3", "P", "A", 60, 40), ("a4", "Q", "A", 40, 60)]))
    resultado = calcular_control(grafo)
    assert resultado.amlr.por_participacion[("P", "A")] == ("capital",)
    assert resultado.amlr.por_participacion[("Q", "A")] == ("votos",)
    assert pruebas(grafo, resultado, "P") == {"A3"}
    assert pruebas(grafo, resultado, "Q") == {"A3"}
    assert resultado.domina("Q", "A") and not resultado.domina("P", "A")


def test_ej5_varios_tramos_de_control():
    grafo = preparar(entrada([("a1", "P", "A", 60, 60), ("a2", "A2", "A", 40, 40), ("a3", "A", "B", 50, 50),
                              ("a4", "B2", "B", 50, 50), ("a5", "B", "C", 60, 60), ("a6", "C2", "C", 40, 40),
                              ("a7", "C", "S", 50, 50), ("a8", "S2", "S", 50, 50)]))
    resultado = calcular_control(grafo)
    assert pruebas(grafo, resultado, "P") == set()
    assert pruebas(grafo, resultado, "S2") == {"A1"}
    assert resultado.avisos_amlr == ()


def test_ej6_control_por_capital_y_por_votos():
    grafo = preparar(entrada([("a1", "P", "A", 60, 10), ("a2", "Q", "A", 40, 90),
                              ("a3", "A", "S", 10, 45), ("a4", "R", "S", 90, 55)]))
    resultado = calcular_control(grafo)
    assert pruebas(grafo, resultado, "P") == {"A3"}
    assert "A3" in pruebas(grafo, resultado, "Q")
    assert {"A1", "A2"} <= pruebas(grafo, resultado, "R")
    assert resultado.domina("Q", "A") and not resultado.domina("P", "A")


def test_control_amlr_sin_participaciones_no_controla():
    grafo = preparar(entrada([("a1", "P", "S", 50, 50), ("a2", "Q", "S", 50, 50)]))
    assert control_amlr(grafo, participaciones(grafo, "B")).pares == frozenset()
