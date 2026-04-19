from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse  
from reportlab.pdfgen import canvas  
from django.contrib.auth.hashers import make_password
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

def export_order_pdf(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="orders.pdf"'
    
    p = canvas.Canvas(response)
    p.setTitle("Orders Report")
    
    # Используем стандартный шрифт
    y = 800
    
    p.setFont("Helvetica", 14)
    p.drawString(50, y, "VESTIGE Orders List")
    y -= 40
    
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "ID")
    p.drawString(100, y, "User")
    p.drawString(250, y, "Total")
    p.drawString(350, y, "Status")
    p.drawString(450, y, "Date")
    y -= 20
    
    p.setFont("Helvetica", 9)
    for order in queryset:
        if y < 100:
            p.showPage()
            y = 800
            p.setFont("Helvetica", 9)
        
        p.drawString(50, y, str(order.id))
        p.drawString(100, y, order.user.email[:20])
        p.drawString(250, y, f"{order.total_price:.2f}")
        p.drawString(350, y, order.status)
        p.drawString(450, y, order.created_at.strftime("%Y-%m-%d"))
        y -= 20
    
    p.save()
    return response

export_order_pdf.short_description = "Экспортировать выбранные заказы в PDF"


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

    fields = ('email', 'name', 'phone', 'password', 'is_staff', 'date_joined')

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data or not change:
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)

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
    
    @admin.display(description='Доп. категории')
    def get_additional_categories(self, obj):
        return ", ".join([c.name for c in obj.additional_categories.all()][:3]) or "—"

    list_display = ('name', 'price', 'category', 'get_additional_categories', 'condition', 'stock', 'item_image_preview')
    
    list_filter = ('category', 'condition', 'created_at')  # [ТЗ 7.2]
    search_fields = ('name', 'description')  # [ТЗ 7.11]
    readonly_fields = ('created_at', 'updated_at')  # [ТЗ 7.10]
    raw_id_fields = ('category',)  # [ТЗ 7.9] raw_id_fields для внешних ключей
    date_hierarchy = 'created_at'  # [ТЗ 7.4]
    
    filter_horizontal = ('additional_categories',)  # [ТЗ 7.7]

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'description', 'price', 'category', 'additional_categories')  # добавили additional_categories
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

    actions = [export_order_pdf]  # [ТЗ 5.1] Генерация PDF в админке


@admin.register(models.OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'antique_item', 'quantity', 'price_at_time')
    search_fields = ('order__id', 'antique_item__name')