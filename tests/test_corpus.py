"""El corpus de corpus/: cada caso da el resultado que documenta.

Se comprueba de tres formas: el resultado calculado coincide con el
.esperado.json de cada caso; la línea de órdenes devuelve el código de salida
esperado sobre el fichero real; y los ficheros son exactamente los que genera
corpus/generar.py, que además falla si una expectativa no se cumple.
"""

import importlib.util
import json
from pathlib import Path

import pytest

from titularidad.carga import cargar_fichero
from titularidad.cli import main as cli
from titularidad.salida import informe

CORPUS = Path(__file__).resolve().parent.parent / "corpus"


def _generador():
    spec = importlib.util.spec_from_file_location("corpus_generar", CORPUS / "generar.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


G = _generador()
ESPERADOS = sorted(CORPUS.glob("*.esperado.json"))


def test_estan_todos_los_casos():
    assert [p.name.removesuffix(".esperado.json") for p in ESPERADOS] == [c.nombre for c in G.CASOS]
    assert len(ESPERADOS) == 11


@pytest.mark.parametrize("esperado", ESPERADOS, ids=lambda p: p.name.removesuffix(".esperado.json"))
def test_cada_caso_da_su_resultado(esperado):
    datos = json.loads(esperado.read_text(encoding="utf-8"))
    entrada = CORPUS / f"{datos['caso']}.json"
    carga = cargar_fichero(entrada)
    assert carga.valida, carga.errores
    assert G.resumen(informe(carga)) == datos["resultado"]


@pytest.mark.parametrize("esperado", ESPERADOS, ids=lambda p: p.name.removesuffix(".esperado.json"))
def test_la_linea_de_ordenes_da_el_codigo_esperado(esperado, capsys):
    datos = json.loads(esperado.read_text(encoding="utf-8"))
    assert cli([str(CORPUS / f"{datos['caso']}.json")]) == datos["resultado"]["codigo_salida"]
    capsys.readouterr()


def test_los_ficheros_son_los_que_genera_el_script():
    """Reproducible: si alguien edita un fichero a mano o cambia generar.py sin regenerar, falla."""
    generados = {"README.md": G.readme()}
    for caso in G.CASOS:
        generados.update(G.ficheros(caso))
    en_disco = {p.name: p.read_text(encoding="utf-8") for p in CORPUS.iterdir() if p.suffix in (".json", ".md")}
    assert en_disco == generados


def test_el_script_falla_sin_escribir_si_una_expectativa_no_se_cumple(tmp_path, monkeypatch):
    caso = G.CASOS[1]
    mal = G.Caso(caso.nombre, caso.demuestra, caso.entrada, {**caso.esperado, "codigo_salida": 1})
    assert G.comprobar(mal) == ["codigo_salida: se esperaba 1 y se obtuvo 0"]
    monkeypatch.setattr(G, "DIRECTORIO", tmp_path)
    monkeypatch.setattr(G, "CASOS", [G.CASOS[0], mal])
    with pytest.raises(SystemExit):
        G.main()
    assert list(tmp_path.iterdir()) == []


def test_los_datos_son_sinteticos():
    """Solo nombres «ficticios», sin identificadores de entidades ni de personas."""
    for caso in G.CASOS:
        for nodo in caso.entrada["nodos"]:
            assert "ficticia" in (nodo.get("denominacion") or nodo.get("nombre"))
            assert not {"nif", "euid", "identificacion"} & set(nodo)
