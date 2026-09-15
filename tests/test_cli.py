"""Línea de órdenes calcular-titularidad: códigos de salida, --json y --regimen."""

import json
import tomllib
from pathlib import Path

from ayudas import verificacion
from titularidad.carga import cargar
from titularidad.cli import main
from titularidad.salida import como_dict, informe

V = verificacion()
RAIZ = Path(__file__).resolve().parent.parent
CARGOS = [{"persona": "ADM", "cargo": "miembro_organo_administracion", "ejecutivo": True}]


def escribir(tmp_path, datos, nombre="entrada.json"):
    ruta = tmp_path / nombre
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return str(ruta)


def estructura(aristas):
    """Entrada con S (con un administrador ejecutivo) y personas o entidades según haga falta."""
    participadas = {"S"} | {p for _, _, p, _ in aristas}
    nombres = sorted(participadas | {t for _, t, _, _ in aristas} | {"ADM"})
    nodos = [
        {"id": n, "tipo": "entidad_juridica", "denominacion": n, "clase": "sociedad",
         **({"cargos": CARGOS} if n == "S" else {})}
        if n in participadas else {"id": n, "tipo": "persona_fisica", "nombre": n}
        for n in nombres
    ]
    return {
        "version_modelo": "0.1", "fecha_referencia": "2027-07-10", "entidad_objetivo": "S", "nodos": nodos,
        "participaciones": [{"id": i, "titular": t, "participada": p, "capital": v, "votos": v}
                            for i, t, p, v in aristas],
    }


EJ2 = estructura([("a1", "H", "S", 30), ("a2", "X", "S", 70), ("a3", "P", "H", 60), ("a4", "Q", "H", 40)])
EJ3 = estructura([("a1", "C", "S", 60), ("a2", "R", "S", 40), ("a3", "P", "C", 30), ("a4", "Q", "C", 70)])
# P y Q tienen el 50 % de H, que tiene el 30 % de S. Con el 50 % justo nadie controla H;
# leído justo por encima, P y Q la controlarían y serían titulares (A3 y E2).
MITAD = estructura([("a1", "P", "H", 50), ("a2", "Q", "H", 50), ("a3", "H", "S", 30), ("a4", "R", "S", 70)])
EJ1 = estructura([(f"a{i}", f"P{i}", "S", 25) for i in range(1, 5)])


# --- Códigos de salida -------------------------------------------------------------------


def test_determinados_estables_y_coinciden_devuelve_0(tmp_path, capsys):
    """Ej. 2: los dos dan P y X, sin avisos (P por E2 en España y por A3 en el AMLR)."""
    assert main([escribir(tmp_path, EJ2)]) == 0
    assert "Los dos regímenes coinciden en quién es titular real." in capsys.readouterr().out


def test_modelo_no_es_estable_devuelve_1(tmp_path, capsys):
    """Ej. 7: los dos dan los mismos titulares, pero en el AMLR P-CARLOS depende de N3 (ART54-SENS)."""
    assert main([escribir(tmp_path, V.leer_ejemplo_modelo())]) == 1
    salida = capsys.readouterr().out
    assert "Los dos regímenes coinciden en quién es titular real." in salida
    assert "~ AMLR: el resultado no es estable." in salida


def test_umbral_exacto_devuelve_1(tmp_path, capsys):
    """Los dos determinados y con el mismo titular (R), pero con el 50 % justo de H: UMBRAL-EXACTO."""
    assert main(["--json", escribir(tmp_path, MITAD)]) == 1
    emitido = json.loads(capsys.readouterr().out)
    assert [f["difiere"] for f in emitido["comparacion"]] == [False]
    for regimen in ("espana", "amlr"):
        assert emitido[regimen]["estado"] == "determinado"
        assert emitido[regimen]["inestable_por"] == ["UMBRAL-EXACTO"]


