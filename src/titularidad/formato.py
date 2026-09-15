"""Cómo se muestran los valores exactos en los mensajes (C6: solo se redondea al mostrar)."""

from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction


def porcentaje(valor) -> str:
    """El valor exacto redondeado a 2 decimales, con coma decimal."""
    valor = Fraction(valor)
    with localcontext() as contexto:
        contexto.prec = 50
        decimal = Decimal(valor.numerator) / Decimal(valor.denominator)
    return f"{decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}".replace(".", ",")


def por_magnitud(valores: dict) -> str:
    """«capital 25,53 %, votos 29,03 %»."""
    return ", ".join(f"{m} {porcentaje(v)} %" for m, v in valores.items())
