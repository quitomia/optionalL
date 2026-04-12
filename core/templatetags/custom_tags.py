from django import template
from django.db.models import Sum, F
from ..models import AntiqueItem, CartItem

register = template.Library()

# [ТЗ 2.12] Шаблонный фильтр для форматирования цены
@register.filter
def currency(value):
    """Форматирует число как цену с символом рубля"""
    if value is None:
        return "0 ₽"
    try:
        return f"{float(value):,.0f} ₽".replace(",", " ")
    except (ValueError, TypeError):
        return f"{value} ₽"

# [ТЗ 2.17] Шаблонный тег с контекстными переменными (сумма корзины)
@register.simple_tag(takes_context=True)
def cart_total(context):
    """Возвращает общую сумму товаров в корзине текущего пользователя"""
    request = context.get('request')
    if request and request.user.is_authenticated:
        total = CartItem.objects.filter(user=request.user).aggregate(
            total=Sum(F('antique_item__price') * F('quantity'))
        )['total']
        return total or 0
    return 0

# [ТЗ 2.18] Шаблонный тег, возвращающий QuerySet (новинки)
@register.simple_tag
def get_new_items(limit=3):
    """Возвращает последние добавленные товары"""
    return AntiqueItem.objects.filter(stock__gt=0).order_by('-created_at')[:limit]

# [ТЗ 2.12] Еще один шаблонный фильтр (количество товаров в корзине)
@register.filter
def cart_count(user):
    """Возвращает количество товаров в корзине"""
    if user.is_authenticated:
        return CartItem.objects.filter(user=user).count()
    return 0