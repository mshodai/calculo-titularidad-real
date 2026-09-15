"""El ejemplo completo de docs/modelo-datos.md, §10, leído del propio documento.

Tanto la entrada (el bloque JSON del §10) como el resultado esperado de la
validación (§10.2) salen del documento, así que si uno de los dos cambia sin
el otro, estos tests fallan.
"""

import re
from decimal import Decimal
from pathlib import Path

from titularidad.carga import cargar
from titularidad.modelo import EntidadJuridica, PersonaFisica

MODELO = Path(__file__).resolve().parent.parent / "docs" / "modelo-datos.md"


def _seccion(texto, titulo):
    """Texto desde el encabezado `titulo` hasta el siguiente de igual o mayor nivel."""
    nivel = titulo.split(" ")[0]
    inicio = texto.index(titulo)
    fin = re.search(rf"^#{{1,{len(nivel)}}} ", texto[inicio + len(titulo):], re.MULTILINE)
    return texto[inicio : inicio + len(titulo) + fin.start()] if fin else texto[inicio:]


TEXTO = MODELO.read_text(encoding="utf-8")
EJEMPLO = re.search(r"```json\n(.*?)\n```", _seccion(TEXTO, "## 10. Ejemplo completo"), re.DOTALL).group(1)
ESPERADO = _seccion(TEXTO, "### 10.2 Resultado esperado de la validación")
RESULTADO = cargar(EJEMPLO)


def test_sin_errores_como_dice_el_documento():
    assert "**Errores:** ninguno." in ESPERADO
    assert RESULTADO.errores == ()
    assert RESULTADO.valida


def test_los_avisos_son_los_del_documento():
    esperados = set(re.findall(r"AVI-\d\d", ESPERADO))
    assert esperados == {"AVI-01", "AVI-02", "AVI-03", "AVI-06"}
    assert {a.codigo for a in RESULTADO.avisos} == esperados


def test_detalle_de_los_avisos():
    por_codigo = {}
    for aviso in RESULTADO.avisos:
        por_codigo.setdefault(aviso.codigo, []).append(aviso)

    # AVI-01: ciclo E-OBJETIVO → E-BETA → E-HOLDING → E-OBJETIVO
    (ciclo,) = por_codigo["AVI-01"]
    assert set(ciclo.ids) == {"E-OBJETIVO", "E-BETA", "E-HOLDING"}

    # AVI-02 y AVI-03: E-FONDO no tiene titulares (0 %) y no cotiza
    assert [a.ids for a in por_codigo["AVI-02"]] == [("E-FONDO",), ("E-FONDO",)]
    assert all("quedan 100 sin identificar" in a.mensaje for a in por_codigo["AVI-02"])
    assert all(a.informativo_en == () for a in por_codigo["AVI-02"] + por_codigo["AVI-03"])
    assert [a.ids for a in por_codigo["AVI-03"]] == [("E-FONDO",)]

    # AVI-06: la arista p03 tiene por_cuenta_de
    assert [a.ids for a in por_codigo["AVI-06"]] == [("p03",)]


def test_estructura_leida():
    entrada = RESULTADO.entrada
    assert entrada.entidad_objetivo == "E-OBJETIVO"
    assert len(entrada.nodos) == 12
    assert len(entrada.participaciones) == 9
    assert isinstance(entrada.nodos["E-GESTORA"], EntidadJuridica)
    assert isinstance(entrada.nodos["P-ANA"], PersonaFisica)
    assert entrada.nodos["P-ANA"].identificacion.documento.numero == "00000000T"

    p03 = next(p for p in entrada.participaciones if p.id == "p03")
    assert (p03.titular, p03.por_cuenta_de) == ("P-BRUNO", "P-CARLOS")
    assert (p03.capital, p03.votos) == (Decimal(18), Decimal(20))

    objetivo = entrada.nodos["E-OBJETIVO"]
    gestora = next(c for c in objetivo.cargos if c.persona == "E-GESTORA")
    assert gestora.representante == "P-ELENA"


def test_las_sumas_del_documento():
    """§10.2: E-OBJETIVO suma 100 en capital y en votos."""
    entrada = RESULTADO.entrada
    for magnitud in ("capital", "votos"):
        suma = sum(
            getattr(p, magnitud) for p in entrada.participaciones if p.participada == "E-OBJETIVO"
        )
        assert suma == 100
