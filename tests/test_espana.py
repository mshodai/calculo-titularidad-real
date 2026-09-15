"""Régimen español (src/titularidad/espana.py).

Contra las cifras verificadas (verificacion/test_cifras_ciclos.py: el ejemplo
del modelo, §6.3) y contra lo que el §10 de la especificación dice de cada
ejemplo en España.
"""

import json
from fractions import Fraction

import pytest

from ayudas import entrada, verificacion
from titularidad.carga import cargar
from titularidad.espana import (
    DETERMINADO,
    EXCEPTUADA,
    FUERA_DE_ALCANCE,
    NO_DETERMINABLE,
    SUPLETORIO,
    calcular_espana,
)

V = verificacion()
ADMIN = [{"persona": "ADM", "cargo": "miembro_organo_administracion", "ejecutivo": False}]


def calcular(aristas, **opciones):
    opciones.setdefault("cargos", ADMIN)
    return calcular_espana(entrada(aristas, **opciones))


def titulares(resultado):
    return {t.persona: t for t in resultado.titulares}


def codigos(incidencias):
    return sorted(i.codigo for i in incidencias)


def de(resultado, codigo):
    return [i for i in resultado.posibles + resultado.avisos if i.codigo == codigo]


# --- El ejemplo del modelo (§6.3 y Ej. 7) ------------------------------------------


@pytest.fixture(scope="module")
def modelo():
    return calcular_espana(cargar(json.dumps(V.leer_ejemplo_modelo())).entrada)


def test_modelo_titulares_y_cifras_verificadas(modelo):
    """§6.3: P-ANA por E1 (40,43 / 49,46) y E2 (60 %); P-CARLOS por E1 (25,53 / 29,03)."""
    assert modelo.estado == DETERMINADO
    t = titulares(modelo)
    assert set(t) == {"P-ANA", "P-CARLOS"}
    _, h = V.preparar(V.leer_ejemplo_modelo())
    for p in t:
        for m in ("capital", "votos"):
            assert t[p].participacion[m] == V.metodo_b(h[m], p, "E-OBJETIVO")
        assert t[p].agregado == V.metodo_c(h["votos"], p, "E-OBJETIVO")
    assert t["P-ANA"].participacion == {"capital": Fraction(3800, 94), "votos": Fraction(4600, 93)}
    assert t["P-CARLOS"].participacion == {"capital": Fraction(2400, 94), "votos": Fraction(2700, 93)}
    assert t["P-ANA"].pruebas == {"E1", "E2"} and t["P-ANA"].agregado == 60
    assert t["P-CARLOS"].pruebas == {"E1"} and t["P-CARLOS"].agregado == 20


def test_modelo_ana_controla_el_objetivo(modelo):
    """§6.3: «en España P-ANA controla E-OBJETIVO» (CCom 42.1.a)."""
    t = titulares(modelo)
    assert t["P-ANA"].controla and not t["P-CARLOS"].controla


def test_modelo_marca_por_cuenta_de(modelo):
    t = titulares(modelo)
    assert {a.arista for a in t["P-CARLOS"].por_cuenta_de} == {"p03"}
    assert t["P-ANA"].por_cuenta_de == ()


def test_modelo_aviso_de_hueco_de_diego(modelo):
    """§6.3: 12,77 + 21,28 = 34,04 > 25, así que P-DIEGO podría serlo si participa en E-FONDO."""
    (hueco,) = de(modelo, "POS-HUECO")
    assert hueco.ids == ("P-DIEGO",)
    assert "capital 34,04 %" in hueco.mensaje
    assert codigos(modelo.avisos) == ["H2"]  # ni CICLO-SENS ni UMBRAL-EXACTO (§6.3)


def test_modelo_cadenas_que_explican(modelo):
    t = titulares(modelo)
    assert dict(t["P-ANA"].cadenas["capital"]) == {("P-ANA", "E-OBJETIVO"): 20,
                                                   ("P-ANA", "E-HOLDING", "E-OBJETIVO"): 18}


# --- Ejemplos del §10 ------------------------------------------------------------------


