"""Motor de propagación (src/titularidad/propagacion.py).

Las cifras de referencia son las de verificacion/test_cifras_ciclos.py, que ya
se comprueban contra los documentos. Aquí se exige que el motor dé exactamente
lo mismo que esa verificación, calculándolas con sus propias funciones y además
con los valores literales que ella afirma.
"""

import json
from fractions import Fraction

import pytest

from ayudas import entrada, verificacion
from titularidad.carga import cargar
from titularidad.modelo import MAGNITUDES
from titularidad.propagacion import (
    NO_IDENTIFICADO,
    FueraDeAlcance,
    OPACA,
    Virtual,
    enumerar_cadenas,
    preparar,
    propagar,
    serie_completa,
)

V = verificacion()


def hueco(entidad):
    return Virtual(NO_IDENTIFICADO, entidad)


def por_texto(diccionario):
    """Claves como texto, para comparar con la verificación (que usa texto para los virtuales)."""
    return {str(k): v for k, v in diccionario.items()}


# --- El ejemplo del modelo: las mismas cifras que la verificación --------------

MODELO = cargar(json.dumps(V.leer_ejemplo_modelo())).entrada
S = "E-OBJETIVO"


@pytest.fixture(scope="module")
def modelo():
    grafo = preparar(MODELO)
    return grafo, propagar(grafo)


def test_modelo_mismo_grafo_que_la_verificacion(modelo):
    grafo, _ = modelo
    _, h = V.preparar(V.leer_ejemplo_modelo())
    for m in MAGNITUDES:
        assert {(str(z), y): v for (z, y), v in grafo.h[m].items()} == h[m]


@pytest.mark.parametrize("m", MAGNITUDES)
def test_modelo_metodo_b_igual_que_la_verificacion(modelo, m):
    """Método B: own_m(X, Y) para todos los pares, idéntico a verificacion.metodo_b."""
    grafo, propagacion = modelo
    _, h = V.preparar(V.leer_ejemplo_modelo())
    own = serie_completa(grafo, m)
    for origen, destinos in own.items():
        for destino, valor in destinos.items():
            assert valor == V.metodo_b(h[m], str(origen), destino), (origen, destino)
    esperado = {str(x): V.metodo_b(h[m], str(x), S) for x in propagacion.serie[m] if str(x) in {z for z, _ in h[m]}}
    assert {k: v for k, v in por_texto(propagacion.serie[m]).items() if k in esperado} == esperado


def test_modelo_metodo_b_cifras_de_la_verificacion(modelo):
    """Los valores literales que afirma verificacion (test_metodo_b_capital y _votos)."""
    _, propagacion = modelo
    titulares = ["P-ANA", "P-CARLOS", "P-DIEGO", hueco("E-FONDO")]
    capital = [propagacion.serie["capital"][x] for x in titulares]
    votos = [propagacion.serie["votos"][x] for x in titulares]
    assert capital == [Fraction(3800, 94), Fraction(2400, 94), Fraction(1200, 94), Fraction(2000, 94)]
    assert votos == [Fraction(4600, 93), Fraction(2700, 93), Fraction(2000, 93), 0]
    assert propagacion.serie["capital"]["P-BRUNO"] == 0  # C2: el testaferro no recibe nada


def test_modelo_reparte_el_100(modelo):
    """C20: con el método B, titulares últimos más huecos suman exactamente 100."""
    _, propagacion = modelo
    for m in MAGNITUDES:
        ultimos = [x for x in propagacion.serie[m] if isinstance(x, Virtual) or x.startswith("P-")]
        assert sum(propagacion.serie[m][x] for x in ultimos) == 100


@pytest.mark.parametrize("m", MAGNITUDES)
def test_modelo_metodo_a_igual_que_la_verificacion(modelo, m):
    _, propagacion = modelo
    _, h = V.preparar(V.leer_ejemplo_modelo())
    for x in ["P-ANA", "P-CARLOS", "P-DIEGO", hueco("E-FONDO"), "E-HOLDING", "E-BETA"]:
        assert propagacion.simples[m][x] == V.metodo_a(h[m], str(x), S), x
    titulares = ["P-ANA", "P-CARLOS", "P-DIEGO", hueco("E-FONDO")]
    literales = {"capital": [38, 24, 12, 20], "votos": [46, 27, 20, 0]}
    assert [propagacion.simples[m][x] for x in titulares] == literales[m]


