"""Validaciones del §6.2 de docs/modelo-datos.md, una a una.

Cada test parte de una entrada mínima válida (S, 100 % de P, P administrador)
y cambia solo lo necesario para provocar el error o el aviso.
"""

import json
from datetime import date
from decimal import Decimal

import pytest

from titularidad.carga import cargar, cargar_fichero
from titularidad.modelo import EntidadJuridica, PersonaFisica


def base():
    return {
        "version_modelo": "0.1",
        "fecha_referencia": "2026-09-15",
        "entidad_objetivo": "S",
        "nodos": [
            {
                "id": "S",
                "tipo": "entidad_juridica",
                "denominacion": "S, S.L.",
                "clase": "sociedad",
                "cargos": [{"persona": "P", "cargo": "miembro_organo_administracion", "ejecutivo": True}],
            },
            {"id": "P", "tipo": "persona_fisica", "nombre": "P"},
        ],
        "participaciones": [
            {"id": "a1", "titular": "P", "participada": "S", "capital": 100, "votos": 100},
        ],
    }


def persona(id_):
    return {"id": id_, "tipo": "persona_fisica", "nombre": id_}


def entidad(id_, **campos):
    return {"id": id_, "tipo": "entidad_juridica", "denominacion": id_, "clase": "sociedad", **campos}


def arista(id_, titular, participada, capital, votos, **campos):
    return {
        "id": id_,
        "titular": titular,
        "participada": participada,
        "capital": capital,
        "votos": votos,
        **campos,
    }


def cargar_dict(datos):
    return cargar(json.dumps(datos, ensure_ascii=False))


def codigos(incidencias):
    return [i.codigo for i in incidencias]


# --- Entrada válida ------------------------------------------------------------


def test_entrada_minima_valida():
    resultado = cargar_dict(base())
    assert resultado.valida
    assert resultado.errores == ()
    assert resultado.avisos == ()
    entrada = resultado.entrada
    assert entrada.fecha_referencia == date(2026, 9, 15)
    assert isinstance(entrada.nodos["S"], EntidadJuridica)
    assert isinstance(entrada.nodos["P"], PersonaFisica)
    assert entrada.nodos["S"].cargos[0].ejecutivo is True


def test_porcentajes_como_decimal_exacto():
    """D4: 16,6667 se lee como decimal exacto, no como float."""
    datos = base()
    datos["nodos"] += [persona(f"Q{i}") for i in range(6)]
    datos["participaciones"] = [arista(f"a{i}", f"Q{i}", "S", 16.6667, 16.6667) for i in range(6)]
    datos["nodos"][0]["cargos"][0]["persona"] = "Q0"
    datos["nodos"].remove(persona("P"))
    resultado = cargar_dict(datos)
    assert resultado.valida, resultado.errores
    valores = [p.capital for p in resultado.entrada.participaciones]
    assert all(type(v) is Decimal for v in valores)
    assert valores[0] == Decimal("16.6667")
    assert sum(valores) == Decimal("100.0002")


def test_cargar_fichero(tmp_path):
    ruta = tmp_path / "entrada.json"
    ruta.write_text(json.dumps(base()), encoding="utf-8")
    assert cargar_fichero(ruta).valida


# --- ERR-01: estructura, tipos y campos desconocidos ---------------------------


def test_err01_json_mal_formado():
    resultado = cargar("{no es json")
    assert codigos(resultado.errores) == ["ERR-01"]
    assert resultado.entrada is None


@pytest.mark.parametrize("texto", ["NaN", "Infinity", "-Infinity"])
def test_err01_constantes_no_numericas(texto):
    datos = json.dumps(base()).replace('"capital": 100', f'"capital": {texto}')
    assert "ERR-01" in codigos(cargar(datos).errores)


def test_err01_clave_repetida():
    datos = json.dumps(base()).replace('"capital": 100', '"capital": 100, "capital": 50')
    assert codigos(cargar(datos).errores) == ["ERR-01"]


def test_err01_campo_desconocido():
    """D20: una errata en un campo opcional no pasa inadvertida."""
    datos = base()
    datos["participaciones"][0]["por_cuenta"] = "P"
    resultado = cargar_dict(datos)
    assert codigos(resultado.errores) == ["ERR-01"]
    assert "por_cuenta" in resultado.errores[0].mensaje


def test_err01_campo_desconocido_en_objeto_anidado():
    datos = base()
    datos["nodos"][0]["cargos"][0]["ejecutiva"] = True
    assert codigos(cargar_dict(datos).errores) == ["ERR-01"]


def test_err01_falta_una_magnitud():
    """D5: las dos claves son obligatorias, aunque sea con null."""
    datos = base()
    del datos["participaciones"][0]["votos"]
    assert codigos(cargar_dict(datos).errores) == ["ERR-01"]


