from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Avg, Sum, F
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import AntiqueItem, Category, CartItem, User, Order, OrderItem
from .forms import CartItemForm, OrderForm, LoginForm, RegistrationForm, AntiqueItemForm

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
        
            user = User(
                email=email,
                name=name,
                phone=phone,
                password=make_password(password)  # Хэшируем пароль
            )
            user.save()
            
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
    # [ТЗ 4.3] Поиск товаров на главной странице
    search_query = request.GET.get('search', '')  
    search_results = None
    search_count = 0
    
    # ВЫПОЛНЯЕМ ПОИСК, если есть запрос
    if search_query:
        search_results = AntiqueItem.objects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(era__icontains=search_query),
            stock__gt=0  # только товары в наличии
        ).order_by('-created_at')[:8]  # первые 8 результатов
        
        search_count = search_results.count()
    
    # [ТЗ 6.3] Сеансы - получаем недавно просмотренные товары
    viewed_ids = request.session.get('recently_viewed', [])
    recently_viewed = AntiqueItem.objects.filter(
        id__in=viewed_ids, 
        stock__gt=0
    )[:4]
    
    # [ТЗ 2.15] Функция агрегирования - статистика для главной страницы
    all_items = AntiqueItem.objects.all()
    stats = all_items.aggregate(
        total_count=Count('id'),
        avg_price=Avg('price'),
        total_stock=Sum('stock')
    )
    
    # Получаем заказы пользователя для главной страницы
    user_orders = []
    user_id = request.session.get('user_id')
    if user_id:
        user_orders = Order.objects.filter(
            user_id=user_id
        ).select_related('user').prefetch_related('items__antique_item').order_by('-created_at')[:3]
    
    context = {
        'recently_viewed': recently_viewed,
        'user_orders': user_orders,
        'is_authenticated': bool(user_id),
        'stats': stats,
        # Данные для поиска
        'search_query': search_query,
        'search_results': search_results,  # ← теперь здесь будут результаты поиска
        'search_count': search_count,
    }
    return render(request, 'core/home.html', context)




def logout_view(request):
    """Выход из аккаунта"""
    logout(request)
    return redirect('core:home')



def catalog_view(request):
    items = AntiqueItem.objects.select_related('category').all()
    
    # [ТЗ 4.3] __icontains и __contains - поиск
    search_query = request.GET.get('search', '')
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(era__icontains=search_query)
        )
    
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
    
    in_stock = request.GET.get('in_stock', '')
    if in_stock:
        items = items.exclude(stock=0) 
    
    sort_by = request.GET.get('sort', '-created_at')  # по умолчанию новинки
    allowed_sorts = ['price', '-price', 'name', '-name', 'created_at', '-created_at']
    if sort_by in allowed_sorts:
        items = items.order_by(sort_by)
    
    # [ТЗ 2.15] Функция агрегирования

    stats = items.aggregate(
        total_count=Count('id'),           # количество товаров
        avg_price=Avg('price'),            # средняя цена
        total_stock=Sum('stock')           # всего на складе
    )
    
    # [ТЗ 4.5] values(), values_list() - для категорий в фильтре
    categories = Category.objects.values('id', 'name', 'slug').annotate(
        item_count=Count('items')
    ).order_by('name')
    
    paginator = Paginator(items, 8)  
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
    item = get_object_or_404(AntiqueItem, pk=pk)
    
    # [ТЗ 6.3] Сохраняем просмотренный товар в сессию
    viewed_ids = request.session.get('recently_viewed', [])
    
    if pk not in viewed_ids:
        viewed_ids.insert(0, pk)
    else:
        viewed_ids.remove(pk)
        viewed_ids.insert(0, pk)
    
    viewed_ids = viewed_ids[:5]  # храним только 5 последних
    request.session['recently_viewed'] = viewed_ids
    
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


def cart_view(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return render(request, 'core/cart.html', {'cart_items': [], 'total': 0, 'has_items': False})
    
    cart_items = CartItem.objects.filter(user_id=user_id).select_related('antique_item').prefetch_related('antique_item__category')
    
    # Вычисляем сумму без скидки
    subtotal = cart_items.aggregate(
        total=Sum(F('antique_item__price') * F('quantity'))
    )['total'] or 0
    
    # Проверяем количество завершенных заказов пользователя
    completed_orders_count = Order.objects.filter(
        user_id=user_id,
        status='delivered'  # только доставленные заказы
    ).count()
    
    # Определяем скидку (5% если 3+ заказа)
    discount_percent = 5 if completed_orders_count >= 3 else 0
    discount_amount = (subtotal * discount_percent) / 100
    total = subtotal - discount_amount
    
    # Информация для отображения
    orders_needed = max(0, 3 - completed_orders_count) if discount_percent == 0 else 0
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount_percent': discount_percent,
        'discount_amount': discount_amount,
        'total': total,
        'has_items': cart_items.exists(),
        'cart_count': cart_items.count(),
        'completed_orders_count': completed_orders_count,
        'orders_needed': orders_needed,
        'has_discount': discount_percent > 0,
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
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('core:login')
    
    cart_items = CartItem.objects.filter(user_id=user_id)
    
    if not cart_items.exists():
        return redirect('core:cart')
    
    # Вычисляем сумму без скидки
    subtotal = cart_items.aggregate(
        total=Sum(F('antique_item__price') * F('quantity'))
    )['total'] or 0
    
    # Проверяем количество завершенных заказов пользователя
    completed_orders_count = Order.objects.filter(
        user_id=user_id,
        status='delivered'
    ).count()
    
    # Определяем скидку
    discount_percent = 5 if completed_orders_count >= 3 else 0
    discount_amount = (subtotal * discount_percent) / 100
    total = subtotal - discount_amount
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Создаем заказ с итоговой суммой (уже со скидкой)
            order = Order(
                user_id=user_id,
                delivery_address=form.cleaned_data['delivery_address'],
                payment_method=form.cleaned_data['payment_method'],
                total_price=total,  # ← сохраняем сумму со скидкой
                status='processing'
            )
            order.save()
            
            # Создаем элементы заказа
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
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
        'subtotal': subtotal,
        'discount_percent': discount_percent,
        'discount_amount': discount_amount,
        'total': total,
        'form': form,
        'completed_orders_count': completed_orders_count,
        'has_discount': discount_percent > 0,
    }
    
    return render(request, 'core/checkout.html', context)

def order_success_view(request, order_id):
    """Страница успешного оформления заказа"""
    return render(request, 'core/order_success.html', {'order_id': order_id})


# Создание товара
def item_create_view(request):
    if request.method == 'POST':
        form = AntiqueItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            return redirect('core:item_detail', pk=item.id)
    else:
        form = AntiqueItemForm()
    
    return render(request, 'core/item_form.html', {
        'form': form,
        'title': 'Добавить товар'
    })


# Редактирование товара
def item_edit_view(request, pk):
    item = get_object_or_404(AntiqueItem, pk=pk)
    
    if request.method == 'POST':
        form = AntiqueItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('core:item_detail', pk=item.id)
    else:
        form = AntiqueItemForm(instance=item)
    
    return render(request, 'core/item_form.html', {
        'form': form,
        'title': 'Редактировать товар'
    })


# Удаление товара
def item_delete_view(request, pk):
    item = get_object_or_404(AntiqueItem, pk=pk)
    
    if request.method == 'POST':
        item.delete()
        return redirect('core:catalog')
    
    return render(request, 'core/item_confirm_delete.html', {'item': item})