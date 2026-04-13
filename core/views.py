from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Avg, Sum, F
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import AntiqueItem, Category, CartItem, User
from .forms import RegistrationForm, LoginForm, CartItemForm, OrderForm


# Регистрация
def register_view(request):
    if request.session.get('user_id'):
        return redirect('core:home')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data['name']
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            
            # Создаем нового пользователя вручную
            user = User(
                email=email,
                name=name,
                phone=phone,
                password=make_password(password)  # Хэшируем пароль
            )
            user.save()
            
            # Сохраняем ID пользователя в сессии
            request.session['user_id'] = user.id
            request.session['user_email'] = user.email
            request.session['user_name'] = user.name
            
            return redirect('core:home')
    else:
        form = RegistrationForm()
    
    return render(request, 'core/register.html', {'form': form})


# Вход
def login_view(request):
    if request.session.get('user_id'):
        return redirect('core:home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Ищем пользователя по email
            try:
                user = User.objects.get(email=email)
                # Проверяем пароль
                if check_password(password, user.password):
                    # Сохраняем пользователя в сессии
                    request.session['user_id'] = user.id
                    request.session['user_email'] = user.email
                    request.session['user_name'] = user.name
                    return redirect('core:home')
                else:
                    form.add_error(None, 'Неверный email или пароль')
            except User.DoesNotExist:
                form.add_error(None, 'Неверный email или пароль')
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})



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




def logout_view(request):
    """Выход из аккаунта"""
    logout(request)
    return redirect('core:home')



def catalog_view(request):
    # [ТЗ 2.6] filter() в view
    # [ТЗ 4.2] Chaining filters
    items = AntiqueItem.objects.select_related('category').all()
    
    # [ТЗ 4.3] __icontains и __contains - поиск
    search_query = request.GET.get('search', '')
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |  # регистронезависимый поиск
            Q(description__icontains=search_query) |
            Q(era__icontains=search_query)
        )
    
    # [ТЗ 2.7] Использование __ (два варианта)
    # Вариант 1: обращение к связанной таблице через __
    category_slug = request.GET.get('category', '')
    if category_slug:
        items = items.filter(category__slug=category_slug)  # __ для доступа к полю связанной модели
    
    # Вариант 2: фильтрация по цене (цена__gte, цена__lte)
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        items = items.filter(price__gte=min_price)  # __gte - больше или равно
    if max_price:
        items = items.filter(price__lte=max_price)  # __lte - меньше или равно
    
    # [ТЗ 2.8] Метод exclude() - исключаем товары с нулевым остатком (если нужно показать только в наличии)
    in_stock = request.GET.get('in_stock', '')
    if in_stock:
        items = items.exclude(stock=0)  # exclude исключает товары с stock=0
    
    # [ТЗ 2.9] Метод order_by()
    sort_by = request.GET.get('sort', '-created_at')  # по умолчанию новинки
    allowed_sorts = ['price', '-price', 'name', '-name', 'created_at', '-created_at']
    if sort_by in allowed_sorts:
        items = items.order_by(sort_by)
    
    # [ТЗ 2.15] Функция агрегирования
    from django.db.models import Count, Avg, Sum
    stats = items.aggregate(
        total_count=Count('id'),           # количество товаров
        avg_price=Avg('price'),            # средняя цена
        total_stock=Sum('stock')           # всего на складе
    )
    
    # [ТЗ 4.5] values(), values_list() - для категорий в фильтре
    categories = Category.objects.values('id', 'name', 'slug').annotate(
        item_count=Count('items')
    ).order_by('name')
    
    # [ТЗ 2.14] Пагинация + try, except
    paginator = Paginator(items, 12)  # 12 товаров на страницу
    page = request.GET.get('page', 1)
    
    try:
        page_items = paginator.page(page)
    except PageNotAnInteger:
        page_items = paginator.page(1)
    except EmptyPage:
        page_items = paginator.page(paginator.num_pages)
    
    # [ТЗ 4.6] count(), exists()
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(user=request.user).count()  # count()
        
        # Проверяем, есть ли товары в корзине (exists)
        has_items = CartItem.objects.filter(user=request.user).exists()  # exists()
    
    context = {
        'items': page_items,
        'categories': categories,
        'stats': stats,
        'search_query': search_query,
        'selected_category': category_slug,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock': in_stock,
        'sort_by': sort_by,
        'cart_count': cart_count,
    }
    
    return render(request, 'core/catalog.html', context)





