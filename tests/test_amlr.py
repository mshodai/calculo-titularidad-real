"""Régimen AMLR (src/titularidad/amlr.py).

Contra las cifras verificadas (verificacion/test_cifras_ciclos.py: el ejemplo
del modelo, §6.3, incluido el aviso ART54-SENS de P-CARLOS) y contra lo que el
§10 de la especificación dice de cada ejemplo en el AMLR.
"""

import json
from fractions import Fraction

import pytest

from ayudas import entrada, verificacion
from titularidad.amlr import DETERMINADO, FUERA_DE_ALCANCE, NO_DETERMINABLE, SIN_TITULAR, calcular_amlr
from titularidad.carga import cargar

V = verificacion()
DIRECTIVO = [{"persona": "DIR", "cargo": "directivo", "ejecutivo": True}]


def calcular(aristas, **opciones):
    opciones.setdefault("cargos", DIRECTIVO)
    opciones.setdefault("fecha", "2027-07-10")  # ya aplicable: sin AMLR-NO-APLICABLE
    return calcular_amlr(entrada(aristas, **opciones))


def titulares(resultado):
    return {t.persona: t.pruebas for t in resultado.titulares}


def de(resultado, codigo):
    return [i for i in resultado.posibles + resultado.avisos if i.codigo == codigo]


def codigos(resultado):
    return sorted(i.codigo for i in resultado.posibles + resultado.avisos)


# --- El ejemplo del modelo (§6.3 y Ej. 7) ------------------------------------------


@pytest.fixture(scope="module")
def modelo():
    return calcular_amlr(cargar(json.dumps(V.leer_ejemplo_modelo())).entrada)


def test_modelo_titulares_y_pruebas(modelo):
    """§6.3: P-ANA por A1 (40,43 / 49,46) y A3 (E-HOLDING, 30 / 35); P-CARLOS por A1 (25,53 / 29,03)."""
    assert modelo.estado == DETERMINADO
    t = titulares(modelo)
    assert set(t) == {"P-ANA", "P-CARLOS"}
    assert t["P-ANA"].cumplidas == {"A1", "A3"}
    assert t["P-ANA"].a1 == {"capital": Fraction(3800, 94), "votos": Fraction(4600, 93)}
    assert t["P-ANA"].a3 == {"capital": 30, "votos": 35}
    assert t["P-CARLOS"].cumplidas == {"A1"}
    assert t["P-CARLOS"].a1 == {"capital": Fraction(2400, 94), "votos": Fraction(2700, 93)}
    _, h = V.preparar(V.leer_ejemplo_modelo())
    for p in t:
        for m, v in t[p].a1.items():
            assert v == V.metodo_b(h[m], p, "E-OBJETIVO")


def test_modelo_ana_no_controla_el_objetivo(modelo):
    """§6.3: «No controla E-OBJETIVO: 49,46 no pasa de 50»."""
    assert not titulares(modelo)["P-ANA"].a2


def test_modelo_art54_sens_de_carlos(modelo):
    """§6.3: sin la cadena por E-BETA, P-CARLOS se queda en 19,15 % de capital y 21,51 % de votos."""
    (aviso,) = de(modelo, "ART54-SENS")
    assert aviso.ids == ("P-CARLOS",)
    assert "capital 19,15 %, votos 21,51 %" in aviso.mensaje


def test_modelo_aviso_de_hueco_de_diego(modelo):
    (hueco,) = de(modelo, "POS-HUECO")
    assert hueco.ids == ("P-DIEGO",)
    assert "capital 34,04 %" in hueco.mensaje


def test_modelo_avisos(modelo):
    """Ni CICLO-SENS, ni UMBRAL-EXACTO, ni POS-FORMAL (P-BRUNO se queda en 19,15 / 21,51), ni POS-AGREGADO
    (C⁺ solo añade el control de P-ANA, que ya es titular). La fecha de referencia es de 2026."""
    assert codigos(modelo) == ["AMLR-NO-APLICABLE", "ART54-SENS", "H2", "POS-HUECO"]


def test_modelo_marca_por_cuenta_de(modelo):
    marcas = {t.persona: {a.arista for a in t.por_cuenta_de} for t in modelo.titulares}
    assert marcas == {"P-ANA": set(), "P-CARLOS": {"p03"}}


# --- Ejemplo del §4.2 del modelo de datos --------------------------------------------


