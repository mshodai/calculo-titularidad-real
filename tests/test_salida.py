"""La salida (src/titularidad/salida.py): los dos regímenes y la comparación."""

import json
import re
from pathlib import Path

import pytest

from ayudas import entrada, verificacion
from titularidad.carga import cargar
from titularidad.modelo import ResultadoCarga
from titularidad.salida import (
    AMLR,
    CASOS_NO_RESUELTOS,
    CASOS_POR_AVISO,
    ESPANA,
    ORIGEN_DE_OTROS_AVISOS,
    como_dict,
    como_json,
    informe,
    texto,
)

V = verificacion()
RAIZ = Path(__file__).resolve().parent.parent
CARGOS = [{"persona": "DIR", "cargo": "directivo", "ejecutivo": True},
          {"persona": "ADM", "cargo": "miembro_organo_administracion", "ejecutivo": False}]


def informe_de(aristas, **opciones):
    opciones.setdefault("cargos", CARGOS)
    opciones.setdefault("fecha", "2027-07-10")
    return informe(ResultadoCarga(entrada(aristas, **opciones), (), ()))


def fila(inf, persona):
    return next(f for f in inf.filas if f.persona == persona)


# --- El ejemplo del modelo ---------------------------------------------------------------


@pytest.fixture(scope="module")
def modelo():
    return informe(cargar(json.dumps(V.leer_ejemplo_modelo())))


def test_modelo_comparacion(modelo):
    """Ej. 7: los dos regímenes identifican a P-ANA y P-CARLOS; P-DIEGO, posible en los dos."""
    assert [(f.persona, f.espana, f.detalle_espana, f.amlr, f.detalle_amlr) for f in modelo.filas] == [
        ("P-ANA", "titular", ("E1", "E2"), "titular", ("A1", "A3")),
        ("P-CARLOS", "titular", ("E1",), "titular", ("A1",)),
        ("P-DIEGO", "posible", ("POS-HUECO",), "posible", ("POS-HUECO",)),
    ]
    assert not any(f.difiere for f in modelo.filas)


def test_modelo_difieren_en_el_criterio(modelo):
    """§6.3: «en España P-ANA controla E-OBJETIVO […]; en el AMLR nadie la controla»."""
    (diferencia,) = modelo.diferencias
    assert "«P-ANA»" in diferencia and "controla la entidad en España" in diferencia


def plano(t):
    """El texto sin los saltos de línea del ajuste a 100 columnas."""
    return " ".join(t.split())


def test_modelo_texto(modelo):
    assert texto(modelo).startswith("Titularidad real de «E-OBJETIVO» a 2026-09-15\n\nResultado de un cálculo bajo las lecturas")
    t = plano(texto(modelo))
    assert "no una determinación jurídica" in t
    assert "Los dos regímenes coinciden en quién es titular real." in t
    assert "P-ANA: E1 (L1) capital 40,43 %, votos 49,46 %; E2 (L2) 60,00 %; controla la entidad" in t
    assert "Por cuenta de otro: p03 (titular formal: P-BRUNO)" in t
    assert "→ N3: AMLR: si el art. 54 sustituye al 52.1 o se añade a él" in t
    assert "LECTURAS DE LAS QUE DEPENDE ESTE RESULTADO" in t
    assert "AVI-06" in t  # los avisos de la validación también salen
    # C32: el AMLR no es estable por el ART54-SENS de P-CARLOS; España, sí
    assert "~ AMLR: el resultado no es estable." in t and "~ España" not in t
    # C33: los dos pueden no estar completos por el hueco de E-FONDO (POS-HUECO de P-DIEGO)
    assert "? España: el resultado puede no estar completo." in t and "? AMLR" in t