def test_ej1_exactamente_el_25():
    """Nadie pasa del 25 %: supletorio (condicional). UMBRAL-EXACTO: leídos por encima, lo serían."""
    r = calcular([(f"a{i}", f"P{i}", "S", 25, 25) for i in range(1, 5)])
    assert r.estado == SUPLETORIO
    assert r.administradores == ("ADM",)
    assert [i.ids for i in de(r, "UMBRAL-EXACTO")] == [("P1", "P2", "P3", "P4")]


def test_ej2_p_solo_por_l2():
    r = calcular([("a1", "H", "S", 30, 30), ("a2", "X", "S", 70, 70), ("a3", "P", "H", 60, 60), ("a4", "Q", "H", 40, 40)])
    t = titulares(r)
    assert set(t) == {"P", "X"}
    assert t["P"].pruebas == {"E2"} and t["P"].agregado == 30 and t["P"].participacion["capital"] == 18
    assert r.posibles == ()


def test_ej2_variante_con_acumulacion():
    r = calcular([("a1", "A1", "S", 15, 15), ("a2", "A2", "S", 15, 15), ("a3", "X", "S", 70, 70),
                  ("a4", "P", "A1", 60, 60), ("a5", "Q1", "A1", 40, 40), ("a6", "P", "A2", 60, 60), ("a7", "Q2", "A2", 40, 40)])
    t = titulares(r)
    assert t["P"].pruebas == {"E2"} and t["P"].agregado == 30
    assert t["P"].participacion["capital"] == 18  # L1: 9 + 9


def test_ej3_participacion_arriba_control_abajo():
    """P no es titular (L1 = 18, L2 = 0), pero sí con L3: 30 > 25, POS-T."""
    r = calcular([("a1", "C", "S", 60, 60), ("a2", "R", "S", 40, 40), ("a3", "P", "C", 30, 30), ("a4", "Q", "C", 70, 70)])
    t = titulares(r)
    assert set(t) == {"Q", "R"}
    assert t["Q"].participacion["capital"] == 42 and t["Q"].agregado == 60 and t["Q"].controla
    assert [(i.codigo, i.ids) for i in r.posibles] == [("POS-T", ("P",))]
    assert "capital 30,00 %" in r.posibles[0].mensaje


def test_ej4_mayoria_de_capital_sin_mayoria_de_votos():
    r = calcular([("a1", "A", "S", 30, 30), ("a2", "R", "S", 70, 70), ("a3", "P", "A", 60, 40), ("a4", "Q", "A", 40, 60)])
    t = titulares(r)
    assert set(t) == {"Q", "R"}
    assert t["Q"].pruebas == {"E2"} and t["Q"].agregado == 30
    assert r.posibles == ()


def test_ej5_varios_tramos_de_control():
    """L3 = 25, que no es > 25: ni titular ni aviso POS-T. UMBRAL-EXACTO: P y B2 (§10)."""
    r = calcular([("a1", "P", "A", 60, 60), ("a2", "A2", "A", 40, 40), ("a3", "A", "B", 50, 50), ("a4", "B2", "B", 50, 50),
                  ("a5", "B", "C", 60, 60), ("a6", "C2", "C", 40, 40), ("a7", "C", "S", 50, 50), ("a8", "S2", "S", 50, 50)])
    assert set(titulares(r)) == {"S2"}
    assert r.posibles == ()
    assert [i.ids for i in de(r, "UMBRAL-EXACTO")] == [("B2", "P")]


def test_ej5b_sustitucion_o_suma():
    r = calcular([("a1", "P", "A", 50, 50), ("a2", "A2", "A", 50, 50), ("a3", "A", "D", 100, 100),
                  ("a4", "D", "S", 50, 50), ("a5", "S2", "S", 50, 50)])
    assert set(titulares(r)) == {"S2"}
    assert [i.ids for i in de(r, "UMBRAL-EXACTO")] == [("A2", "P")]