def test_seccion_42():
    """P controla S con el método B (51,14 %): A1 y A2. Con el A (45 %) solo A1, pero sigue siéndolo."""
    r = calcular([("a1", "P", "S", 45, 45), ("a2", "Q", "S", 35, 35), ("a3", "H", "S", 20, 20),
                  ("a4", "S", "H", 60, 60), ("a5", "R", "H", 40, 40)])
    t = titulares(r)
    assert set(t) == {"P", "Q"}
    assert t["P"].cumplidas == {"A1", "A2"} and t["P"].a1["votos"] == Fraction(4500, 88)
    assert not de(r, "CICLO-SENS")


# --- Ejemplos del §10 ------------------------------------------------------------------


def test_ej1_exactamente_el_25():
    """25 ≥ 25: cuatro titulares. UMBRAL-EXACTO: leídos justo por debajo, nadie lo sería."""
    r = calcular([(f"a{i}", f"P{i}", "S", 25, 25) for i in range(1, 5)])
    assert r.estado == DETERMINADO
    assert {p: t.cumplidas for p, t in titulares(r).items()} == {f"P{i}": {"A1"} for i in range(1, 5)}
    assert [i.ids for i in de(r, "UMBRAL-EXACTO")] == [("P1", "P2", "P3", "P4")]


def test_ej2_control_arriba_participacion_abajo():
    r = calcular([("a1", "H", "S", 30, 30), ("a2", "X", "S", 70, 70), ("a3", "P", "H", 60, 60), ("a4", "Q", "H", 40, 40)])
    t = titulares(r)
    assert set(t) == {"P", "X"}
    assert t["P"].cumplidas == {"A3"} and t["P"].a3 == {"capital": 30, "votos": 30}
    assert t["X"].cumplidas == {"A1", "A2"}
    assert codigos(r) == []


def test_ej2_variante_con_acumulacion():
    """54.a: 15 + 15 = 30 ≥ 25."""
    r = calcular([("a1", "A1", "S", 15, 15), ("a2", "A2", "S", 15, 15), ("a3", "X", "S", 70, 70),
                  ("a4", "P", "A1", 60, 60), ("a5", "Q1", "A1", 40, 40), ("a6", "P", "A2", 60, 60), ("a7", "Q2", "A2", 40, 40)])
    assert titulares(r)["P"].a3 == {"capital": 30, "votos": 30}


def test_ej3_participacion_arriba_control_abajo():
    """P por A4: C controla S y own(P, C) = 30 ≥ 25. Por A1 no (18 %)."""
    r = calcular([("a1", "C", "S", 60, 60), ("a2", "R", "S", 40, 40), ("a3", "P", "C", 30, 30), ("a4", "Q", "C", 70, 70)])
    t = titulares(r)
    assert set(t) == {"P", "Q", "R"}
    assert t["P"].cumplidas == {"A4"} and t["P"].a4 == {"C": {"capital": 30, "votos": 30}}
    assert {"A1", "A2"} <= t["Q"].cumplidas
    assert t["R"].cumplidas == {"A1"}


def test_ej4_mayoria_de_capital_sin_mayoria_de_votos():
    """P controla A por capital y Q por votos (N11): los dos por A3."""
    r = calcular([("a1", "A", "S", 30, 30), ("a2", "R", "S", 70, 70), ("a3", "P", "A", 60, 40), ("a4", "Q", "A", 40, 60)])
    t = titulares(r)
    assert set(t) == {"P", "Q", "R"}
    assert t["P"].cumplidas == {"A3"} and t["Q"].cumplidas == {"A3"}


def test_ej5_varios_tramos_de_control():
    """P: 52.1 da 9 %; ni 54.a ni 54.b. Lectura extensiva 25 ≥ 25: POS-T. B2, igual:
    0,5 × 1 × 0,5 = 25 (la especificación omitía a B2; corregido en el Ej. 5).
    UMBRAL-EXACTO: leídas por encima, las aristas del 50 % harían titulares a P, A2, B2 y C2."""
    r = calcular([("a1", "P", "A", 60, 60), ("a2", "A2", "A", 40, 40), ("a3", "A", "B", 50, 50), ("a4", "B2", "B", 50, 50),
                  ("a5", "B", "C", 60, 60), ("a6", "C2", "C", 40, 40), ("a7", "C", "S", 50, 50), ("a8", "S2", "S", 50, 50)])
    assert set(titulares(r)) == {"S2"}
    pos_t = de(r, "POS-T")
    assert [i.ids for i in pos_t] == [("B2",), ("P",)]
    assert all("capital 25,00 %" in i.mensaje for i in pos_t)
    assert [i.ids for i in de(r, "UMBRAL-EXACTO")] == [("A2", "B2", "C2", "P")]