def test_modelo_json(modelo):
    datos = json.loads(como_json(modelo))
    ana = next(t for t in datos["espana"]["titulares"] if t["persona"] == "P-ANA")
    assert ana["E1"]["capital"] == {"exacto": "1900/47", "redondeado": "40.43"}  # 3800/94, verificado
    assert ana["E2"] == {"exacto": "60", "redondeado": "60.00"}
    carlos = next(t for t in datos["amlr"]["titulares"] if t["persona"] == "P-CARLOS")
    assert carlos["A1"]["votos"] == {"exacto": "900/31", "redondeado": "29.03"}  # 2700/93
    assert carlos["por_cuenta_de"][0]["titular_formal"] == "P-BRUNO"
    art54 = next(a for a in datos["amlr"]["avisos"] if a["codigo"] == "ART54-SENS")
    assert art54["casos"] == ["N3"]
    assert datos["advertencia"].startswith("Resultado de un cálculo")


def test_json_sin_numeros_en_coma_flotante(modelo):
    """Los valores van como texto (fracción exacta y redondeo), nunca como float (C6)."""
    def recorrer(x):
        if isinstance(x, dict):
            for v in x.values():
                recorrer(v)
        elif isinstance(x, list):
            for v in x:
                recorrer(v)
        else:
            assert not isinstance(x, float), x
    recorrer(json.loads(como_json(modelo)))


# --- Divergencias -------------------------------------------------------------------------


def test_ej3_titular_solo_en_el_amlr_por_el_54b():
    inf = informe_de([("a1", "C", "S", 60, 60), ("a2", "R", "S", 40, 40), ("a3", "P", "C", 30, 30), ("a4", "Q", "C", 70, 70)])
    p = fila(inf, "P")
    assert p.difiere and (p.espana, p.detalle_espana, p.amlr) == ("posible", ("POS-T",), "titular")
    (diferencia,) = inf.diferencias
    assert "54.b" in diferencia and "En España queda como posible (POS-T)" in diferencia
    assert "≠ Resultado distinto en cada régimen para 1 de 3 personas." in plano(texto(inf))


def test_ej1_umbral_y_estado():
    inf = informe_de([(f"a{i}", f"P{i}", "S", 25, 25) for i in range(1, 5)])
    assert (inf.espana.estado, inf.amlr.estado) == ("supletorio (condicional)", "determinado")
    assert inf.diferencias[0].startswith("Estado: en España «supletorio (condicional)»")
    assert all("«25 % o más» y España «superior al 25»" in d for d in inf.diferencias[1:])
    t = plano(texto(inf))
    assert "≠ Los dos regímenes llegan a estados distintos." in t
    assert "Administradores a los que se presume el control (Ley 4.2.b bis, C22): ADM" in t


def test_titular_solo_en_espana_por_la_agregacion_del_art_42():
    """P domina K sumando su 30 % y el 25 % de D, que domina: L2. En el AMLR ninguna prueba
    lo alcanza, pero con el control agregado (N8) sí: POS-AGREGADO."""
    inf = informe_de([("a1", "P", "K", 30, 30), ("a2", "D", "K", 25, 25), ("a3", "Y", "K", 45, 45),
                      ("a4", "P", "D", 60, 60), ("a5", "X", "D", 40, 40), ("a6", "K", "S", 30, 30), ("a7", "R", "S", 70, 70)])
    p = fila(inf, "P")
    assert (p.espana, p.detalle_espana, p.amlr, p.detalle_amlr) == ("titular", ("E2",), "posible", ("POS-AGREGADO",))
    (diferencia,) = inf.diferencias
    assert "art. 42 (L2)" in diferencia and "En el AMLR queda como posible (POS-AGREGADO)" in diferencia


def test_ej8a_exceptuada_en_espana():
    inf = informe_de([("a1", "L", "S", 60, 60), ("a2", "P", "S", 40, 40)], cotizadas={"L": True})
    assert inf.espana.estado == "exceptuada"
    assert any("en España no se calcula («exceptuada»)" in d for d in inf.diferencias)


def test_sin_titulares_en_ningun_regimen():
    inf = informe_de([(f"a{i}", f"P{i}", "S", 20, 20) for i in range(5)])
    t = plano(texto(inf))
    assert "Nadie aparece como titular ni como posible titular en ningún régimen." in t
    assert "Cargos de dirección de alto nivel (22.2 y 63.4, C23). No son titulares reales: DIR" in t


def test_entrada_no_valida():
    inf = informe(cargar("{}"))
    assert texto(inf).startswith("La entrada no es válida: no se calcula.")
    assert como_dict(inf)["valida"] is False