@pytest.mark.parametrize("valor", ["25", True])
def test_err01_porcentaje_de_otro_tipo(valor):
    datos = base()
    datos["participaciones"][0]["capital"] = valor
    assert "ERR-01" in codigos(cargar_dict(datos).errores)


def test_err01_version_distinta():
    datos = base()
    datos["version_modelo"] = "0.2"
    assert codigos(cargar_dict(datos).errores) == ["ERR-01"]


@pytest.mark.parametrize("fecha", ["2026-02-30", "20260915", "15/09/2026"])
def test_err01_fecha_no_valida(fecha):
    datos = base()
    datos["fecha_referencia"] = fecha
    assert codigos(cargar_dict(datos).errores) == ["ERR-01"]


def test_err01_valor_de_enumeracion():
    datos = base()
    datos["nodos"][0]["clase"] = "cooperativa"
    assert codigos(cargar_dict(datos).errores) == ["ERR-01"]


def test_err01_null_en_campo_opcional():
    """Solo capital, votos y por_cuenta_de admiten null; los demás se omiten."""
    datos = base()
    datos["participaciones"][0]["desde"] = None
    assert codigos(cargar_dict(datos).errores) == ["ERR-01"]


def test_por_cuenta_de_null_es_valido():
    datos = base()
    datos["participaciones"][0]["por_cuenta_de"] = None
    assert cargar_dict(datos).valida


# --- ERR-02 a ERR-05: identificadores y referencias ----------------------------


def test_err02_id_de_nodo_repetido():
    datos = base()
    datos["nodos"].append(persona("P"))
    assert codigos(cargar_dict(datos).errores) == ["ERR-02"]


def test_err02_id_de_arista_repetido():
    datos = base()
    datos["participaciones"][0]["capital"] = 50
    datos["nodos"].append(persona("Q"))
    datos["participaciones"].append(arista("a1", "Q", "S", 50, 0))
    assert codigos(cargar_dict(datos).errores) == ["ERR-02"]


def test_err03_objetivo_inexistente():
    datos = base()
    datos["entidad_objetivo"] = "X"
    assert "ERR-03" in codigos(cargar_dict(datos).errores)


def test_err03_objetivo_persona_fisica():
    datos = base()
    datos["entidad_objetivo"] = "P"
    assert codigos(cargar_dict(datos).errores) == ["ERR-03"]


@pytest.mark.parametrize("campo", ["titular", "participada", "por_cuenta_de"])
def test_err04_arista_apunta_a_nodo_inexistente(campo):
    datos = base()
    datos["participaciones"][0][campo] = "X"
    assert "ERR-04" in codigos(cargar_dict(datos).errores)


def test_err04_cargo_apunta_a_nodo_inexistente():
    datos = base()
    datos["nodos"][0]["cargos"][0]["persona"] = "X"
    assert codigos(cargar_dict(datos).errores) == ["ERR-04"]


def test_err05_participada_persona_fisica():
    datos = base()
    datos["nodos"].append(persona("Q"))
    datos["participaciones"].append(arista("a2", "Q", "P", 10, 10))
    assert "ERR-05" in codigos(cargar_dict(datos).errores)


# --- ERR-06 y ERR-07: porcentajes ----------------------------------------------


@pytest.mark.parametrize("valor", ["100.0001", "-0.0001", "25.00001", "1e3"])
def test_err06_porcentaje_fuera_de_rango_o_con_mas_de_4_decimales(valor):
    datos = json.dumps(base()).replace('"capital": 100', f'"capital": {valor}')
    assert codigos(cargar(datos).errores) == ["ERR-06"]


def test_err06_cuenta_los_decimales_del_valor():
    """25.00000 vale exactamente 25: los ceros finales no cuentan."""
    datos = json.dumps(base()).replace('"capital": 100', '"capital": 100.00000')
    assert cargar(datos).valida


def test_err06_no_se_deja_redondear_por_el_contexto_decimal():
    """Un valor con 30 decimales no se da por bueno al redondearlo a 28 dígitos."""
    valor = "99.999999999999999999999999999999"
    datos = json.dumps(base()).replace('"capital": 100', f'"capital": {valor}')
    assert codigos(cargar(datos).errores) == ["ERR-06"]


def test_err07_capital_y_votos_null():
    datos = base()
    datos["participaciones"][0].update(capital=None, votos=None)
    assert codigos(cargar_dict(datos).errores) == ["ERR-07"]


def test_avi04_una_magnitud_null():
    datos = base()
    datos["participaciones"][0]["votos"] = None
    resultado = cargar_dict(datos)
    assert resultado.valida
    assert "AVI-04" in codigos(resultado.avisos)


