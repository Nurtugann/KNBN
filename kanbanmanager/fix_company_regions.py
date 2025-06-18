# fix_company_regions.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kanbanmanager.settings")
django.setup()

from main.models import Company, Region

for company in Company.objects.all():
    if isinstance(company.region, str):
        region = Region.objects.filter(code=company.region).first()
        if region:
            company.region = region
            company.save()

print("✅ Компании обновлены.")
