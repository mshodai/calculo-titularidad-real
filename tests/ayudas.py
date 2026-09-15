"""Funciones auxiliares de los tests. No contiene tests."""

import importlib.util
import json
from pathlib import Path

from titularidad.carga import cargar

RAIZ = Path(__file__).resolve().parent.parent


def verificacion():
    """El módulo de verificación, cargado por ruta.

    No se importan sus nombres a este módulo, para que pytest no vuelva a
    recoger sus tests aquí.
    """
    ruta = RAIZ / "verificacion" / "test_cifras_ciclos.py"
    spec = importlib.util.spec_from_file_location("verificacion_cifras_ciclos", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def entrada(aristas, objetivo="S", entidades=(), clases=None):
    """Entrada validada a partir de (id, titular, participada, capital, votos[, por_cuenta_de]).

    Son entidades el objetivo, las participadas y las de `entidades`; el resto,
    personas. Pasa por `cargar`, así que la entrada es válida según el modelo.
    """
    clases = clases or {}
    nombres = {objetivo} | set(entidades)
    for a in aristas:
        nombres |= {a[1], a[2]} | ({a[5]} if len(a) > 5 else set())
    son_entidad = {objetivo} | set(entidades) | {a[2] for a in aristas}
    nodos = []
    for n in sorted(nombres):
        if n in son_entidad:
            nodos.append({"id": n, "tipo": "entidad_juridica", "denominacion": n, "clase": clases.get(n, "sociedad")})
        else:
            nodos.append({"id": n, "tipo": "persona_fisica", "nombre": n})
    participaciones = []
    for a in aristas:
        p = {"id": a[0], "titular": a[1], "participada": a[2], "capital": f"__{a[0]}c__", "votos": f"__{a[0]}v__"}
        if len(a) > 5:
            p["por_cuenta_de"] = a[5]
        participaciones.append(p)
    texto = json.dumps({
        "version_modelo": "0.1",
        "fecha_referencia": "2026-09-15",
        "entidad_objetivo": objetivo,
        "nodos": nodos,
        "participaciones": participaciones,
    })
    for a in aristas:  # los valores, tal cual, sin pasar por float
        texto = texto.replace(f'"__{a[0]}c__"', str(a[3])).replace(f'"__{a[0]}v__"', str(a[4]))
    resultado = cargar(texto)
    assert resultado.valida, resultado.errores
    return resultado.entrada
