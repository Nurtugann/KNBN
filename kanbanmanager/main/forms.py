# main/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import (
    Company,
    CompanyStatusHistory,
    Comment,
    CompanyStatusDocument,
    REGION_CHOICES,
    Status,
)

User = get_user_model()


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        # Теперь включаем новые поля bin_number, manager_name, debt_amount, а также status/region
        fields = [
            'name',
            'bin_number',
            'manager_name',
            'debt_amount',
            'status',
            'region',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название компании'
            }),
            'bin_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'БИН (необязательно)'
            }),
            'manager_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Управляющий (необязательно)'
            }),
            'debt_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Сумма долга (необязательно, формат 1234.56)'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'bin_number': 'БИН',
            'manager_name': 'Управляющий',
            'debt_amount': 'Сумма долга',
            'status': 'Текущий статус',
            'region': 'Регион',
        }
        help_texts = {
            'bin_number': 'Необязательное поле',
            'manager_name': 'Необязательное поле',
            'debt_amount': 'Необязательное поле',
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Если user не суперпользователь — регион фиксируется из профиля, а выбор ограничен этим одним регионом.
        """
        super().__init__(*args, **kwargs)

        # Статусы упорядоченные по order
        self.fields['status'].queryset = Status.objects.order_by('order')

        if not user or not user.is_staff:
            # Получаем первый регион из профиля; если нет — оставляем пустым
            # (User.profile.regions — это ManyToManyField(Region))
            user_regions = user.profile.regions.all() if user and hasattr(user, 'profile') else []
            if user_regions.exists():
                # Предлагаем в choices только этот один регион
                region_code = user_regions.first().code
                region_name = dict(REGION_CHOICES).get(region_code, region_code)
                self.fields['region'].choices = [
                    (region_code, region_name)
                ]
                # Отключаем изменение региона
                self.fields['region'].disabled = True
            else:
                # Если у пользователя нет привязанных регионов, поле остаётся пустым и отключённым
                self.fields['region'].choices = []
                self.fields['region'].disabled = True


class CompanyStatusHistoryForm(forms.ModelForm):
    class Meta:
        model = CompanyStatusHistory
        fields = ['status', 'changed_at']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'changed_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
        }
        labels = {
            'status': 'Статус',
            'changed_at': 'Дата и время изменения',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # При редактировании, чтобы datetime-local правильно отобразить текущее значение:
        if self.instance and self.instance.changed_at:
            self.fields['changed_at'].initial = self.instance.changed_at.strftime('%Y-%m-%dT%H:%M')


# main/forms.py

from django import forms
from .models import Comment, Company, Status, CompanyStatusHistory, CompanyStatusDocument

class CommentForm(forms.ModelForm):
    # Добавляем поле status (необязательное), чтобы комментировать конкретный этап
    status = forms.ModelChoiceField(
        queryset=Status.objects.all(),
        required=False,
        widget=forms.HiddenInput  # мы будем передавать его скрытым input’ом в шаблоне
    )

    class Meta:
        model = Comment
        fields = ['text', 'status']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Напишите комментарий…'}),
        }


from .models import Region


class SignUpForm(UserCreationForm):
    region = forms.ChoiceField(
        choices=REGION_CHOICES,
        label="Регион",
        help_text="Выберите регион пользователя"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "region", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Вместо user.profile.region нужно user.profile.regions.add(...)
            region_code = self.cleaned_data["region"]
            # Найдём объект Region по коду:
            try:
                reg = Region.objects.get(code=region_code)
                user.profile.regions.add(reg)
            except Region.DoesNotExist:
                pass
        return user



# main/forms.py

from django import forms
from django.forms import ClearableFileInput
from .models import CompanyStatusDocument

# main/forms.py

# main/forms.py

from django import forms

class CompanyStatusDocumentForm(forms.Form):
    """
    Просто одно поле FileField (без multiple). 
    В шаблоне мы сами напишем <input type="file" multiple>.
    """
    files = forms.FileField(
        label="PDF-файлы",
        help_text="Можно выбрать несколько PDF-файлов.",
        widget=forms.ClearableFileInput,  # без attrs={'multiple': True}
        required=True
    )