def item_detail_view(request, pk):
    """Детальная страница товара"""
    from django.shortcuts import get_object_or_404
    from .models import AntiqueItem
    
    # [ТЗ 2.11] get_object_or_404
    item = get_object_or_404(AntiqueItem, pk=pk)
    
    # [ТЗ 4.6] count() - количество товаров в корзине
    cart_count = 0
    if request.session.get('user_id'):
        from .models import CartItem
        cart_count = CartItem.objects.filter(user_id=request.session.get('user_id')).count()
    
    context = {
        'item': item,
        'cart_count': cart_count,
    }
    
    return render(request, 'core/item_detail.html', context)


def add_to_cart(request, pk):
    """[ТЗ 4.10] Добавление товара в корзину с HttpResponseRedirect"""
    from django.shortcuts import get_object_or_404
    from .models import AntiqueItem, CartItem
    
    # [ТЗ 2.11] get_object_or_404
    item = get_object_or_404(AntiqueItem, pk=pk)
    
    user_id = request.session.get('user_id')
    if not user_id:
        # Если не авторизован - перенаправляем на вход
        return HttpResponseRedirect(reverse('core:login') + '?next=' + request.path)
    
    quantity = int(request.POST.get('quantity', 1))
    
    # [ТЗ 4.7] update() - обновляем количество если товар уже в корзине
    cart_item, created = CartItem.objects.get_or_create(
        user_id=user_id,
        antique_item=item,
        defaults={'quantity': quantity}
    )
    
    if not created:
        # Обновляем количество
        cart_item.quantity += quantity
        cart_item.save()
    
    # [ТЗ 4.10] HttpResponseRedirect
    return HttpResponseRedirect(reverse('core:item_detail', args=[item.id]))



# Корзина
def cart_view(request):
    """[ТЗ 4.6, 4.7, 3.9] Страница корзины"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return render(request, 'core/cart.html', {'cart_items': [], 'total': 0})
    
    # [ТЗ 3.9] prefetch_related() - оптимизация запросов
    cart_items = CartItem.objects.filter(user_id=user_id).select_related('antique_item').prefetch_related('antique_item__category')
    
    # [ТЗ 4.6] count() - количество товаров в корзине
    cart_count = cart_items.count()
    
    # [ТЗ 4.6] exists() - проверяем, есть ли товары
    has_items = cart_items.exists()
    
    # Вычисляем общую сумму с помощью агрегации
    total = cart_items.aggregate(
        total=Sum(F('antique_item__price') * F('quantity'))
    )['total'] or 0
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
        'has_items': has_items,
    }
    
    return render(request, 'core/cart.html', context)


# [ТЗ 4.7] Обновление количества товара
def update_cart_item(request, item_id):
    """Обновление количества товара в корзине"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('core:login')
    
    cart_item = get_object_or_404(CartItem, id=item_id, user_id=user_id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            # [ТЗ 4.7] update() - обновление
            CartItem.objects.filter(id=item_id).update(quantity=quantity)
        else:
            # [ТЗ 4.7] delete() - удаление
            cart_item.delete()
    
    return HttpResponseRedirect(reverse('core:cart'))


# [ТЗ 4.7] Удаление товара из корзины
def remove_cart_item(request, item_id):
    """Удаление товара из корзины"""
    user_id = request.session.get('user_id')
    
    if user_id:
        # [ТЗ 4.7] delete()
        CartItem.objects.filter(id=item_id, user_id=user_id).delete()
    
    return HttpResponseRedirect(reverse('core:cart'))


# Оформление заказа
def checkout_view(request):
    """[ТЗ 3.1, 3.4, 3.5, 3.6, 4.8, 4.9, 4.12] Оформление заказа"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('core:login')
    
    cart_items = CartItem.objects.filter(user_id=user_id)
    
    if not cart_items.exists():
        return redirect('core:cart')
    
    total = cart_items.aggregate(
        total=Sum(F('antique_item__price') * F('quantity'))
    )['total'] or 0
    
    if request.method == 'POST':
        # [ТЗ 4.9] form.is_valid() + cleaned_data
        form = OrderForm(request.POST)
        if form.is_valid():
            # [ТЗ 3.6] save(commit=True/False)
            order = form.save(commit=False)
            order.user_id = user_id
            order.total_price = total
            order.save()
            
            # [ТЗ 3.6] сохраняем позиции заказа с commit=True
            for cart_item in cart_items:
                order.items.create(
                    antique_item=cart_item.antique_item,
                    quantity=cart_item.quantity,
                    price_at_time=cart_item.antique_item.price
                )
            
            # Очищаем корзину
            cart_items.delete()
            
            return redirect('core:order_success', order_id=order.id)
    else:
        form = OrderForm()
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'form': form,
    }
    
    return render(request, 'core/checkout.html', context)


def order_success_view(request, order_id):
    """Страница успешного оформления заказа"""
    return render(request, 'core/order_success.html', {'order_id': order_id})