# --- ERR-08: aristas duplicadas ------------------------------------------------


def test_err08_misma_combinacion_titular_participada():
    datos = base()
    datos["participaciones"][0].update(capital=50, votos=50)
    datos["participaciones"].append(arista("a2", "P", "S", 50, 50))
    assert codigos(cargar_dict(datos).errores) == ["ERR-08"]


def test_err08_admite_la_misma_pareja_con_otro_por_cuenta_de():
    """D14: la combinación incluye por_cuenta_de (propia y como testaferro)."""
    datos = base()
    datos["nodos"].append(persona("Q"))
    datos["participaciones"][0].update(capital=50, votos=50)
    datos["participaciones"].append(arista("a2", "P", "S", 50, 50, por_cuenta_de="Q"))
    assert cargar_dict(datos).valida


# --- ERR-09 y ERR-10: sumas por encima del 100 % (D15) -------------------------


def _socios(valores, magnitud):
    """JSON de S con un socio por valor en `magnitud`; la otra, null.

    Los valores se escriben tal cual en el texto, para que no pasen por float.
    """
    datos = base()
    datos["nodos"] = [datos["nodos"][0]] + [persona(f"Q{i}") for i in range(len(valores))]
    datos["nodos"][0]["cargos"][0]["persona"] = "Q0"
    otra = "votos" if magnitud == "capital" else "capital"
    datos["participaciones"] = [
        arista(f"a{i}", f"Q{i}", "S", **{magnitud: f"__v{i}__", otra: None}) for i in range(len(valores))
    ]
    texto = json.dumps(datos)
    for i, valor in enumerate(valores):
        texto = texto.replace(f'"__v{i}__"', valor)
    return texto


@pytest.mark.parametrize(
    "valores, admitido",
    [
        (["50.0001", "50"], True),  # 2 aristas: hasta 100,0001
        (["50.0001", "50.0001"], False),
        (["33.3334", "33.3334", "33.3333"], True),  # 3 aristas: hasta 100,0001
        (["33.3334", "33.3334", "33.3334"], False),
        (["16.6667"] * 6, True),  # 6 aristas: hasta 100,0003
        (["16.6667"] * 5 + ["16.6669"], False),  # 100,0004
    ],
)
@pytest.mark.parametrize("magnitud, codigo", [("capital", "ERR-09"), ("votos", "ERR-10")])
def test_err09_err10_tolerancia_de_redondeo(valores, admitido, magnitud, codigo):
    errores = codigos(cargar(_socios(valores, magnitud)).errores)
    assert errores == ([] if admitido else [codigo])


# --- ERR-11 y ERR-12 -----------------------------------------------------------


def test_err11_por_cuenta_de_igual_a_titular():
    datos = base()
    datos["participaciones"][0]["por_cuenta_de"] = "P"
    assert codigos(cargar_dict(datos).errores) == ["ERR-11"]


def test_err11_por_cuenta_de_en_arista_reflexiva():
    datos = base()
    datos["participaciones"][0].update(capital=90, votos=90)
    datos["participaciones"].append(arista("a2", "S", "S", 10, 10, por_cuenta_de="P"))
    assert codigos(cargar_dict(datos).errores) == ["ERR-11"]


def test_err12_entidad_administradora_sin_representante():
    datos = base()
    datos["nodos"].append(entidad("G"))
    datos["nodos"][0]["cargos"][0]["persona"] = "G"
    assert codigos(cargar_dict(datos).errores) == ["ERR-12"]


def test_err12_representante_que_no_es_persona_fisica():
    datos = base()
    datos["nodos"] += [entidad("G"), entidad("H")]
    datos["nodos"][0]["cargos"][0].update(persona="G", representante="H")
    assert codigos(cargar_dict(datos).errores) == ["ERR-12"]


def test_entidad_administradora_con_representante():
    datos = base()
    datos["nodos"].append(entidad("G"))
    datos["nodos"][0]["cargos"][0].update(persona="G", representante="P")
    assert cargar_dict(datos).valida


# --- Avisos --------------------------------------------------------------------


def test_avi01_autocartera_es_un_ciclo():
    """D9: la arista reflexiva cuenta como ciclo."""
    datos = base()
    datos["participaciones"][0].update(capital=90, votos=90)
    datos["participaciones"].append(arista("a2", "S", "S", 10, 10))
    resultado = cargar_dict(datos)
    assert resultado.valida
    ciclos = [a for a in resultado.avisos if a.codigo == "AVI-01"]
    assert [a.ids for a in ciclos] == [("S",)]


