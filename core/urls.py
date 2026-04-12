from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'), 
    path('item/<int:pk>/', views.item_detail_view, name='item_detail'),  # детальная страница товара
]