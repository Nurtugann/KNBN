import pandas as pd
from django.core.management.base import BaseCommand
from main.models import Company
from django.db import transaction

class Command(BaseCommand):
    help = 'Импортирует компании из Excel с мэппингом регионов'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='Путь к Excel-файлу')
        parser.add_argument('--sheet', type=str, default='2024', help='Имя листа в Excel')
        parser.add_argument('--skiprows', type=int, default=2, help='Сколько строк пропустить сверху')

    @transaction.atomic
    def handle(self, *args, **options):
        path     = options['file']
        sheet    = options['sheet']
        skiprows = options['skiprows']

        # Читаем Excel
        df = pd.read_excel(path, sheet_name=sheet, skiprows=skiprows)
        df = df[df['Unnamed: 0'].notna()]
        df = df[['Контрагенты', 'БИН / ИИН', 'Регион']][1:]

        # Мэппинг кириллицы -> латиница по REGION_CHOICES
        cyr_to_lat = {
            'АСТ':'AKM',
            'КОС':'KST',
            'СКО': 'SKO',  # пример: Северо-Казахстан → KST
            'АКМ': 'AKM',
            'ПАВ': 'PAV',
            'ВКО': 'VKO',
            'КАР': 'KAR',
            # добавьте остальные по вашей таблице
        }
        # Доступные коды из модели
        valid_codes = {code for code, _ in Company._meta.get_field('region').choices}

        total = 0
        for idx, row in df.iterrows():
            name    = str(row['Контрагенты']).strip()
            bin_num = str(row['БИН / ИИН']).strip()
            raw     = str(row['Регион']).strip().upper()

            code = cyr_to_lat.get(raw)
            if not code or code not in valid_codes:
                self.stderr.write(f'⚠ Строка {idx + skiprows + 1}: неизвестный код региона "{raw}"')
                continue

            obj, created = Company.objects.update_or_create(
                name=name,
                defaults={
                    'bin_number': bin_num,
                    'region':     code,
                }
            )
            verb = 'Создана' if created else 'Обновлена'
            self.stdout.write(f'{verb} компания: {obj.name} (регион {code})')
            total += 1

        self.stdout.write(self.style.SUCCESS(f'Импорт завершён: обработано {total} компаний.'))
