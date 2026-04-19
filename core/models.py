from django.db import models

from django.db import models
from django.utils import timezone # [ТЗ 2.2]
from django.urls import reverse

from .managers import AvailableItemManager

class User(models.Model):
    email = models.CharField(max_length=255, unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined'] # [ТЗ 2.3]

    def __str__(self):
        return self.email

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True) # Для красивых URL

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class AntiqueItem(models.Model):
    # [ТЗ 2.4] choices для состояния
    class ConditionChoices(models.TextChoices):
        EXCELLENT = 'excellent', 'Отличное'
        GOOD = 'good', 'Хорошее'
        RESTORED = 'restored', 'С реставрацией'

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items') # [ТЗ 2.5] related_name
    additional_categories = models.ManyToManyField(
        Category, 
        blank=True,
        related_name='additional_items',
        verbose_name='Дополнительные категории'
    )
    era = models.CharField(max_length=100, blank=True)
    condition = models.CharField(max_length=20, choices=ConditionChoices.choices, default=ConditionChoices.GOOD)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='items/', blank=True, null=True)
    certificate_pdf = models.FileField(upload_to='certificates/', blank=True, null=True)
    video_review_url = models.URLField(blank=True, null=True) # [ТЗ 5.3]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()
    available = AvailableItemManager()

    class Meta:
        verbose_name = 'Антикварный предмет'
        verbose_name_plural = 'Антикварные предметы'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:item_detail', args=[self.id])

    def save(self, *args, **kwargs):
        # Здесь можно добавить логику, например, проверку цены
        if self.price < 0:
            raise ValueError("Цена не может быть отрицательной")
        super().save(*args, **kwargs)



class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    antique_item = models.ForeignKey(AntiqueItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Предмет корзины'
        verbose_name_plural = 'Корзина'

    def __str__(self):
        return f"{self.user.email} - {self.antique_item.name}"

class Order(models.Model):
    class StatusChoices(models.TextChoices):
        PROCESSING = 'processing', 'В обработке'
        SHIPPED = 'shipped', 'Отправлен'
        DELIVERED = 'delivered', 'Доставлен'
        CANCELLED = 'cancelled', 'Отменён'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PROCESSING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.TextField()
    payment_method = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    items_m2m = models.ManyToManyField(
        'AntiqueItem', 
        through='OrderItem',
        through_fields=('order', 'antique_item'),
        related_name='orders_m2m'
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} {self.user.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    antique_item = models.ForeignKey(AntiqueItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f"{self.antique_item.name} (x{self.quantity}) in Order #{self.order.id}"