def test_ej6_mezcla_de_magnitudes():
    """P: L1 6 / 4,5; producto mixto 0,6 × 0,45 = 27 > 25, POS-MEZCLA."""
    r = calcular([("a1", "P", "A", 60, 10), ("a2", "Q", "A", 40, 90), ("a3", "A", "S", 10, 45), ("a4", "R", "S", 90, 55)])
    t = titulares(r)
    assert set(t) == {"Q", "R"}
    assert t["Q"].pruebas >= {"E2"} and t["Q"].agregado == 45
    assert [(i.codigo, i.ids) for i in r.posibles] == [("POS-MEZCLA", ("P",))]
    assert "27,00 %" in r.posibles[0].mensaje


def test_ej8a_filial_de_cotizada():
    r = calcular([("a1", "L", "S", 60, 60), ("a2", "P", "S", 40, 40)], cotizadas={"L": True})
    assert r.estado == EXCEPTUADA
    assert "«L»" in r.motivo and "60,00 %" in r.motivo and "RD 9.4" in r.motivo


def test_ej8a_variante_exencion_sens():
    """L con el 40 % del capital y el 60 % de los votos: no es filial según C30, pero sí con los votos."""
    r = calcular([("a1", "L", "S", 40, 60), ("a2", "P", "S", 60, 40)], cotizadas={"L": True})
    assert r.estado == DETERMINADO
    assert titulares(r)["P"].participacion["capital"] == 60
    assert [i.ids for i in de(r, "EXENCION-SENS")] == [("L",)]


def test_ej8b_la_filial_es_intermedia():
    r = calcular([("a1", "L", "X", 51, 51), ("a2", "P", "X", 49, 49), ("a3", "X", "S", 70, 70), ("a4", "R", "S", 30, 30)],
                 cotizadas={"L": True})
    t = titulares(r)
    assert set(t) == {"P", "R"}
    assert t["P"].participacion["capital"] == Fraction(343, 10)  # 0,49 × 70
    (cotizada,) = de(r, "COTIZADA")
    assert "capital 35,70 %" in cotizada.mensaje
    assert [i.ids for i in de(r, "EXENCION-SENS")] == [("L",)]
    assert not de(r, "H1")  # lo que va a COTIZADA(L) no es un hueco


# --- Excepciones y alcance ---------------------------------------------------------------


def test_c5_objetivo_cotizado():
    assert calcular([("a1", "P", "S", 100, 100)], cotizadas={"S": True}).estado == EXCEPTUADA


def test_c5_objetivo_cotizado_sin_requisitos_se_calcula():
    r = calcular([("a1", "P", "S", 100, 100)], cotizadas={"S": False})
    assert r.estado == DETERMINADO


def test_c5_intermedia_sin_requisitos_se_recorre():
    r = calcular([("a1", "L", "S", 60, 60), ("a2", "R", "S", 40, 40), ("a3", "P", "L", 100, 100)], cotizadas={"L": False})
    assert set(titulares(r)) == {"P", "R"}
    assert not de(r, "COTIZADA")


def test_c31_objetivo_que_no_es_sociedad():
    r = calcular([("a1", "P", "S", 100, 100)], clases={"S": "fundacion"})
    assert r.estado == FUERA_DE_ALCANCE
    assert "C31" in r.motivo


# --- Supuesto supletorio (§8.1) -------------------------------------------------------------


def test_supletorio_con_representante():
    cargos = [{"persona": "G", "cargo": "miembro_organo_administracion", "ejecutivo": False, "representante": "E"},
              {"persona": "F", "cargo": "miembro_organo_administracion", "ejecutivo": True},
              {"persona": "D", "cargo": "directivo", "ejecutivo": True}]
    r = calcular([(f"a{i}", f"P{i}", "S", 20, 20) for i in range(5)], cargos=cargos, entidades=("G",))
    assert r.estado == SUPLETORIO
    assert r.administradores == ("E", "F")  # el representante de G y F; el directivo no


def test_supletorio_no_determinable_con_hueco():
    """H1: el 80 % de S es de una entidad sin titulares."""
    r = calcular([("a1", "P", "S", 20, 20), ("a2", "F", "S", 80, 80)], entidades=("F",))
    assert r.estado == NO_DETERMINABLE
    assert "Ley 4.4" in r.motivo
    assert {"H1", "H2"} <= {i.codigo for i in r.avisos}


