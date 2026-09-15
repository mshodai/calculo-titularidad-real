"""Verificación del límite de precisión de docs/modelo-datos.md, D23.

Con N acciones (o votos), la cantidad más próxima a un umbral por el lado que
importa está a una distancia que baja con N. Con porcentajes a 4 decimales,
redondeados al más próximo (D15), esa cantidad se registra como el propio
umbral cuando la distancia es menor que 0,00005.

Para cada caso se comprueba el primer N de su clase (paridad o resto entre 4)
que se registra como el umbral, y que el anterior de la misma clase no. Como
la distancia es c/N, a partir de ese N ya se registra siempre como el umbral.

Uso, desde la raíz del repositorio:

    python3 -m unittest discover -s verificacion -v
"""

import unittest
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal
from fractions import Fraction
from math import ceil, floor
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"


def registrado(acciones, total, redondeo=ROUND_HALF_UP):
    """Porcentaje con 4 decimales, como en la entrada (D4)."""
    return (Decimal(acciones) * 100 / Decimal(total)).quantize(Decimal("0.0001"), rounding=redondeo)


def mas_proxima(umbral, lado, total):
    """Acciones más próximas al umbral: la mínima por encima o la máxima por debajo."""
    exacto = Fraction(umbral, 100) * total
    return floor(exacto) + 1 if lado == "encima" else ceil(exacto) - 1


class LimiteDePrecision(unittest.TestCase):
    # (umbral, lado, clase de N, paso entre N de la clase, primer N que se registra como el umbral)
    CASOS = [
        (50, "encima", "impar", 2, 1_000_001),
        (50, "encima", "par", 2, 2_000_002),
        (25, "encima", "resto 3", 4, 500_003),
        (25, "encima", "resto 2", 4, 1_000_002),
        (25, "encima", "resto 1", 4, 1_500_001),
        (25, "encima", "resto 0", 4, 2_000_004),
        (25, "debajo", "resto 1", 4, 500_001),
        (25, "debajo", "resto 2", 4, 1_000_002),
        (25, "debajo", "resto 3", 4, 1_500_003),
        (25, "debajo", "resto 0", 4, 2_000_004),
    ]

    def test_primer_tamano_de_cada_clase(self):
        for umbral, lado, clase, paso, primero in self.CASOS:
            with self.subTest(umbral=umbral, lado=lado, clase=clase):
                objetivo = Decimal(umbral).quantize(Decimal("0.0001"))
                antes = primero - paso
                if antes != 2_000_000:  # empate: se comprueba aparte
                    self.assertNotEqual(registrado(mas_proxima(umbral, lado, antes), antes), objetivo)
                self.assertEqual(registrado(mas_proxima(umbral, lado, primero), primero), objetivo)

    def test_empate_en_dos_millones(self):
        """Con 2.000.000 la distancia es justo 0,00005: depende del redondeo del empate."""
        n = 2_000_000
        for umbral, lado in [(50, "encima"), (25, "encima"), (25, "debajo")]:
            with self.subTest(umbral=umbral, lado=lado):
                k = mas_proxima(umbral, lado, n)
                self.assertEqual(abs(Fraction(k * 100, n) - umbral), Fraction(5, 100000))
        self.assertNotEqual(registrado(1_000_001, n, ROUND_HALF_UP), registrado(1_000_001, n, ROUND_HALF_EVEN))

    def test_cifras_en_el_documento(self):
        texto = (DOCS / "modelo-datos.md").read_text(encoding="utf-8")
        for cifra in ["1.000.001", "2.000.002", "2.000.000", "500.001", "500.003", "50/N", "100/N", "25/N"]:
            self.assertIn(cifra, texto)


if __name__ == "__main__":
    unittest.main()