# --- Cada aviso con su caso no resuelto ------------------------------------------------------


def test_todos_los_avisos_tienen_origen():
    """Cada código de aviso que emite el cálculo tiene su caso no resuelto o su origen."""
    codigos = set()
    for fichero in ("espana.py", "amlr.py", "propagacion.py", "control.py"):
        fuente = (RAIZ / "src" / "titularidad" / fichero).read_text(encoding="utf-8")
        codigos |= set(re.findall(r'Incidencia\(\s*"([A-Z0-9-]+)"', fuente))
    assert codigos, "no se han encontrado códigos"
    sin_origen = codigos - set(CASOS_POR_AVISO) - set(ORIGEN_DE_OTROS_AVISOS)
    assert not sin_origen
    for casos in CASOS_POR_AVISO.values():
        assert set(casos) <= {ESPANA, AMLR}
        assert all(n in CASOS_NO_RESUELTOS for ns in casos.values() for n in ns)


def test_la_correspondencia_sigue_ambiguedades_md():
    """La columna «Señal en la salida» de docs/ambiguedades.md: cada código que nombra señala ese caso."""
    ambiguedades = (RAIZ / "docs" / "ambiguedades.md").read_text(encoding="utf-8")
    filas = re.findall(r"^\| (N\d+) \|.*\| ([^|]*) \|$", ambiguedades, re.MULTILINE)
    assert len(filas) == 14
    for n, senal in filas:
        for codigo in re.findall(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b", senal):
            regimenes = CASOS_POR_AVISO.get(codigo, {})
            assert any(n in casos for casos in regimenes.values()), (n, codigo)
    # Y al revés: cada caso que da la salida está en la tabla con ese código.
    por_caso = dict(filas)
    for codigo, regimenes in CASOS_POR_AVISO.items():
        for casos in regimenes.values():
            for n in casos:
                if codigo not in ("T-NO-CONVERGE", "MEZCLA-NO-CONVERGE"):  # acompañan a POS-T y POS-MEZCLA
                    assert codigo in por_caso[n], (codigo, n)


def test_ciclo_sens_en_espana_no_cita_n12():
    """N12 (autocartera y control) es del AMLR; en España CICLO-SENS solo afecta a E1 (N7)."""
    assert CASOS_POR_AVISO["CICLO-SENS"][ESPANA] == ("N7",)
    assert "N12" in CASOS_POR_AVISO["CICLO-SENS"][AMLR]


def test_estabilidad_en_el_json(modelo):
    datos = json.loads(como_json(modelo))
    assert (datos["espana"]["estable"], datos["espana"]["inestable_por"]) == (True, [])
    assert (datos["amlr"]["estable"], datos["amlr"]["inestable_por"]) == (False, ["ART54-SENS"])


def test_los_avisos_de_c32_tienen_origen():
    from titularidad.salida import CAMBIARIA_CON_OTRA_LECTURA, SIN_COMPROBAR
    assert not (CAMBIARIA_CON_OTRA_LECTURA & SIN_COMPROBAR)
    for codigo in CAMBIARIA_CON_OTRA_LECTURA | SIN_COMPROBAR:
        assert codigo in CASOS_POR_AVISO or codigo in ORIGEN_DE_OTROS_AVISOS


def test_c32_sigue_la_especificacion():
    """Los dos grupos de C32 (§9) son los mismos que usa la salida."""
    from titularidad.salida import CAMBIARIA_CON_OTRA_LECTURA, SIN_COMPROBAR
    especificacion = (RAIZ / "docs" / "especificacion-calculo.md").read_text(encoding="utf-8")
    c32 = especificacion[especificacion.index("**[C32"):]
    grupo1 = c32[c32.index("otra lectura que el cálculo comprueba:**"):c32.index("Es lo que señalan")]
    grupo2 = c32[c32.index("no se ha podido hacer:**"):c32.index("\n\nUn «determinado»")]
    codigo = r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b"
    assert set(re.findall(codigo, grupo1)) == CAMBIARIA_CON_OTRA_LECTURA
    assert set(re.findall(codigo, grupo2)) == SIN_COMPROBAR

# X tiene el 30 % de S; el 60 % de X no está identificado y Q1 a Q4 tienen un 10 % cada uno.
# Lo que llega a S sin identificar es un 18 % (sin H1), pero quien tenga ese 60 % controla X (H3),
# y Q1 a Q4 lo controlarían con el hueco (POS-HUECO y H2, C34).
HUECO_QUE_CONTROLA = [(f"q{i}", f"Q{i}", "X", 10, 10) for i in range(1, 5)] + [("a1", "X", "S", 30, 30)]


def test_inestable_incompleto_o_las_dos_cosas(modelo):
    """C32 y C33 son criterios separados, y la salida dice cuál se da."""
    from titularidad.salida import incompleto_por, inestable_por
    # Las dos: el AMLR del modelo (ART54-SENS; POS-HUECO y H2).
    assert inestable_por(modelo.amlr) == ("ART54-SENS",)
    assert incompleto_por(modelo.amlr) == ("H2", "POS-HUECO")
    # Solo incompleto: España en el modelo, y el hueco que controla X.
    assert inestable_por(modelo.espana) == () and incompleto_por(modelo.espana) == ("H2", "POS-HUECO")
    hueco = informe_de(HUECO_QUE_CONTROLA + [("a2", "R", "S", 70, 70)])
    for r in (hueco.espana, hueco.amlr):
        assert (inestable_por(r), incompleto_por(r)) == ((), ("H2", "H3", "POS-HUECO"))
    # Solo inestable: el 25 % justo del Ej. 1 en el AMLR, sin huecos.
    ej1 = informe_de([(f"a{i}", f"P{i}", "S", 25, 25) for i in range(1, 5)])
    assert (inestable_por(ej1.amlr), incompleto_por(ej1.amlr)) == (("UMBRAL-EXACTO",), ())


def test_completitud_en_el_json(modelo):
    datos = json.loads(como_json(modelo))
    for regimen in ("espana", "amlr"):
        assert (datos[regimen]["completo"], datos[regimen]["incompleto_por"]) == (False, ["H2", "POS-HUECO"])


def test_c33_sigue_la_especificacion():
    """Los avisos de C33 (§9) son los mismos que usa la salida, y no se solapan con los de C32."""
    from titularidad.salida import CAMBIARIA_CON_OTRA_LECTURA, FALTAN_DATOS, SIN_COMPROBAR
    especificacion = (RAIZ / "docs" / "especificacion-calculo.md").read_text(encoding="utf-8")
    c33 = especificacion[especificacion.index("**[C33"):]
    lista = c33[c33.index("No lo es si lleva alguno de estos avisos:"):c33.index("Lo que llega por cotizadas")]
    assert set(re.findall(r"\*\*([A-Z][A-Z0-9-]*)", lista)) | set(re.findall(r"\b(POS-HUECO)\b", lista)) == FALTAN_DATOS
    assert not (FALTAN_DATOS & (CAMBIARIA_CON_OTRA_LECTURA | SIN_COMPROBAR))


def test_ambiguedades_md_tiene_cada_caso_con_sus_apartados():
    """Los catorce casos N y los del formato del dato, cada uno con sus apartados."""
    texto_ = (RAIZ / "docs" / "ambiguedades.md").read_text(encoding="utf-8")
    secciones = re.split(r"^## ", texto_, flags=re.MULTILINE)
    casos = {s.split(".")[0]: s for s in secciones if re.match(r"[NF]\d+\.", s)}
    assert sorted(casos, key=lambda c: (c[0], int(c[1:]))) == [f"F{i}" for i in range(1, 5)] + [f"N{i}" for i in range(1, 15)]
    for nombre, seccion in casos.items():
        origen = "**Qué dice la norma.**" if nombre.startswith("N") else "**De dónde viene.**"
        for apartado in (origen, "**Por qué no determina", "**Qué hace esta implementación.**", "**Cómo se señala en la salida.**"):
            assert apartado in seccion, (nombre, apartado)
        if nombre.startswith("N"):
            assert "**Régimen.**" in seccion, nombre
    assert set(CASOS_NO_RESUELTOS) <= set(casos)  # los casos que cita la salida están documentados
