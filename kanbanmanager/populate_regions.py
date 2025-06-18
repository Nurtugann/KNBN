# populate_regions.py
import os
import django

# Устанавливаем настройки Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kanbanmanager.settings")
django.setup()

from main.models import Region

regions = [
    ("KST", "Костанай"),
    ("AKM", "Акмола"),
    ("PAV", "Павлодар"),
    ("KAR", "Караганда"),
    ("VKO", "ВКО"),
    ("SKO", "СКО"),
]

for code, name in regions:
    Region.objects.get_or_create(code=code, name=name)

print("✅ Регионы успешно добавлены (или уже существуют).")