def test_modelo_metodo_c_igual_que_la_verificacion(modelo):
    _, propagacion = modelo
    _, h = V.preparar(V.leer_ejemplo_modelo())
    _, va, base = V.dominio(h["votos"])
    assert propagacion.dominio.base(S) == base(S) == 100
    for x in propagacion.directiva:
        if str(x) in {z for z, _ in h["votos"]}:
            assert propagacion.directiva[x] == va(str(x), S) * 100 / base(S), x
    assert propagacion.directiva["P-ANA"] == 60
    assert propagacion.directiva["P-CARLOS"] == 20
    assert S in propagacion.dominio.dependientes["P-ANA"]


def test_modelo_sin_avisos_de_convergencia(modelo):
    grafo, propagacion = modelo
    assert grafo.ciclos_cerrados == ()
    assert propagacion.avisos == ()


def test_modelo_cadenas_de_ana(modelo):
    """C8: la explicación lista las cadenas sin repeticiones."""
    grafo, _ = modelo
    cadenas = dict(enumerar_cadenas(grafo, "capital", "P-ANA"))
    assert cadenas == {("P-ANA", S): 20, ("P-ANA", "E-HOLDING", S): 18}


# --- Ejemplo del §4.2 del modelo de datos --------------------------------------

S42 = entrada([("a1", "P", "S", 45, 45), ("a2", "Q", "S", 35, 35), ("a3", "H", "S", 20, 20),
               ("a4", "S", "H", 60, 60), ("a5", "R", "H", 40, 40)])


def test_seccion_42_los_tres_metodos():
    propagacion = propagar(preparar(S42))
    h = V.grafo_simple([("P", "S", 45), ("Q", "S", 35), ("H", "S", 20), ("S", "H", 60), ("R", "H", 40)])
    for x in "PQR":
        assert propagacion.serie["votos"][x] == V.metodo_b(h["votos"], x, "S")
        assert propagacion.simples["votos"][x] == V.metodo_a(h["votos"], x, "S")
        assert propagacion.directiva[x] == V.metodo_c(h["votos"], x, "S")
    assert [propagacion.serie["votos"][x] for x in "PQR"] == [Fraction(4500, 88), Fraction(3500, 88), Fraction(800, 88)]
    assert [propagacion.simples["votos"][x] for x in "PQR"] == [45, 35, 8]
    assert [propagacion.directiva[x] for x in "PQR"] == [Fraction(225, 4), Fraction(175, 4), 0]


# --- C2: participaciones por cuenta de otro ------------------------------------


def test_c2_atribuciones_con_marca(modelo):
    grafo, _ = modelo
    marcas = {(a.arista, a.titular_formal, a.principal, a.magnitud) for a in grafo.atribuciones}
    assert marcas == {("p03", "P-BRUNO", "P-CARLOS", "capital"), ("p03", "P-BRUNO", "P-CARLOS", "votos")}


def test_c1_despues_de_c2_no_pierde_al_principal_sin_participaciones_propias():
    """§2, orden: Q no tiene aristas en la entrada; solo T tiene el 30 % por cuenta de Q.

    Con C1 antes de C2, Q quedaba fuera del subgrafo y se perdía un titular real.
    """
    grafo = preparar(entrada([("a1", "T", "S", 30, 30, "Q"), ("a2", "P", "S", 70, 70)]))
    propagacion = propagar(grafo)
    assert propagacion.serie["capital"]["Q"] == 30
    assert propagacion.serie["capital"]["T"] == 0
    assert [(a.titular_formal, a.principal) for a in grafo.atribuciones] == [("T", "Q"), ("T", "Q")]


