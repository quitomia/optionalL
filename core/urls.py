from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('catalog/', views.catalog_view, name='catalog'),
    path('item/<int:pk>/', views.item_detail_view, name='item_detail'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),    
    # Аутентификация
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success_view, name='order_success'),
    path('orders/', views.user_orders_view, name='user_orders'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),

    path('auctions/', views.auctions_list_view, name='auctions'),
    path('auctions/<int:pk>/', views.auction_detail_view, name='auction_detail'),
    path('profile/', views.profile_view, name='profile'),

    # CRUD для товаров
    path('items/create/', views.item_create_view, name='item_create'),
    path('items/<int:pk>/edit/', views.item_edit_view, name='item_edit'),
    path('items/<int:pk>/delete/', views.item_delete_view, name='item_delete'),
]
