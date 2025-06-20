# Generated by Django 5.1.9 on 2025-06-04 09:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_alter_company_name_alter_status_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='main.status', verbose_name='Этап (статус)'),
        ),
        migrations.AddField(
            model_name='companystatushistory',
            name='is_paused',
            field=models.BooleanField(default=False, help_text='Если True, отсчёт рабочих дней для этого этапа приостановлен', verbose_name='На паузе'),
        ),
        migrations.AddField(
            model_name='companystatushistory',
            name='paused_at',
            field=models.DateTimeField(blank=True, help_text='Когда этап был поставлен на паузу', null=True, verbose_name='Время постановки на паузу'),
        ),
    ]
