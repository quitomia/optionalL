# core/forms.py

from django import forms
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Order, CartItem


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



# [ТЗ 3.4] Meta widgets в формах
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


# [ТЗ 4.12] fields, exclude, widgets, labels, help_texts, error_messages
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['delivery_address', 'payment_method']  # fields
        # exclude = ['user', 'total_price', 'status']  # альтернатива
        
        widgets = {  # [ТЗ 3.4, 4.8] Meta widgets, forms.Textarea
            'delivery_address': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Улица, дом, квартира, подъезд...',
                'class': 'form-input'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-input'
            }),
        }
        
        labels = {  # labels
            'delivery_address': 'Адрес доставки',
            'payment_method': 'Способ оплаты',
        }
        
        help_texts = {  # help_texts
            'delivery_address': 'Укажите точный адрес для доставки',
            'payment_method': 'Выберите удобный способ оплаты',
        }
        
        error_messages = {  # error_messages
            'delivery_address': {
                'required': 'Пожалуйста, укажите адрес доставки',
            },
        }
    
    # [ТЗ 3.5] Пример clean_<fieldname>()
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