def test_c29_lectura_contraria_en_las_dos_magnitudes():
    """AMLR, N9: las cifras de verificacion.test_sin_c2_bruno_no_llega."""
    propagacion = propagar(preparar(MODELO, c2_en=()))
    assert propagacion.serie["capital"]["P-BRUNO"] == Fraction(1800, 94)
    assert propagacion.serie["votos"]["P-BRUNO"] == Fraction(2000, 93)


def test_c29_lectura_contraria_solo_en_capital():
    """España, N13: las cifras de verificacion.test_sin_c2_en_capital_espana."""
    grafo = preparar(MODELO, c2_en=("votos",))
    propagacion = propagar(grafo)
    assert propagacion.serie["capital"]["P-BRUNO"] == Fraction(1800, 94)
    assert propagacion.serie["votos"]["P-BRUNO"] == 0
    assert propagacion.serie["capital"]["P-CARLOS"] == Fraction(600, 94)
    assert propagacion.serie["votos"]["P-CARLOS"] == Fraction(2700, 93)
    assert {a.magnitud for a in grafo.atribuciones} == {"votos"}


# --- C4: huecos ------------------------------------------------------------------


def test_c4_hueco_por_suma_incompleta():
    propagacion = propagar(preparar(entrada([("a1", "P", "S", 80, 100)])))
    assert propagacion.serie["capital"][hueco("S")] == 20
    assert hueco("S") not in {x for x, v in propagacion.serie["votos"].items() if v}


def test_c4_sin_hueco_dentro_de_la_tolerancia_de_redondeo():
    """D15: tres tercios redondeados (99,9999) son un accionariado completo."""
    grafo = preparar(entrada([(f"a{i}", f"P{i}", "S", "33.3333", "33.3333") for i in range(3)]))
    assert grafo.virtuales() == set()


def test_c4_magnitud_desconocida_va_al_hueco():
    grafo = preparar(entrada([("a1", "P", "S", 60, 60), ("a2", "Q", "S", "null", 40)]))
    propagacion = propagar(grafo)
    assert propagacion.serie["capital"]["Q"] == 0
    assert propagacion.serie["capital"][hueco("S")] == 40


def test_c4_entidad_que_no_es_sociedad_es_opaca():
    e = entrada([("a1", "F", "S", 30, 30), ("a2", "P", "S", 70, 70), ("a3", "Q", "F", 100, 100)],
                clases={"F": "fundacion"})
    propagacion = propagar(preparar(e))
    assert propagacion.serie["capital"][Virtual(OPACA, "F")] == 30
    assert propagacion.serie["capital"]["Q"] == 0


def test_c31_objetivo_que_no_es_sociedad_queda_fuera_de_alcance():
    """C31: no se calcula; no es un caso de «no hay titulares»."""
    e = entrada([("a1", "P", "S", 100, 100)], clases={"S": "fundacion"})
    with pytest.raises(FueraDeAlcance, match="fuera de alcance"):
        preparar(e)


def test_detener_para_el_regimen():
    """El mecanismo que usará COTIZADA (C5), sin decidir el motor quién cotiza."""
    e = entrada([("a1", "L", "S", 60, 60), ("a2", "P", "S", 40, 40), ("a3", "Q", "L", 100, 100)])
    propagacion = propagar(preparar(e, detener={"L": "COTIZADA"}))
    assert propagacion.serie["capital"][Virtual("COTIZADA", "L")] == 60
    assert propagacion.serie["capital"]["Q"] == 0


# --- Autocartera (N12) -------------------------------------------------------------


def test_autocartera_serie_completa_y_cadenas_simples():
    """§6.2: con un 10 % de autocartera, 48 % pasa a 48 / 0,9 = 53,33 % con el método B."""
    propagacion = propagar(preparar(entrada([("a1", "P", "S", 48, 48), ("a2", "S", "S", 10, 10), ("a3", "R", "S", 42, 42)])))
    assert propagacion.serie["capital"]["P"] == Fraction(160, 3)
    assert propagacion.simples["capital"]["P"] == 48


# --- No convergencia -----------------------------------------------------------------


