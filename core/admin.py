from django.contrib import admin
from django.utils.html import format_html
from . import models

# [ТЗ 6.5] Inlines в админке
class CartItemInline(admin.TabularInline):
    model = models.CartItem
    extra = 0
    fields = ('antique_item', 'quantity')


class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    extra = 0
    readonly_fields = ('price_at_time',)  # [ТЗ 7.10] readonly_fields


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    # [ТЗ 7.1] list_display + собственный метод
    @admin.display(description='Полное имя')
    def get_full_name(self, obj):
        return obj.name  # В вашей модели поле называется 'name'
    
    list_display = ('email', 'get_full_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff',)  # [ТЗ 7.2] list_filter (у вас нет is_active)
    search_fields = ('email', 'name')  # [ТЗ 7.11] search_fields
    list_display_links = ('email',)  # [ТЗ 7.8] list_display_links
    readonly_fields = ('date_joined',)  # [ТЗ 7.10] (у вас нет last_login)


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(models.AntiqueItem)
class AntiqueItemAdmin(admin.ModelAdmin):
    # [ТЗ 7.5, 7.6] @admin.display и short_description
    @admin.display(description='Превью')
    def item_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;"/>', obj.image)
        return "Нет фото"

    list_display = ('name', 'price', 'category', 'condition', 'stock', 'item_image_preview')
    list_filter = ('category', 'condition', 'created_at')  # [ТЗ 7.2]
    search_fields = ('name', 'description')  # [ТЗ 7.11]
    readonly_fields = ('created_at', 'updated_at')  # [ТЗ 7.10]
    raw_id_fields = ('category',)  # [ТЗ 7.9] raw_id_fields для внешних ключей
    date_hierarchy = 'created_at'  # [ТЗ 7.4]
    
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'description', 'price', 'category')
        }),
        ('Детали', {
            'fields': ('era', 'condition', 'stock')
        }),
        ('Медиа', {
            'fields': ('image', 'certificate_pdf', 'video_review_url')
        }),
        ('Важные даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(models.CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'antique_item', 'quantity', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__email', 'antique_item__name')


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'payment_method')  # [ТЗ 7.2]
    search_fields = ('user__email', 'delivery_address')  # [ТЗ 7.11]
    readonly_fields = ('total_price', 'created_at', 'updated_at')  # [ТЗ 7.10]
    inlines = [OrderItemInline]  # [ТЗ 6.5] inlines


@admin.register(models.OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'antique_item', 'quantity', 'price_at_time')
    search_fields = ('order__id', 'antique_item__name')