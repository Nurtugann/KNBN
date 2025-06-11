# dump_from_sqlite.py
import io, os, django
from django.core.management import call_command

# Подключаем Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kanbanmanager.settings")
django.setup()

# Выгружаем всё, кроме системных моделей
stream = io.StringIO()
call_command(
    'dumpdata',
    '--exclude', 'contenttypes',
    '--exclude', 'auth.permission',
    '--exclude', 'admin.logentry',
    '--indent', '2',
    stdout=stream
)

# Пишем файл в UTF-8 без BOM
with open('full_data.json', 'w', encoding='utf-8') as f:
    f.write(stream.getvalue())

print("✅ full_data.json записан из SQLite в UTF-8 без BOM.")
