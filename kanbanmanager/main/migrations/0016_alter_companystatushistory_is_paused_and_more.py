# Generated by Django 5.1.9 on 2025-06-04 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_comment_status_companystatushistory_is_paused_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companystatushistory',
            name='is_paused',
            field=models.BooleanField(default=False, help_text='Если True — этап остановлен (пауза)', verbose_name='На паузе'),
        ),
        migrations.AlterField(
            model_name='companystatushistory',
            name='paused_at',
            field=models.DateTimeField(blank=True, help_text='Если is_paused=True — дата и время последнего нажатия «Пауза»', null=True, verbose_name='Когда поставили на паузу'),
        ),
    ]
