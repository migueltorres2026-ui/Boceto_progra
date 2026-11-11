"""Validaciones reutilizables. Las funciones retornan valores normalizados."""
import re
from datetime import date
from decimal import Decimal, InvalidOperation


def texto(valor, nombre, limite=100, obligatorio=True):
    if not isinstance(valor, str):
        raise ValueError(f'{nombre}: ingresa texto.')
    valor = valor.strip()
    if (obligatorio and not valor) or len(valor) > limite:
        raise ValueError(f'{nombre}: entre {1 if obligatorio else 0} y {limite} caracteres.')
    return valor


def entero(valor, nombre, minimo=1):
    if type(valor) is not int or valor < minimo:
        raise ValueError(f'{nombre}: ingresa un entero mayor o igual a {minimo}.')
    return valor


def precio(valor):
    try:
        numero = Decimal(str(valor))
        if not numero.is_finite() or numero <= 0 or numero > Decimal('9999999999.99'):
            raise ValueError()
        if numero != numero.quantize(Decimal('0.01')):
            raise ValueError()
        return numero.quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        raise ValueError('Precio: positivo, con máximo dos decimales y hasta 9999999999.99.') from None


def correo(valor):
    valor = texto(valor, 'Correo', 150).lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', valor):
        raise ValueError('Correo inválido. Ejemplo: miguel@ejemplo.cl')
    return valor


def fechas(inicio, fin):
    if type(inicio) is not date or type(fin) is not date:
        raise ValueError('Las fechas deben ser objetos date.')
    if fin < inicio:
        raise ValueError('La fecha final no puede ser anterior a la inicial.')
