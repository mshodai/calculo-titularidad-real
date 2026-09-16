"""Genera el corpus de corpus/: estructuras sintéticas con su resultado esperado.

Uso, desde cualquier directorio: python corpus/generar.py

Cada caso es una entrada según docs/modelo-datos.md y un resultado esperado,
escrito a mano aquí a partir de la especificación, no copiado del cálculo.
Antes de escribir nada, el script calcula cada caso con el código de src/ y
lo compara con lo esperado. Si alguno no coincide, termina con error y no
escribe ningún fichero.

Los datos son sintéticos y deterministas: cada ejecución produce exactamente
los mismos ficheros. Los nombres son letras y números («S», «P1», «H») y las
denominaciones dicen «ficticia»; no hay NIF ni ningún dato que recuerde a
una entidad real.

Por cada caso se escriben NN-nombre.json (la entrada) y
NN-nombre.esperado.json (qué demuestra y el resultado), y un README.md con la
lista.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

DIRECTORIO = Path(__file__).resolve().parent
# Usa siempre el código de src/, no una versión instalada del paquete.
sys.path.insert(0, str(DIRECTORIO.parent / "src"))

from titularidad.carga import cargar  # noqa: E402
from titularidad.cli import codigo_de_salida  # noqa: E402
from titularidad.salida import como_dict, informe  # noqa: E402

FECHA = "2027-07-10"  # ya aplicable el AMLR: sin el aviso AMLR-NO-APLICABLE
ADMINISTRADOR = {"persona": "ADM", "cargo": "miembro_organo_administracion", "ejecutivo": True}


# --- Construcción de las entradas ----------------------------------------------------------


def estructura(aristas, entidades=(), cotizadas=()):
    """Entrada con S como entidad objetivo y ADM como administrador ejecutivo.

    Cada arista es (id, titular, participada, capital, votos[, por_cuenta_de]).
    Son entidades S, las participadas y las de `entidades`; el resto, personas.
    Las `cotizadas` tienen cotización con requisitos de información.
    """
    son_entidad = {"S"} | set(entidades) | set(cotizadas) | {a[2] for a in aristas}
    nombres = son_entidad | {a[1] for a in aristas} | {a[5] for a in aristas if len(a) > 5} | {"ADM"}
    nodos = []
    for n in sorted(nombres, key=lambda n: (n not in son_entidad, n != "S", n)):
        if n in son_entidad:
            nodo = {"id": n, "tipo": "entidad_juridica", "denominacion": f"Sociedad ficticia {n}", "clase": "sociedad"}
            if n in cotizadas:
                nodo["cotizacion"] = {"mercado": "Mercado ficticio", "requisitos_informacion_ue_o_equivalentes": True}
            if n == "S":
                nodo["cargos"] = [ADMINISTRADOR]
        else:
            nodo = {"id": n, "tipo": "persona_fisica", "nombre": f"Persona ficticia {n}"}
        nodos.append(nodo)
    participaciones = []
    for a in aristas:
        arista = {"id": a[0], "titular": a[1], "participada": a[2], "capital": a[3], "votos": a[4]}
        if len(a) > 5:
            arista["por_cuenta_de"] = a[5]
        participaciones.append(arista)
    return {"version_modelo": "0.1", "fecha_referencia": FECHA, "entidad_objetivo": "S",
            "nodos": nodos, "participaciones": participaciones}


# --- Resultado esperado --------------------------------------------------------------------


def m(capital, votos=None):
    """Valores exactos por magnitud, como texto."""
    return {"capital": str(capital), "votos": str(capital if votos is None else votos)}


def es(pruebas, e1, e2, controla=False, por_cuenta_de=()):
    """Titular en España: pruebas, E1 (L1) por magnitud, E2 (L2) y si controla S."""
    return {"pruebas": list(pruebas), "E1": e1, "E2": None if e2 is None else str(e2), "controla": controla,
            "por_cuenta_de": list(por_cuenta_de)}


def am(pruebas, a1=None, a2=False, a3=None, a4=None, por_cuenta_de=()):
    """Titular en el AMLR: pruebas y valores de A1, A2, A3 y A4."""
    return {"pruebas": list(pruebas), "A1": a1 or {}, "A2": a2, "A3": a3 or {}, "A4": a4 or {},
            "por_cuenta_de": list(por_cuenta_de)}


def regimen(estado="determinado", titulares=None, posibles=None, avisos=(), estable=True, completo=True,
            supletorio=()):
    return {"estado": estado, "titulares": titulares or {}, "posibles": posibles or {}, "avisos": sorted(avisos),
            "estable": estable, "completo": completo, "supletorio": list(supletorio)}


def resumen(inf):
    """Lo que se compara de cada caso: el resultado de los dos regímenes, sin los mensajes."""
    datos = como_dict(inf)
    resultado = {"codigo_salida": codigo_de_salida(inf),
                 "avisos_entrada": sorted(a["codigo"] for a in datos["avisos_entrada"])}
    for clave in ("espana", "amlr"):
        r = datos[clave]
        titulares = {}
        for t in r["titulares"]:
            aristas = sorted({a["arista"] for a in t["por_cuenta_de"]})
            if clave == "espana":
                titulares[t["persona"]] = es(t["pruebas"], {k: v["exacto"] for k, v in t["E1"].items()},
                                             t["E2"] and t["E2"]["exacto"], t["controla"], aristas)
            else:
                titulares[t["persona"]] = am(
                    t["pruebas"], {k: v["exacto"] for k, v in t["A1"].items()}, t["A2"],
                    {k: v["exacto"] for k, v in t["A3"].items()},
                    {e: {k: v["exacto"] for k, v in vs.items()} for e, vs in t["A4"].items()}, aristas)
        posibles = {}
        for p in r["posibles"]:
            for persona in p["ids"]:
                posibles.setdefault(persona, []).append(p["codigo"])
        resultado[clave] = regimen(
            r["estado"], titulares, {p: sorted(c) for p, c in posibles.items()}, [a["codigo"] for a in r["avisos"]],
            r["estable"], r["completo"], r.get("administradores") or r.get("cargos_direccion") or ())
    resultado["difieren"] = [f["persona"] for f in datos["comparacion"] if f["difiere"]]
    return resultado


# --- Los casos -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Caso:
    nombre: str
    demuestra: str
    entrada: dict
    esperado: dict


# X tiene el 30 % de S. El 60 % de X no está identificado y Q1 a Q4 tienen un 10 % cada uno.
HUECO_QUE_CONTROLA = [(f"q{i}", f"Q{i}", "X", 10, 10) for i in range(1, 5)] + [("a1", "X", "S", 30, 30)]
# X tiene el 30 % de S. El 30 % de X no está identificado; Q1 tiene el 30 %, Q2 y Q3 el 15 % y Q4 el 10 %.
SOCIO_QUE_CONTROLARIA = [("q1", "Q1", "X", 30, 30), ("q2", "Q2", "X", 15, 15), ("q3", "Q3", "X", 15, 15),
                         ("q4", "Q4", "X", 10, 10), ("a1", "X", "S", 30, 30)]

CASOS = [
    Caso(
        "01-cuatro-socios-al-25",
        "Umbral: el AMLR pide «25 % o más» y España «superior al 25». Con cuatro socios al 25 % justo, los "
        "cuatro son titulares en el AMLR y en España se aplica el supuesto supletorio del administrador. El "
        "25 % justo hace el resultado inestable en los dos (UMBRAL-EXACTO, C28).",
        estructura([(f"a{i}", f"P{i}", "S", 25, 25) for i in range(1, 5)]),
        {
            "codigo_salida": 1, "avisos_entrada": [],
            "espana": regimen("supletorio (condicional)", avisos=["UMBRAL-EXACTO"], estable=False,
                              supletorio=["ADM"]),
            "amlr": regimen(titulares={f"P{i}": am(["A1"], m(25)) for i in range(1, 5)}, avisos=["UMBRAL-EXACTO"],
                            estable=False),
            "difieren": ["P1", "P2", "P3", "P4"],
        },
    ),
    Caso(
        "02-art54a-control-arriba",
        "Art. 54.a: P controla H (60 %), que tiene el 30 % de S. En el AMLR se le atribuye entero (A3); en "
        "España, por la agregación de votos del art. 42 (E2). Por multiplicación solo llega al 18 %. Los dos "
        "regímenes coinciden y el resultado es estable y completo: código 0.",
        estructura([("a1", "H", "S", 30, 30), ("a2", "X", "S", 70, 70), ("a3", "P", "H", 60, 60),
                    ("a4", "Q", "H", 40, 40)]),
        {
            "codigo_salida": 0, "avisos_entrada": [],
            "espana": regimen(titulares={"P": es(["E2"], m(18), 30), "X": es(["E1", "E2"], m(70), 70, True)}),
            "amlr": regimen(titulares={"P": am(["A3"], a3=m(30)), "X": am(["A1", "A2"], m(70), True)}),
            "difieren": [],
        },
    ),
    Caso(
        "03-art54b-participacion-arriba",
        "Art. 54.b: C controla S (60 %) y P tiene el 30 % de C. En el AMLR, P es titular (A4). En España no: "
        "L1 da el 18 % y L2 nada, porque P no domina C. Solo queda como posible con la lectura extensiva "
        "(POS-T, N1/N2), que hace inestable el resultado español.",
        estructura([("a1", "C", "S", 60, 60), ("a2", "R", "S", 40, 40), ("a3", "P", "C", 30, 30),
                    ("a4", "Q", "C", 70, 70)]),
        {
            "codigo_salida": 1, "avisos_entrada": [],
            "espana": regimen(titulares={"Q": es(["E1", "E2"], m(42), 60, True), "R": es(["E1", "E2"], m(40), 40)},
                              posibles={"P": ["POS-T"]}, estable=False),
            "amlr": regimen(titulares={
                "P": am(["A4"], a4={"C": m(30)}),
                "Q": am(["A1", "A2", "A3", "A4"], m(42), True, m(60), {"C": m(70)}),
                "R": am(["A1"], m(40)),
            }),
            "difieren": ["P"],
        },
    ),
    Caso(
        "04-ciclo-cambia-el-resultado",
        "Ciclo: S tiene el 40 % de H y H el 20 % de S. P tiene el 24 % directo. Con la serie completa (método "
        "B) llega a 24 / 0,92 = 26,09 % y es titular en los dos regímenes; con las cadenas simples (método A) "
        "se queda en el 24 % y no lo sería. CICLO-SENS (N7) en los dos.",
        estructura([("a1", "P", "S", 24, 24), ("a2", "H", "S", 20, 20), ("a3", "Q", "S", 56, 56),
                    ("a4", "S", "H", 40, 40), ("a5", "R", "H", 60, 60)]),
        {
            "codigo_salida": 1, "avisos_entrada": ["AVI-01"],
            "espana": regimen(titulares={"P": es(["E1"], m("600/23"), 24),
                                         "Q": es(["E1", "E2"], m("1400/23"), 56, True)},
                              avisos=["CICLO-SENS"], estable=False),
            "amlr": regimen(titulares={"P": am(["A1"], m("600/23")), "Q": am(["A1", "A2"], m("1400/23"), True)},
                            avisos=["CICLO-SENS"], estable=False),
            "difieren": [],
        },
    ),
    Caso(
        "05-cotizada-con-filial",
        "RD 9.4: S es filial participada mayoritariamente de la cotizada L (60 % del capital), así que en "
        "España está exceptuada (C30). En el AMLR la cotización no cambia el cálculo: P es titular (A1) y lo "
        "que llega a través de L no está identificado (H1, H3), así que el resultado no es completo.",
        estructura([("a1", "L", "S", 60, 60), ("a2", "P", "S", 40, 40)], cotizadas=["L"]),
        {
            "codigo_salida": 1, "avisos_entrada": ["AVI-02", "AVI-02", "AVI-03"],
            "espana": regimen("exceptuada"),
            "amlr": regimen(titulares={"P": am(["A1"], m(40))}, avisos=["H1", "H3"], completo=False),
            "difieren": ["P"],  # titular en el AMLR; en España no se calcula
        },
    ),
    Caso(
        "06-filial-intermedia-de-cotizada",
        "RD 9.4 en una intermedia (C30): X es filial de la cotizada L (51 %), pero no es la entidad objetivo, "
        "así que se recorren sus socios. P, con el 49 % de X, tiene el 34,3 % de S y es titular en los dos. "
        "Lo que llega por L va a COTIZADA(L) en España, y S sería filial de L con una cadena de mayorías "
        "directas (EXENCION-SENS, N14).",
        estructura([("a1", "L", "X", 51, 51), ("a2", "P", "X", 49, 49), ("a3", "X", "S", 70, 70),
                    ("a4", "R", "S", 30, 30)], cotizadas=["L"]),
        {
            "codigo_salida": 1, "avisos_entrada": ["AVI-02", "AVI-02", "AVI-03"],
            "espana": regimen(titulares={"P": es(["E1"], m("343/10"), 0), "R": es(["E1", "E2"], m(30), 30)},
                              avisos=["COTIZADA", "EXENCION-SENS"], estable=False),
            "amlr": regimen(titulares={"P": am(["A1", "A4"], m("343/10"), a4={"X": m(49)}), "R": am(["A1"], m(30))},
                            avisos=["H1", "H3"], completo=False),
            "difieren": [],
        },
    ),
    Caso(
        "07-testaferro",
        "Por cuenta de otro (C2): T figura con el 30 % de S por cuenta de Q, que no tiene nada más. Se "
        "atribuye a Q, que es titular en los dos regímenes con la marca «por cuenta de». Con la lectura "
        "contraria (N9 en el AMLR, N13 en España), T lo sería: POS-FORMAL.",
        estructura([("a1", "T", "S", 30, 30, "Q"), ("a2", "P", "S", 70, 70)]),
        {
            "codigo_salida": 1, "avisos_entrada": ["AVI-06"],
            "espana": regimen(titulares={"P": es(["E1", "E2"], m(70), 70, True),
                                         "Q": es(["E1", "E2"], m(30), 30, por_cuenta_de=["a1"])},
                              posibles={"T": ["POS-FORMAL"]}, estable=False),
            "amlr": regimen(titulares={"P": am(["A1", "A2"], m(70), True), "Q": am(["A1"], m(30), por_cuenta_de=["a1"])},
                            posibles={"T": ["POS-FORMAL"]}, estable=False),
            "difieren": [],
        },
    ),
    Caso(
        "08-hueco-que-controla",
        "H3 (C33): el 60 % de X no está identificado y X tiene el 30 % de S. A S llega un 18 % sin "
        "identificar, que no da H1, y ninguno de los socios conocidos de X llega al umbral multiplicando con el "
        "hueco (3 + 18). Pero quien tenga ese 60 % controla X y sería titular (A3; E2): H3. Q1 a Q4 también lo "
        "serían si el hueco fuera suyo (10 + 60): POS-HUECO (C34). El resultado es estable pero no completo.",
        estructura(HUECO_QUE_CONTROLA + [("a2", "R", "S", 70, 70)]),
        {
            "codigo_salida": 1, "avisos_entrada": ["AVI-02", "AVI-02"],
            "espana": regimen(titulares={"R": es(["E1", "E2"], m(70), 70, True)},
                              posibles={f"Q{i}": ["POS-HUECO"] for i in range(1, 5)}, avisos=["H2", "H3"],
                              completo=False),
            "amlr": regimen(titulares={"R": am(["A1", "A2"], m(70), True)},
                            posibles={f"Q{i}": ["POS-HUECO"] for i in range(1, 5)}, avisos=["H2", "H3"],
                            completo=False),
            "difieren": [],
        },
    ),
    Caso(
        "09-control-por-capital-y-por-votos",
        "N11: en A, P tiene el 60 % del capital y el 40 % de los votos, y Q al revés. En el AMLR los dos "
        "controlan A (53.2.c: capital o votos) y son titulares por A3. En España solo domina Q, porque el "
        "art. 42 solo mira los votos.",
        estructura([("a1", "A", "S", 30, 30), ("a2", "R", "S", 70, 70), ("a3", "P", "A", 60, 40),
                    ("a4", "Q", "A", 40, 60)]),
        {
            "codigo_salida": 1, "avisos_entrada": [],
            "espana": regimen(titulares={"Q": es(["E2"], m(12, 18), 30), "R": es(["E1", "E2"], m(70), 70, True)}),
            "amlr": regimen(titulares={"P": am(["A3"], a3=m(30)), "Q": am(["A3"], a3=m(30)),
                                       "R": am(["A1", "A2"], m(70), True)}),
            "difieren": ["P"],
        },
    ),
    Caso(
        "10-inestable",
        "Inestable pero completo (C32): P y Q tienen el 50 % justo de H, que tiene el 30 % de S. Con el 50 % "
        "nadie controla H y el único titular es R. Leído justo por encima del 50, P y Q controlarían H y "
        "serían titulares (UMBRAL-EXACTO). No falta ningún dato.",
        estructura([("a1", "P", "H", 50, 50), ("a2", "Q", "H", 50, 50), ("a3", "H", "S", 30, 30),
                    ("a4", "R", "S", 70, 70)]),
        {
            "codigo_salida": 1, "avisos_entrada": [],
            "espana": regimen(titulares={"R": es(["E1", "E2"], m(70), 70, True)}, avisos=["UMBRAL-EXACTO"],
                              estable=False),
            "amlr": regimen(titulares={"R": am(["A1", "A2"], m(70), True)}, avisos=["UMBRAL-EXACTO"], estable=False),
            "difieren": [],
        },
    ),
    Caso(
        "11-incompleto",
        "Incompleto pero estable (C33): solo está identificado el 60 % de S, que es de R. El 40 % que falta "
        "alcanza por sí solo el umbral (H1): puede haber otro titular. Ninguna otra lectura cambia el "
        "resultado. En España, ese 40 % cumpliría además E2 (H3).",
        estructura([("a1", "R", "S", 60, 60)]),
        {
            "codigo_salida": 1, "avisos_entrada": ["AVI-02", "AVI-02"],
            "espana": regimen(titulares={"R": es(["E1", "E2"], m(60), 60, True)}, avisos=["H1", "H3"], completo=False),
            "amlr": regimen(titulares={"R": am(["A1", "A2"], m(60), True)}, avisos=["H1"], completo=False),
            "difieren": [],
        },
    ),
    Caso(
        "12-socio-que-controlaria-con-el-hueco",
        "POS-HUECO por control (C34): X tiene el 30 % de S y el 30 % de X no está identificado. El hueco solo no "
        "controla X (sin H3), a S llega un 9 % sin identificar (sin H1) y Q1, con el 30 % de X, llega al 9 + 9 = "
        "18 % multiplicando. Pero si el hueco fuera de Q1, tendría el 60 % de X, la controlaría y sería titular "
        "(A3; E2). Q2, Q3 y Q4 se quedan en el 45 % o menos. Sin C34 el resultado saldría completo.",
        estructura(SOCIO_QUE_CONTROLARIA + [("a2", "R", "S", 70, 70)]),
        {
            "codigo_salida": 1, "avisos_entrada": ["AVI-02", "AVI-02"],
            "espana": regimen(titulares={"R": es(["E1", "E2"], m(70), 70, True)}, posibles={"Q1": ["POS-HUECO"]},
                              avisos=["H2"], completo=False),
            "amlr": regimen(titulares={"R": am(["A1", "A2"], m(70), True)}, posibles={"Q1": ["POS-HUECO"]},
                            avisos=["H2"], completo=False),
            "difieren": [],
        },
    ),
]


# --- Autoverificación y escritura --------------------------------------------------------------


def comprobar(caso):
    """Calcula el caso y devuelve las diferencias con lo esperado (vacío si coincide)."""
    carga = cargar(json.dumps(caso.entrada, ensure_ascii=False))
    if carga.errores:
        return [f"la entrada no es válida: {[e.codigo for e in carga.errores]}"]
    obtenido = resumen(informe(carga))
    return [f"{clave}: se esperaba {caso.esperado.get(clave)!r} y se obtuvo {obtenido.get(clave)!r}"
            for clave in sorted(set(obtenido) | set(caso.esperado))
            if obtenido.get(clave) != caso.esperado.get(clave)]


def ficheros(caso):
    """Los dos ficheros de un caso: nombre → contenido."""
    esperado = {"caso": caso.nombre, "demuestra": caso.demuestra, "resultado": caso.esperado}
    return {f"{caso.nombre}.json": _json(caso.entrada), f"{caso.nombre}.esperado.json": _json(esperado)}


def readme():
    lineas = [
        "# Corpus",
        "",
        "Estructuras sintéticas con su resultado esperado. Lo genera `corpus/generar.py`, que comprueba cada "
        "caso con el código de `src/` antes de escribirlo. No se edita a mano.",
        "",
        "```",
        "python corpus/generar.py",
        "```",
        "",
        "Cada caso tiene la entrada (`NN-nombre.json`, según `docs/modelo-datos.md`) y el resultado esperado "
        "(`NN-nombre.esperado.json`). El código de salida es el de `calcular-titularidad`: 0 si los dos "
        "regímenes quedan determinados, estables, completos y con los mismos titulares; 1 si no.",
        "",
        "| Caso | Qué demuestra | España | AMLR | Código |",
        "|---|---|---|---|---|",
    ]
    for caso in CASOS:
        r = caso.esperado
        fila = [caso.nombre, caso.demuestra, _celda(r["espana"]), _celda(r["amlr"]), str(r["codigo_salida"])]
        lineas.append("| " + " | ".join(fila) + " |")
    return "\n".join(lineas) + "\n"


def _celda(r):
    titulares = ", ".join(r["titulares"]) or "ninguno"
    return f"{r['estado']}: {titulares}"


def _json(datos):
    return json.dumps(datos, ensure_ascii=False, indent=2) + "\n"


def main():
    fallos = [(caso.nombre, diferencias) for caso in CASOS if (diferencias := comprobar(caso))]
    if fallos:
        for nombre, diferencias in fallos:
            print(f"{nombre}:", *diferencias, sep="\n  ", file=sys.stderr)
        sys.exit(f"{len(fallos)} caso(s) no dan el resultado esperado: no se escribe nada")
    for caso in CASOS:
        for nombre, contenido in ficheros(caso).items():
            (DIRECTORIO / nombre).write_text(contenido, encoding="utf-8", newline="\n")
        print(f"Escrito corpus/{caso.nombre}.json y .esperado.json")
    (DIRECTORIO / "README.md").write_text(readme(), encoding="utf-8", newline="\n")
    print("Escrito corpus/README.md")


if __name__ == "__main__":
    main()