def test_ciclo_cerrado_sin_titulares_externos():
    """§6.4: X1 y X2 se tienen entre sí al 100 %."""
    grafo = preparar(entrada([("a1", "X1", "X2", 100, 100), ("a2", "X2", "X1", 100, 100),
                              ("a3", "X2", "S", 60, 60), ("a4", "P", "S", 40, 40)]))
    propagacion = propagar(grafo)
    assert [(c.magnitud, c.entidades, c.con_titulares_externos) for c in grafo.ciclos_cerrados] == [
        ("capital", ("X1", "X2"), False), ("votos", ("X1", "X2"), False)]
    assert [a.codigo for a in propagacion.avisos] == ["CICLO-CERRADO", "CICLO-CERRADO"]
    assert propagacion.serie["capital"]["P"] == 40
    assert propagacion.serie["capital"][hueco("X2")] == 60
    assert sum(v for x, v in propagacion.serie["capital"].items() if isinstance(x, Virtual) or x == "P") == 100


def test_ciclo_que_no_converge_por_el_redondeo():
    """§6.4, caso límite: hay un titular de fuera (P, 0,0001 %), pero el exceso
    de redondeo que admite D15 hace que A tenga el 100,0001 % de B."""
    grafo = preparar(entrada([
        ("a1", "B", "A", 100, 100),
        ("a2", "A", "B", "60.0001", "60.0001"),
        ("a3", "Y", "B", 40, 40, "A"),  # por cuenta de A: tras C2, A suma 100,0001
        ("a4", "P", "B", "0.0001", "0.0001"),
        ("a5", "Z", "B", 0, 0),  # cuarta arista con valor: la tolerancia llega a 0,0002
        ("a6", "A", "S", 50, 50),
        ("a7", "R", "S", 50, 50),
    ]))
    assert [(c.entidades, c.con_titulares_externos) for c in grafo.ciclos_cerrados] == [
        (("A", "B"), True), (("A", "B"), True)]
    propagacion = propagar(grafo)
    assert propagacion.serie["capital"]["R"] == 50


def test_ciclo_que_converge_no_avisa(modelo):
    grafo, _ = modelo
    assert grafo.ciclos_cerrados == ()


# Dos sociedades que se tienen al 70 % la una a la otra: el dominio oscila.
CRUZADAS = entrada([("a1", "B", "A", 70, 70), ("a2", "P", "A", 30, 30), ("a3", "A", "B", 70, 70),
                    ("a4", "Q", "B", 30, 30), ("a5", "A", "S", 100, 100)])


def test_dominio_inestable():
    propagacion = propagar(preparar(CRUZADAS))
    assert not propagacion.dominio.estable
    assert propagacion.directiva is None
    assert propagacion.avisos == ()  # DOMINIO-INESTABLE es español: lo da control.py
    # La verificación, con el mismo algoritmo, también lo detecta.
    h = V.grafo_simple([("B", "A", 70), ("P", "A", 30), ("A", "B", 70), ("Q", "B", 30), ("A", "S", 100)])
    with pytest.raises(V.DominioInestable):
        V.dominio(h["votos"])
    # Los métodos A y B sí se calculan: el ciclo converge.
    assert propagacion.serie["capital"]["P"] == Fraction(30, 51) * 100


def test_base_cero_en_el_objetivo():
    """Decisión marcada con AMBIGÜEDAD: si base(S) = 0, el método C no da proporción.

    Todos los votos de S los tienen S misma (30 %) y A (70 %), que depende de S
    porque S domina B y juntas pasan del 50 % de A. El dominio se estabiliza.
    """
    propagacion = propagar(preparar(entrada([
        ("a1", "A", "S", 70, 70), ("a2", "S", "S", 30, 30),
        ("a3", "A", "A", 40, 40), ("a4", "B", "A", 30, 30), ("a5", "S", "A", 30, 30),
        ("a6", "S", "B", 60, 60), ("a7", "Q", "B", 40, 40),
    ])))
    assert propagacion.dominio.estable
    assert propagacion.dominio.base("S") == 0
    assert propagacion.directiva is None
    assert propagacion.avisos == ()
