from django import template

register = template.Library()

def get_value( valor ):
    if valor: return valor
    return '---'

register.filter('get_value', get_value)