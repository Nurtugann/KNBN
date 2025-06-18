# main/models.py

import os
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# -------------------------------------------------------------------
# Статичные справочники
# -------------------------------------------------------------------

REGION_CHOICES = [
    ('KST', 'Костанай'),
    ('AKM', 'Акмола'),
    ('PAV', 'Павлодар'),
    ('KAR', 'Караганда'),
    ('VKO', 'ВКО'),
    ('SKO', 'СКО'),
]


class Status(models.Model):
    """
    Статус для Kanban-доски и истории:
      - name: название
      - order: порядок на доске
      - duration_days: рекомендованное максимальное время в статусе
    """
    name = models.CharField("Название статуса", max_length=400)
    order = models.PositiveIntegerField(
        "Порядок отображения",
        default=0,
        help_text="Чем меньше — тем левее на доске"
    )
    duration_days = models.PositiveIntegerField(
        "Рекомендуемое время (дней)",
        default=0,
        help_text="Рекомендованное количество дней в этом статусе"
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"

    def __str__(self):
        return self.name


# -------------------------------------------------------------------
# Дополнительная модель для регионов (для множественного выбора)
# -------------------------------------------------------------------

class Region(models.Model):
    """
    Модель «Регион» для привязки к профилю пользователя.
    """
    code = models.CharField(
        "Код региона",
        max_length=3,
        unique=True,
        choices=REGION_CHOICES
    )
    name = models.CharField("Название региона", max_length=50)

    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"

    def __str__(self):
        return self.name

    def get_code_display(self):
        return dict(REGION_CHOICES).get(self.code, self.code)

from datetime import timedelta
# -------------------------------------------------------------------
# Основные модели
# -------------------------------------------------------------------

class Company(models.Model):
    """
    Компания — основной объект, привязанный к пользователю-владельцу.
    Дополнительные необязательные поля: БИН, Управляющий, Сумма долга.
    """
    name = models.CharField("Название компании", max_length=200)

    bin_number = models.CharField(
        "БИН",
        max_length=50,
        blank=True,
        null=True,
        help_text="Бизнес-идентификационный номер (необязательно)"
    )
    manager_name = models.CharField(
        "Управляющий",
        max_length=150,
        blank=True,
        null=True,
        help_text="Имя ответственного лица/управляющего (необязательно)"
    )
    debt_amount = models.DecimalField(
        "Сумма долга",
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Сумма долга (необязательно)"
    )

    status = models.ForeignKey(
        Status,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Текущий статус"
    )
    position = models.IntegerField(
        "Позиция в колонке",
        default=0,
        help_text="Порядок внутри одного статуса на доске"
    )
    region = models.CharField(
        "Регион",
        max_length=3,
        choices=REGION_CHOICES,
        default="KST",
        help_text="Географический регион компании"
    )
    repaid_amount = models.DecimalField(
        "Сумма погашения",
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Сумма уже погашенного долга (если есть)"
    )


    class Meta:
        ordering = ["position"]
        verbose_name = "Компания"
        verbose_name_plural = "Компании"

    def __str__(self):
        return self.name

    def region_display(self):
        return dict(REGION_CHOICES).get(self.region, '—')
    

    @property
    def days_left(self):
        latest_status = self.history.order_by('-changed_at').first()
        if not latest_status or not latest_status.status or latest_status.status.duration_days == 0:
            return None
        deadline = latest_status.changed_at.date() + timedelta(days=latest_status.status.duration_days)
        return (deadline - timezone.now().date()).days


class CompanyStatusHistory(models.Model):
    """
    История смены статусов компании.
    Храним момент смены и сам статус, а теперь — ещё и паузу.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="Компания"
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Статус"
    )
    changed_at = models.DateTimeField(
        "Дата и время смены",
        default=timezone.now,
        help_text="Когда был установлен этот статус"
    )

    # Новые поля для «пауз»
    is_paused = models.BooleanField(
        "На паузе",
        default=False,
        help_text="Флаг: этот этап приостановлен?"
    )
    paused_at = models.DateTimeField(
        "Когда поставили на паузу",
        null=True,
        blank=True,
        help_text="Если этап на паузе, когда именно он был поставлен на паузу"
    )

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = "Запись истории статусов"
        verbose_name_plural = "История статусов"

    def __str__(self):
        ts = self.changed_at.strftime("%Y-%m-%d %H:%M")
        st = self.status.name if self.status else "Без статуса"
        return f"{self.company.name}: {ts} → {st}"


class Comment(models.Model):
    """
    Комментарий пользователя к компании или к конкретному этапу (статусу).
    Если status=None, значит это комментарий «к компании в целом».
    Если status=Status, значит — «к этому этапу».
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Компания"
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="stage_comments",
        verbose_name="Этап (если комментарий к этапу)",
        help_text="Оставьте пустым, если это комментарий к компании в целом"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор"
    )
    text = models.TextField("Текст комментария")
    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        target = self.status.name if self.status else "компания"
        return f"Комментарий от {self.author.username} к {target} — {self.company.name}"


User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь"
    )
    regions = models.ManyToManyField(
        Region,
        verbose_name="Регионы пользователя",
        blank=True,
        help_text="Выберите один или несколько регионов"
    )

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Профиль {self.user.username}"


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    """
    При создании User сразу создаём Profile,
    при каждом save – проверяем, что профиль существует.
    """
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)


class CompanyStatusDocument(models.Model):
    """
    Файл (PDF) для пары (Company, Status).
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='status_documents',
        verbose_name="Компания"
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.CASCADE,
        related_name='company_documents',
        verbose_name="Статус"
    )
    file = models.FileField(
        upload_to='company_status_docs/%Y/%m/%d/',
        verbose_name="PDF-файл"
    )
    uploaded_at = models.DateTimeField(
        "Дата загрузки",
        default=timezone.now
    )

    class Meta:
        verbose_name = 'Документ (компания + статус)'
        verbose_name_plural = 'Документы (компания + статус)'

    def __str__(self):
        return f"{self.company.name} — {self.status.name} ({os.path.basename(self.file.name)})"