def test_ej5b_el_54_como_suma():
    """C14: P y A2 por A1 (0,5 × 1 × 0,5 = 25). ART54-SENS: la única cadena tiene un tramo de control."""
    r = calcular([("a1", "P", "A", 50, 50), ("a2", "A2", "A", 50, 50), ("a3", "A", "D", 100, 100),
                  ("a4", "D", "S", 50, 50), ("a5", "S2", "S", 50, 50)])
    t = titulares(r)
    assert set(t) == {"P", "A2", "S2"}
    assert t["P"].cumplidas == {"A1"} and t["P"].a1 == {"capital": 25, "votos": 25}
    assert sorted(i.ids for i in de(r, "ART54-SENS")) == [("A2",), ("P",)]
    assert all("capital 0,00 %" in i.mensaje for i in de(r, "ART54-SENS"))
    assert [i.ids for i in de(r, "UMBRAL-EXACTO")] == [("A2", "P")]


def test_ej6_mezcla_de_magnitudes():
    """P controla A por capital, y A tiene el 45 % de los votos de S: A3."""
    r = calcular([("a1", "P", "A", 60, 10), ("a2", "Q", "A", 40, 90), ("a3", "A", "S", 10, 45), ("a4", "R", "S", 90, 55)])
    t = titulares(r)
    assert set(t) == {"P", "Q", "R"}
    assert t["P"].cumplidas == {"A3"} and t["P"].a3 == {"votos": 45}
    assert "A3" in t["Q"].cumplidas and {"A1", "A2"} <= t["R"].cumplidas
    assert not de(r, "POS-MEZCLA")


def test_ej8a_la_cotizacion_no_cambia_el_calculo():
    """P por A1 (40 %). Lo que llega a través de L (60 %) va a NO_IDENTIFICADO(L): H1."""
    r = calcular([("a1", "L", "S", 60, 60), ("a2", "P", "S", 40, 40)], cotizadas={"L": True})
    assert r.estado == DETERMINADO
    assert titulares(r)["P"].cumplidas == {"A1"}
    (h1,) = de(r, "H1")
    assert "capital 60,00 %" in h1.mensaje
    assert not de(r, "POS-HUECO")  # DIR no participa en S: no se señala (§9)


def test_ej8b_filial_intermedia():
    """P por A1 (0,49 × 70 = 34,3 %) y A4 (X controla S y P tiene el 49 % de X); R por A1. H1: 35,7 %."""
    r = calcular([("a1", "L", "X", 51, 51), ("a2", "P", "X", 49, 49), ("a3", "X", "S", 70, 70), ("a4", "R", "S", 30, 30)],
                 cotizadas={"L": True})
    t = titulares(r)
    assert set(t) == {"P", "R"}
    assert t["P"].cumplidas == {"A1", "A4"} and t["P"].a1["capital"] == Fraction(343, 10)
    assert t["P"].a4 == {"X": {"capital": 49, "votos": 49}}
    (h1,) = de(r, "H1")
    assert "capital 35,70 %" in h1.mensaje


# --- Avisos --------------------------------------------------------------------------------


def test_ciclo_sens_la_autocartera_decide_el_control():
    """N12: con un 10 % de autocartera en H, P controla H con el método B (53,33 %) y es
    titular por A3; con el A (48 %), no."""
    r = calcular([("a1", "H", "S", 30, 30), ("a2", "R", "S", 70, 70),
                  ("a3", "P", "H", 48, 48), ("a4", "H", "H", 10, 10), ("a5", "Q", "H", 42, 42)])
    assert titulares(r)["P"].cumplidas == {"A3"}
    assert [i.ids for i in de(r, "CICLO-SENS")] == [("P",)]


def test_pos_agregado():
    """N8: P controla D1 y D2, que juntas (60 %) controlarían K, con el 30 % de S."""
    r = calcular([
        ("a1", "D1", "K", 30, 30), ("a2", "D2", "K", 30, 30), ("a3", "Y", "K", 40, 40),
        ("a4", "P", "D1", 60, 60), ("a5", "X1", "D1", 40, 40), ("a6", "P", "D2", 60, 60), ("a7", "X2", "D2", 40, 40),
        ("a8", "K", "S", 30, 30), ("a9", "R", "S", 70, 70),
    ])
    assert "P" not in titulares(r)
    assert [i.ids for i in de(r, "POS-AGREGADO")] == [("P",)]