def test_avi02_suma_por_debajo_de_100():
    datos = base()
    datos["participaciones"][0].update(capital=80, votos=100)
    resultado = cargar_dict(datos)
    assert codigos(resultado.avisos) == ["AVI-02"]
    assert "capital" in resultado.avisos[0].mensaje
    assert "quedan 20 sin identificar" in resultado.avisos[0].mensaje
    assert not resultado.avisos[0].informativo


def test_avi02_no_tiene_tolerancia_por_debajo():
    """Tres tercios redondeados hacia abajo suman 99,9999: hay aviso."""
    avisos = cargar(_socios(["33.3333"] * 3, "capital")).avisos
    assert "quedan 0.0001 sin identificar" in [a for a in avisos if a.codigo == "AVI-02"][0].mensaje


def test_avi02_informativo_si_la_entidad_cotiza():
    datos = base()
    datos["nodos"][0]["cotizacion"] = {"mercado": "XMAD", "requisitos_informacion_ue_o_equivalentes": True}
    datos["participaciones"][0].update(capital=30, votos=30)
    avisos = [a for a in cargar_dict(datos).avisos if a.codigo == "AVI-02"]
    assert len(avisos) == 2 and all(a.informativo for a in avisos)


def test_avi03_entidad_sin_titulares_en_la_cadena():
    datos = base()
    datos["nodos"].append(entidad("F"))
    datos["participaciones"][0].update(capital=80, votos=80)
    datos["participaciones"].append(arista("a2", "F", "S", 20, 20))
    resultado = cargar_dict(datos)
    assert [a.ids for a in resultado.avisos if a.codigo == "AVI-03"] == [("F",)]


def test_avi03_no_si_la_entidad_cotiza():
    datos = base()
    datos["nodos"].append(
        entidad("F", cotizacion={"mercado": "XMAD", "requisitos_informacion_ue_o_equivalentes": True})
    )
    datos["participaciones"][0].update(capital=80, votos=80)
    datos["participaciones"].append(arista("a2", "F", "S", 20, 20))
    assert "AVI-03" not in codigos(cargar_dict(datos).avisos)


def test_avi05_entidad_que_no_es_sociedad():
    datos = base()
    datos["nodos"].append({**entidad("F"), "clase": "fundacion"})
    datos["nodos"].append(persona("Q"))
    datos["participaciones"][0].update(capital=80, votos=80)
    datos["participaciones"] += [arista("a2", "F", "S", 20, 20), arista("a3", "Q", "F", 100, 100)]
    assert [a.ids for a in cargar_dict(datos).avisos if a.codigo == "AVI-05"] == [("F",)]


def test_avi06_participacion_por_cuenta_de_otro():
    datos = base()
    datos["nodos"].append(persona("Q"))
    datos["participaciones"][0]["por_cuenta_de"] = "Q"
    resultado = cargar_dict(datos)
    assert resultado.valida
    assert [a.ids for a in resultado.avisos if a.codigo == "AVI-06"] == [("a1",)]


def test_avi07_objetivo_sin_cargos():
    datos = base()
    del datos["nodos"][0]["cargos"]
    assert "AVI-07" in codigos(cargar_dict(datos).avisos)


def test_avi08_nodo_no_conectado():
    datos = base()
    datos["nodos"] += [entidad("X"), persona("Y")]
    datos["participaciones"].append(arista("a2", "Y", "X", 100, 100))
    resultado = cargar_dict(datos)
    assert resultado.valida
    assert sorted(a.ids for a in resultado.avisos if a.codigo == "AVI-08") == [("X",), ("Y",)]


def test_avi08_una_filial_del_objetivo_no_esta_en_la_cadena():
    """Solo conecta el camino hacia el objetivo (especificación, C1)."""
    datos = base()
    datos["nodos"].append(entidad("F"))
    datos["participaciones"].append(arista("a2", "S", "F", 100, 100))
    assert [a.ids for a in cargar_dict(datos).avisos if a.codigo == "AVI-08"] == [("F",)]


def test_avi08_el_principal_de_una_por_cuenta_de_esta_conectado():
    datos = base()
    datos["nodos"].append(persona("Q"))
    datos["participaciones"][0]["por_cuenta_de"] = "Q"
    assert "AVI-08" not in codigos(cargar_dict(datos).avisos)


def test_errores_en_nodos_no_conectados_rechazan_la_entrada():
    datos = base()
    datos["nodos"] += [entidad("X"), persona("Y"), persona("Z")]
    datos["participaciones"] += [arista("a2", "Y", "X", 60, 60), arista("a3", "Z", "X", 60, 60)]
    resultado = cargar_dict(datos)
    assert codigos(resultado.errores) == ["ERR-09", "ERR-10"]
    assert resultado.entrada is None
