from django.db import models
from django.utils import timezone
from django.urls import reverse
from .managers import AvailableItemManager

class User(models.Model):
    email = models.CharField(max_length=255, unique=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Телефон')
    name = models.CharField(max_length=100, verbose_name='Имя')
    password = models.CharField(max_length=255, verbose_name='Пароль')
    is_staff = models.BooleanField(default=False, verbose_name='Персонал')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Дата регистрации')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name

class AntiqueItem(models.Model):
    class ConditionChoices(models.TextChoices):
        EXCELLENT = 'excellent', 'Отличное'
        GOOD = 'good', 'Хорошее'
        RESTORED = 'restored', 'С реставрацией'

    name = models.TextField(verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='Категория'
    )
    additional_categories = models.ManyToManyField(
        Category, 
        blank=True,
        related_name='additional_items',
        verbose_name='Дополнительные категории'
    )
    era = models.CharField(max_length=100, blank=True, verbose_name='Эпоха')
    condition = models.CharField(
        max_length=20, 
        choices=ConditionChoices.choices, 
        default=ConditionChoices.GOOD,
        verbose_name='Состояние'
    )
    stock = models.PositiveIntegerField(default=0, verbose_name='Остаток')
    image = models.ImageField(upload_to='items/', blank=True, null=True, verbose_name='Изображение')
    certificate_pdf = models.FileField(
        upload_to='certificates/', 
        blank=True, 
        null=True,
        verbose_name='Сертификат (PDF)'
    )
    video_review_url = models.URLField(blank=True, null=True, verbose_name='Ссылка на видеообзор')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
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
        if self.price < 0:
            raise ValueError("Цена не может быть отрицательной")
        super().save(*args, **kwargs)
    def is_available(self):
        """Проверяет, доступен ли товар для заказа"""
        return self.stock > 0
    
    def decrease_stock(self, quantity):
        """Уменьшает остаток товара"""
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False
    
    def increase_stock(self, quantity):
        """Увеличивает остаток товара (при отмене заказа)"""
        self.stock += quantity
        self.save()

class CartItem(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='cart_items',
        verbose_name='Пользователь'
    )
    antique_item = models.ForeignKey(
        AntiqueItem, 
        on_delete=models.CASCADE,
        verbose_name='Антикварный предмет'
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

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

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='orders',
        verbose_name='Пользователь'
    )
    status = models.CharField(
        max_length=20, 
        choices=StatusChoices.choices, 
        default=StatusChoices.PROCESSING,
        verbose_name='Статус'
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Общая стоимость')
    delivery_address = models.TextField(verbose_name='Адрес доставки')
    payment_method = models.CharField(max_length=20, verbose_name='Способ оплаты')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
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
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='Заказ'
    )
    antique_item = models.ForeignKey(
        AntiqueItem, 
        on_delete=models.CASCADE,
        verbose_name='Антикварный предмет'
    )
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена на момент заказа')

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f"{self.antique_item.name} (x{self.quantity}) in Order #{self.order.id}"

class Auction(models.Model):
    """Модель аукциона (только информационная)"""
    class StatusChoices(models.TextChoices):
        UPCOMING = 'upcoming', 'Предстоящий'
        ACTIVE = 'active', 'Активный'
        COMPLETED = 'completed', 'Завершён'
        CANCELLED = 'cancelled', 'Отменён'
    
    title = models.CharField(max_length=200, verbose_name='Название аукциона')
    description = models.TextField(verbose_name='Описание')
    start_date = models.DateTimeField(verbose_name='Дата и время начала')
    end_date = models.DateTimeField(verbose_name='Дата и время окончания')
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.UPCOMING,
        verbose_name='Статус'
    )
    image = models.ImageField(
        upload_to='auctions/',
        blank=True,
        null=True,
        verbose_name='Изображение аукциона'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Аукцион'
        verbose_name_plural = 'Аукционы'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
    
    def is_active(self):
        """Проверяет, активен ли аукцион сейчас"""
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    def is_upcoming(self):
        """Проверяет, будет ли аукцион в будущем"""
        return timezone.now() < self.start_date
    
    def is_completed(self):
        """Проверяет, завершён ли аукцион"""
        return timezone.now() > self.end_date
    
    def get_dynamic_status(self):
        """Возвращает статус на основе текущего времени"""
        if self.status == self.StatusChoices.CANCELLED:
            return 'cancelled'
        if self.is_active():
            return 'active'
        if self.is_upcoming():
            return 'upcoming'
        if self.is_completed():
            return 'completed'
        return self.status


class AuctionLot(models.Model):
    """Лот в аукционе (связь аукциона с товаром)"""
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name='lots',
        verbose_name='Аукцион'
    )
    antique_item = models.ForeignKey(
        AntiqueItem,
        on_delete=models.CASCADE,
        related_name='auction_lots',
        verbose_name='Антикварный предмет'
    )
    starting_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Стартовая цена'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок отображения')
    
    class Meta:
        verbose_name = 'Лот аукциона'
        verbose_name_plural = 'Лоты аукционов'
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.auction.title} - {self.antique_item.name}"