def test_pos_formal():
    """N9: T tiene el 30 % por cuenta de Q. Con la lectura contraria, T sería titular por A1."""
    r = calcular([("a1", "T", "S", 30, 30, "Q"), ("a2", "P", "S", 70, 70)])
    assert set(titulares(r)) == {"P", "Q"}
    assert [i.ids for i in de(r, "POS-FORMAL")] == [("T",)]


def test_t_no_converge():
    """A y B se tienen al 60 % la una a la otra: con peso 1, la lectura extensiva no converge."""
    r = calcular([("a1", "B", "A", 60, 60), ("a2", "P", "A", 40, 40), ("a3", "A", "B", 60, 60),
                  ("a4", "Q", "B", 40, 40), ("a5", "A", "S", 50, 50), ("a6", "R", "S", 50, 50)])
    assert de(r, "T-NO-CONVERGE")
    assert not de(r, "POS-T")


def test_amlr_no_aplicable_antes_del_10_de_julio_de_2027():
    antes = calcular([("a1", "P", "S", 100, 100)], fecha="2027-07-09")
    despues = calcular([("a1", "P", "S", 100, 100)], fecha="2027-07-10")
    assert [i.codigo for i in antes.avisos] == ["AMLR-NO-APLICABLE"]
    assert despues.avisos == ()


def test_objetivo_cotizado_solo_es_una_nota():
    r = calcular([("a1", "P", "S", 100, 100)], cotizadas={"S": True})
    assert r.estado == DETERMINADO
    assert r.notas and "65.a" in r.notas[0]


def test_c31_objetivo_que_no_es_sociedad():
    r = calcular([("a1", "P", "S", 100, 100)], clases={"S": "fundacion"})
    assert r.estado == FUERA_DE_ALCANCE


# --- Supuesto supletorio (§8.2) ---------------------------------------------------------


def test_sin_titular_real_identificado():
    cargos = [{"persona": "F", "cargo": "miembro_organo_administracion", "ejecutivo": True},
              {"persona": "G", "cargo": "miembro_organo_administracion", "ejecutivo": False},
              {"persona": "D", "cargo": "directivo", "ejecutivo": True}]
    r = calcular([(f"a{i}", f"P{i}", "S", 20, 20) for i in range(5)], cargos=cargos)
    assert r.estado == SIN_TITULAR
    assert r.titulares == ()
    assert r.cargos_direccion == ("F", "D")  # los ejecutivos; no son titulares reales


def test_cargo_ejecutivo_ocupado_por_entidad_se_excluye_con_aviso():
    cargos = [{"persona": "E", "cargo": "miembro_organo_administracion", "ejecutivo": True, "representante": "X"},
              {"persona": "D", "cargo": "directivo", "ejecutivo": True}]
    r = calcular([(f"a{i}", f"P{i}", "S", 20, 20) for i in range(5)], cargos=cargos, entidades=("E",))
    assert r.cargos_direccion == ("D",)
    assert [i.ids for i in de(r, "CARGO-EJECUTIVO-ENTIDAD")] == [("E",)]


def test_no_determinable_con_hueco():
    """F, sin titulares, tiene el 80 %: H1. P (20 %) podría estar detrás: POS-HUECO; DIR, que
    no participa en S, no."""
    r = calcular([("a1", "P", "S", 20, 20), ("a2", "F", "S", 80, 80)], entidades=("F",))
    assert r.estado == NO_DETERMINABLE
    assert "22.2" in r.motivo
    assert [i.ids for i in de(r, "POS-HUECO")] == [("P",)]


def test_no_determinable_sin_cargos_ejecutivos():
    cargos = [{"persona": "G", "cargo": "miembro_organo_administracion", "ejecutivo": False}]
    r = calcular([(f"a{i}", f"P{i}", "S", 20, 20) for i in range(5)], cargos=cargos)
    assert r.estado == NO_DETERMINABLE


def test_mezcla_no_converge():
    """A tiene el 100 % del capital de B y B el 100 % de los votos de A: cada magnitud por
    separado no tiene ciclo, pero el producto mixto sí, al 100 % (C21)."""
    r = calcular([("a1", "B", "A", 100, 0), ("a2", "P", "A", 0, 100), ("a3", "A", "B", 0, 100),
                  ("a4", "Q", "B", 100, 0), ("a5", "A", "S", 50, 50), ("a6", "R", "S", 50, 50)])
    assert de(r, "MEZCLA-NO-CONVERGE")
    assert not de(r, "POS-MEZCLA")