def test_regimenes_que_difieren_devuelve_1(tmp_path):
    """Ej. 3: P es titular en el AMLR (A4) y no en España."""
    assert main([escribir(tmp_path, EJ3)]) == 1


def test_estado_no_determinado_devuelve_1(tmp_path):
    """Ej. 1: en España, supletorio (condicional)."""
    assert main([escribir(tmp_path, EJ1)]) == 1


def test_un_solo_regimen(tmp_path, capsys):
    """Ej. 3 con un solo régimen: el AMLR, determinado y estable; España, con POS-T (N1/N2)."""
    ruta = escribir(tmp_path, EJ3)
    assert main(["--regimen", "amlr", ruta]) == 0
    salida = capsys.readouterr().out
    assert "AMLR ·" in salida and "ESPAÑA ·" not in salida and "COMPARACIÓN" not in salida
    assert main(["--regimen", "espana", ruta]) == 1
    # Ej. 1: el AMLR queda determinado, pero con el 25 % justo no es estable (UMBRAL-EXACTO).
    assert main(["--regimen", "amlr", escribir(tmp_path, EJ1, "ej1.json")]) == 1


def test_fichero_inexistente_devuelve_2(tmp_path, capsys):
    assert main([str(tmp_path / "no-existe.json")]) == 2
    assert "no existe el fichero" in capsys.readouterr().err


def test_json_mal_formado_devuelve_2(tmp_path, capsys):
    ruta = tmp_path / "roto.json"
    ruta.write_text('{"version_modelo": ', encoding="utf-8")
    assert main([str(ruta)]) == 2
    assert "ERR-01" in capsys.readouterr().out


def test_entrada_no_valida_devuelve_2(tmp_path, capsys):
    datos = json.loads(json.dumps(EJ3))
    datos["participaciones"][0]["capital"] = 120  # ERR-06
    assert main([escribir(tmp_path, datos)]) == 2
    salida = capsys.readouterr().out
    assert salida.startswith("La entrada no es válida: no se calcula.") and "ERR-06" in salida


def test_fichero_que_no_es_utf8_devuelve_2(tmp_path, capsys):
    ruta = tmp_path / "latin1.json"
    ruta.write_bytes('{"nombre": "Muñoz"}'.encode("latin-1"))
    assert main([str(ruta)]) == 2
    assert "UTF-8" in capsys.readouterr().err


# --- --json ------------------------------------------------------------------------------


def test_opcion_json_emite_el_informe(tmp_path, capsys):
    datos = V.leer_ejemplo_modelo()
    assert main(["--json", escribir(tmp_path, datos)]) == 1
    emitido = json.loads(capsys.readouterr().out)
    assert emitido == json.loads(json.dumps(como_dict(informe(cargar(json.dumps(datos))))))
    assert {"espana", "amlr", "comparacion", "diferencias"} <= set(emitido)


def test_opcion_json_con_un_solo_regimen(tmp_path, capsys):
    assert main(["--json", "--regimen", "espana", escribir(tmp_path, EJ3)]) == 1
    emitido = json.loads(capsys.readouterr().out)
    assert "espana" in emitido and "amlr" not in emitido and "comparacion" not in emitido
    assert emitido["espana"]["estado"] == "determinado"
    assert emitido["espana"]["inestable_por"] == ["POS-T"]


def test_opcion_json_con_entrada_no_valida(tmp_path, capsys):
    datos = json.loads(json.dumps(EJ3))
    del datos["entidad_objetivo"]
    assert main(["--json", escribir(tmp_path, datos)]) == 2
    emitido = json.loads(capsys.readouterr().out)
    assert emitido["valida"] is False and emitido["errores"][0]["codigo"] == "ERR-01"


# --- Punto de entrada --------------------------------------------------------------------


def test_punto_de_entrada_declarado():
    proyecto = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    assert proyecto["project"]["scripts"]["calcular-titularidad"] == "titularidad.cli:main"
