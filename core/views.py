from django.shortcuts import render
from django.db.models import Count, Avg, Q
from .models import AntiqueItem, CartItem

def home_view(request):
    """
    Главная страница
    Демонстрирует: агрегирование (2.15), сеансы (6.3), шаблонные теги (2.17, 2.18)
    """
    
    # [ТЗ 2.15] Агрегирование - статистика по товарам
    stats = AntiqueItem.objects.aggregate(
        total_items=Count('id'),
        avg_price=Avg('price'),
        available_count=Count('id', filter=Q(stock__gt=0))
    )
    
    # [ТЗ 6.3] Сеансы - получаем недавно просмотренные товары
    viewed_ids = request.session.get('recently_viewed', [])
    recently_viewed = AntiqueItem.objects.filter(
        id__in=viewed_ids, 
        stock__gt=0
    )[:3]
    
    # [ТЗ 2.17] Данные для корзины (будет использован шаблонный тег)
    # Сама логика в custom_tags.py
    
    context = {
        'total_items': stats['total_items'],
        'avg_price': stats['avg_price'],
        'available_count': stats['available_count'],
        'recently_viewed': recently_viewed,
    }
    return render(request, 'core/home.html', context)


def item_detail_view(request, pk):
    """Детальная страница товара"""
    item = get_object_or_404(AntiqueItem, pk=pk)
    context = {
        'item': item,
    }
    return render(request, 'core/item_detail.html', context)