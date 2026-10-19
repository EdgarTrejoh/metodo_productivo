"""Cálculo mensual aprobado en D-04; no persiste entradas financieras."""

from decimal import Decimal, ROUND_CEILING, localcontext

from django import forms


MAX_AMOUNT = Decimal('999999999.99')


class BreakEvenForm(forms.Form):
    costs = forms.DecimalField(
        label='Costos fijos mensuales', min_value=Decimal('0'), max_value=MAX_AMOUNT,
        max_digits=11, decimal_places=2,
        error_messages={
            'required': 'Ingresa los costos fijos mensuales.',
            'invalid': 'Ingresa un importe numérico válido.',
            'min_value': 'Los costos fijos no pueden ser negativos.',
            'max_value': 'El importe máximo es $999,999,999.99.',
            'max_decimal_places': 'Usa como máximo dos decimales.',
            'max_digits': 'El importe máximo es $999,999,999.99.',
            'max_whole_digits': 'El importe máximo es $999,999,999.99.',
        },
        widget=forms.TextInput(attrs={'inputmode': 'decimal', 'autocomplete': 'off'}),
    )
    price = forms.DecimalField(
        label='Precio de venta unitario', min_value=Decimal('0.01'), max_value=MAX_AMOUNT,
        max_digits=11, decimal_places=2,
        error_messages={
            'required': 'Ingresa el precio de venta unitario.',
            'invalid': 'Ingresa un importe numérico válido.',
            'min_value': 'Se requiere un precio positivo, mínimo $0.01.',
            'max_value': 'El importe máximo es $999,999,999.99.',
            'max_decimal_places': 'Usa como máximo dos decimales.',
            'max_digits': 'El importe máximo es $999,999,999.99.',
            'max_whole_digits': 'El importe máximo es $999,999,999.99.',
        },
        widget=forms.TextInput(attrs={'inputmode': 'decimal', 'autocomplete': 'off'}),
    )
    variable_cost = forms.DecimalField(
        label='Costo variable unitario', min_value=Decimal('0'), max_value=MAX_AMOUNT,
        max_digits=11, decimal_places=2,
        error_messages={
            'required': 'Ingresa el costo variable unitario.',
            'invalid': 'Ingresa un importe numérico válido.',
            'min_value': 'El costo variable no puede ser negativo.',
            'max_value': 'El importe máximo es $999,999,999.99.',
            'max_decimal_places': 'Usa como máximo dos decimales.',
            'max_digits': 'El importe máximo es $999,999,999.99.',
            'max_whole_digits': 'El importe máximo es $999,999,999.99.',
        },
        widget=forms.TextInput(attrs={'inputmode': 'decimal', 'autocomplete': 'off'}),
    )


def calculate(cleaned_data):
    costs = cleaned_data['costs']
    price = cleaned_data['price']
    margin = price - cleaned_data['variable_cost']
    with localcontext() as ctx:
        ctx.prec = 32
        percentage = margin / price * 100
        units = int((costs / margin).to_integral_value(rounding=ROUND_CEILING)) if margin > 0 else None
    income = units * price if units is not None else None
    return {
        'state': 'positive' if margin > 0 else 'zero' if margin == 0 else 'negative',
        'state_label': 'Margen positivo' if margin > 0 else 'Margen cero' if margin == 0 else 'Margen negativo',
        'margin': f'-${-margin:,.2f}' if margin < 0 else f'${margin:,.2f}',
        'percentage': f'{percentage:,.1f} %',
        'units': f'{units:,}' if units is not None else 'No aplica',
        'income': f'${income:,.2f}' if income is not None else 'No aplica',
        'has_equilibrium': margin > 0,
        'explanation': (
            'No hay costos fijos mensuales que cubrir en este modelo.' if margin > 0 and costs == 0 else
            'Las unidades se redondean hacia arriba porque se consideran completas e indivisibles; el equilibrio teórico puede contener fracciones.' if margin > 0 else
            'Cada venta cubre solo su costo variable; no queda margen para cubrir costos fijos.' if margin == 0 else
            'Cada venta genera una contribución negativa; no existe un punto de equilibrio con ventas positivas bajo estos valores.'
        ),
        'large_result': units is not None and units > 1000000,
    }
