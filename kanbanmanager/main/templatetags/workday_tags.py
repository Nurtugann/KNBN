# main/templatetags/workday_tags.py
from django import template
from datetime import timedelta

register = template.Library()

def add_workdays_to_date(start_dt, days):
    """
    Прибавляет к дате start_dt ровно days рабочих дней (Mon–Fri).
    Возвращает новый datetime (с тем же временем, что и start_dt),
    но сдвинутый на days рабочих дней вперёд.
    """
    current_date = start_dt.date()
    added = 0
    while added < days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # 0..4 = Mon..Fri
            added += 1
    return start_dt.replace(
        year=current_date.year,
        month=current_date.month,
        day=current_date.day
    )

@register.filter
def add_workdays(value, days):
    """
    Фильтр: {{ value|add_workdays:days }}.
    value — это datetime, days — целое число рабочих дней.
    """
    try:
        days_int = int(days)
        return add_workdays_to_date(value, days_int)
    except Exception:
        return value
