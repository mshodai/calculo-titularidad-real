"""Línea de órdenes: calcular-titularidad FICHERO [--json] [--regimen {espana,amlr}]."""

import argparse
import sys

from titularidad.carga import cargar_fichero
from titularidad.salida import AMLR, ESPANA, como_json, incompleto_por, inestable_por, informe, regimenes, texto

REGIMENES = {"espana": ESPANA, "amlr": AMLR}
DETERMINADO = "determinado"


class _Formato(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, prefix or "uso: ")


def main(argv=None) -> int:
    """Devuelve 0 si los regímenes calculados quedan «determinados», son
    estables (C32) y completos (C33) y, si son los dos, coinciden en quién es
    titular real; 1 si no; 2 si la entrada no se puede leer o no es válida."""
    parser = argparse.ArgumentParser(
        prog="calcular-titularidad",
        description=(
            "Calcula la titularidad real de una entidad según la Ley 10/2010 y el AMLR, y compara "
            "los dos regímenes. Es un cálculo bajo las lecturas que declara la especificación, no "
            "una determinación jurídica."
        ),
        epilog=(
            "códigos de salida: 0 si los regímenes quedan «determinados», el resultado es estable y "
            "completo, y coinciden en quién es titular real; 1 si difieren, si alguno queda en otro "
            "estado (supletorio, sin titular identificado, no determinable, exceptuada, fuera de "
            "alcance), si el resultado no es estable (cambiaría con otra lectura, por ejemplo con un "
            "valor justo al otro lado de un umbral, o una comprobación no se ha podido hacer: C32) o "
            "si no es completo (lo que no está identificado podría cambiar quién es titular: C33); 2 "
            "si la entrada no se puede leer o no es válida."
        ),
        formatter_class=_Formato,
        add_help=False,
    )
    argumentos = parser.add_argument_group("argumentos")
    argumentos.add_argument("fichero", help="fichero JSON con la estructura de propiedad (docs/modelo-datos.md)")
    opciones = parser.add_argument_group("opciones")
    opciones.add_argument("-h", "--help", action="help", help="muestra esta ayuda y termina")
    opciones.add_argument("--json", action="store_true", help="emite el informe en JSON en lugar de texto")
    opciones.add_argument(
        "--regimen",
        choices=sorted(REGIMENES),
        help="calcula un solo régimen, sin la comparación; por defecto, los dos",
    )
    args = parser.parse_args(argv)

    try:
        carga = cargar_fichero(args.fichero)
    except FileNotFoundError:
        return _error(parser, f"no existe el fichero {args.fichero}")
    except UnicodeDecodeError:
        return _error(parser, f"el fichero {args.fichero} no está codificado en UTF-8")
    except OSError as e:
        return _error(parser, f"no se puede leer el fichero {args.fichero}: {e.strerror}")

    pedidos = (REGIMENES[args.regimen],) if args.regimen else (ESPANA, AMLR)
    inf = informe(carga, pedidos)
    print(como_json(inf) if args.json else texto(inf), end="\n" if args.json else "")
    return codigo_de_salida(inf)


def codigo_de_salida(inf) -> int:
    if inf.errores:
        return 2
    if any(r.estado != DETERMINADO or inestable_por(r) or incompleto_por(r) for _, r in regimenes(inf)):
        return 1
    if any(f.difiere for f in inf.filas):
        return 1
    return 0


def _error(parser, mensaje):
    print(f"{parser.prog}: error: {mensaje}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
