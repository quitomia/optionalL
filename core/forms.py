from django import forms
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Order, CartItem, AntiqueItem
# Форма регистрации
class RegistrationForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'example@mail.ru'})
    )
    name = forms.CharField(
        label='Имя',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ваше имя'})
    )
    phone = forms.CharField(
        label='Телефон',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+7 (999) 123-45-67'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Введите пароль'})
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Повторите пароль'})
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        
        if password and password2 and password != password2:
            raise forms.ValidationError('Пароли не совпадают')
        
        if password and len(password) < 4:
            raise forms.ValidationError('Пароль должен содержать минимум 4 символа')
        
        return cleaned_data


# Форма входа
class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'example@mail.ru'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Введите пароль'})
    )

# core/forms.py (добавьте в конец файла)


class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'quantity-input',
                'min': 1,
                'style': 'width: 80px; padding: 0.5rem;'
            }),
        }
        labels = {
            'quantity': 'Количество',
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['delivery_address', 'payment_method']
        
        widgets = {
            'delivery_address': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Улица, дом, квартира, подъезд...',
                'class': 'form-input'
            }),
            # [ТЗ 4.8] Select с выбором способа оплаты
            'payment_method': forms.Select(attrs={
                'class': 'form-input'
            }, choices=[
                ('card', 'Онлайн картой'),
                ('cash', 'Наличными при получении'),
            ]),
        }
        
        labels = {
            'delivery_address': 'Адрес доставки',
            'payment_method': 'Способ оплаты',
        }
        
        help_texts = {
            'delivery_address': 'Укажите точный адрес для доставки',
            'payment_method': 'Выберите удобный способ оплаты',
        }
        
        error_messages = {
            'delivery_address': {
                'required': 'Пожалуйста, укажите адрес доставки',
            },
        }
    
    def clean_delivery_address(self):
        address = self.cleaned_data.get('delivery_address')
        if len(address) < 10:
            raise forms.ValidationError('Адрес должен содержать минимум 10 символов')
        return address
    # [ТЗ 4.9] form.is_valid() + cleaned_data (используется во view)
    def clean(self):
        cleaned_data = super().clean()
        # Дополнительная валидация
        return cleaned_data

class AntiqueItemForm(forms.ModelForm):
    class Meta:
        model = AntiqueItem
        fields = ['name', 'description', 'price', 'category', 'era', 'condition', 'stock', 'image', 'certificate_pdf', 'video_review_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Название товара'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-input', 'placeholder': 'Описание...'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Цена'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'era': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Например: XIX век'}),
            'condition': forms.Select(attrs={'class': 'form-input'}),
            'stock': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Количество на складе'}),
            'video_review_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
        }
        labels = {
            'name': 'Название',
            'description': 'Описание',
            'price': 'Цена',
            'category': 'Категория',
            'era': 'Эпоха',
            'condition': 'Состояние',
            'stock': 'Количество на складе',
            'image': 'Изображение',
            'certificate_pdf': 'PDF-сертификат',
            'video_review_url': 'Ссылка на видеообзор',
        }
    class Media:
        css = {
            'all': ('css/item-form.css',)  # путь от STATIC_URL
        }
        js = ('js/preview-image.js',)      # скрипт для предпросмотра картинки
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError('Цена должна быть больше 0')
        return price
    
    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock < 0:
            raise forms.ValidationError('Количество не может быть отрицательным')
        return stock