def test_supletorio_no_determinable_sin_cargos():
    r = calcular([(f"a{i}", f"P{i}", "S", 20, 20) for i in range(5)], cargos=[])
    assert r.estado == NO_DETERMINABLE
    assert "AVI-07" in r.motivo


def test_supletorio_no_determinable_si_una_entidad_administra_sin_representante():
    cargos = [{"persona": "G", "cargo": "miembro_organo_administracion", "ejecutivo": False},
              {"persona": "F", "cargo": "miembro_organo_administracion", "ejecutivo": True}]
    r = calcular([(f"a{i}", f"P{i}", "S", 20, 20) for i in range(5)], cargos=cargos, entidades=("G",))
    assert r.estado == NO_DETERMINABLE
    assert "AVI-09" in r.motivo
    assert r.administradores == ("F",)  # los demás se listan igualmente


def test_supletorio_solo_con_directivos():
    cargos = [{"persona": "D", "cargo": "directivo", "ejecutivo": True}]
    r = calcular([(f"a{i}", f"P{i}", "S", 20, 20) for i in range(5)], cargos=cargos)
    assert r.estado == NO_DETERMINABLE


# --- Avisos --------------------------------------------------------------------------------


def test_autocartera_directa_no_da_ciclo_sens():
    """23 % con un 10 % de autocartera: 25,56 % con el método B y 23 % con el A.
    Pero P también pasa por E2 (23 sobre una base de 90, Dir. 22.5), que el
    método A no cambia: el titular es el mismo y no hay CICLO-SENS."""
    r = calcular([("a1", "P", "S", 23, 23), ("a2", "S", "S", 10, 10), ("a3", "R", "S", 67, 67)])
    t = titulares(r)
    assert t["P"].participacion["capital"] == Fraction(230, 9)
    assert t["P"].agregado == Fraction(230, 9) and t["P"].pruebas == {"E1", "E2"}
    assert not de(r, "CICLO-SENS")


def test_ciclo_sens():
    """S tiene el 40 % de H, que tiene el 20 % de S: un ciclo que el dominio no
    neutraliza (S no domina H). P: 24 / 0,92 = 26,09 % con el método B, 24 % con el A."""
    r = calcular([("a1", "P", "S", 24, 24), ("a2", "H", "S", 20, 20), ("a3", "Q", "S", 56, 56),
                  ("a4", "S", "H", 40, 40), ("a5", "R", "H", 60, 60)])
    t = titulares(r)
    assert t["P"].participacion["capital"] == Fraction(600, 23) and t["P"].pruebas == {"E1"}
    assert [i.ids for i in de(r, "CICLO-SENS")] == [("P",)]


def test_pos_formal():
    """N13: T tiene el 30 % por cuenta de Q. Con el capital en el titular formal, T pasaría del 25 %."""
    r = calcular([("a1", "T", "S", 30, 30, "Q"), ("a2", "P", "S", 70, 70)])
    assert set(titulares(r)) == {"P", "Q"}
    assert [(i.codigo, i.ids) for i in r.posibles] == [("POS-FORMAL", ("T",))]


def test_dominio_inestable():
    """Dos sociedades al 70 % la una de la otra: E2 no es determinable; E1 sí."""
    r = calcular([("a1", "B", "A", 70, 70), ("a2", "P", "A", 30, 30), ("a3", "A", "B", 70, 70),
                  ("a4", "Q", "B", 30, 30), ("a5", "A", "S", 100, 100)])
    assert r.estado == DETERMINADO
    assert set(titulares(r)) == {"P", "Q"}
    assert all(t.agregado is None for t in r.titulares)
    assert "DOMINIO-INESTABLE" in {i.codigo for i in r.avisos}


def test_ciclo_cerrado_llega_a_los_avisos():
    r = calcular([("a1", "X1", "X2", 100, 100), ("a2", "X2", "X1", 100, 100),
                  ("a3", "X2", "S", 60, 60), ("a4", "P", "S", 40, 40)])
    assert set(titulares(r)) == {"P"}
    assert {i.codigo for i in r.avisos} >= {"CICLO-CERRADO", "H1"}
