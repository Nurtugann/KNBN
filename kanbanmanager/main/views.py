# main/views.py

import json
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Subquery, OuterRef, Max, IntegerField, Value
from django.db.models.functions import Coalesce, Greatest

from .models import (
    Company,
    Status,
    CompanyStatusHistory,
    Comment,
    Profile,
    CompanyStatusDocument,
    Region,
    REGION_CHOICES,
)
from .forms import (
    CompanyForm,
    CompanyStatusHistoryForm,
    CommentForm,
    CompanyStatusDocumentForm,
    SignUpForm,
)


def count_workdays(start_dt, end_dt):
    """
    Считает число рабочих дней (Mon–Fri) между двумя datetime.
    """
    start_date = start_dt.date()
    end_date = end_dt.date()
    workdays = 0
    current = start_date
    while current < end_date:
        if current.weekday() < 5:
            workdays += 1
        current += timedelta(days=1)
    return workdays


@login_required
def profile(request):
    user = request.user

    if user.is_staff:
        qs = Company.objects.all()
    else:
        user_regions = user.profile.regions.values_list('code', flat=True)
        qs = Company.objects.filter(region__in=user_regions)

    now = timezone.now()

    overdue_list = []
    almost_overdue_list = []

    for c in qs:
        last_hist = c.history.first()

        c.days_in_status = None
        c.is_overdue = False
        calculated_days_left = None  # ✅ теперь переменная локальная

        if last_hist and c.status and c.status.duration_days:
            passed = count_workdays(last_hist.changed_at, now)
            c.days_in_status = passed

            duration = c.status.duration_days

            if passed > duration:
                c.is_overdue = True
            else:
                c.is_overdue = False
                calculated_days_left = duration - passed

        if c.is_overdue:
            overdue_list.append(c)
        elif calculated_days_left is not None and calculated_days_left <= 1:
            almost_overdue_list.append(c)

    by_status = (
        qs.values('status__name')
          .annotate(count=Count('id'))
          .order_by('status__name')
    )

    total = qs.count()
    overdue = len(overdue_list)

    return render(request, 'main/profile.html', {
        'title':               'Личный кабинет',
        'total':               total,
        'overdue':             overdue,
        'by_status':           by_status,
        'almost_overdue_list': almost_overdue_list,
        'overdue_list':        overdue_list,
    })


def add_workdays(start_dt, workdays_to_add):
    """
    Прибавить к дате start_dt указанное количество рабочих дней (Mon–Fri).
    Возвращает datetime (с тем же временем суток).
    """
    current = start_dt
    added = 0
    while added < workdays_to_add:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Company, Status, CompanyStatusHistory, CompanyStatusDocument, Comment
from .forms  import CommentForm

@login_required
def company_detail(request, pk):
    """
    Просмотр детали компании + комментарии, пауза/возобновить, история,
    и кнопка перехода к следующему этапу.
    """
    company = get_object_or_404(Company, pk=pk)

    # 0) Дни в текущем статусе
    last_change = company.history.first()
    days_in_status = None
    if last_change and company.status and company.status.duration_days:
        days_in_status = count_workdays(last_change.changed_at, timezone.now())

    # 1) Комментарий к компании
    if request.method == 'POST' and 'company_comment' in request.POST:
        form = CommentForm(request.POST)
        if form.is_valid():
            com = form.save(commit=False)
            com.company = company
            com.author = request.user
            com.save()
            return redirect('main:company_detail', pk=pk)
    else:
        form = CommentForm()

    # 2) Собираем статус-инфо
    statuses = Status.objects.order_by('order')
    status_info = []
    now = timezone.now()
    for st in statuses:
        hist = CompanyStatusHistory.objects.filter(company=company, status=st)\
                                          .order_by('-changed_at').first()
        workdays = count_workdays(hist.changed_at, now) if hist and st.duration_days else None
        is_over  = bool(workdays and st.duration_days and workdays > st.duration_days)
        docs_count = CompanyStatusDocument.objects.filter(company=company, status=st).count()
        expected_end = add_workdays(hist.changed_at, st.duration_days) if hist and st.duration_days else None
        stage_comments     = Comment.objects.filter(company=company, status=st).order_by('created_at')
        stage_comment_form = CommentForm()
        overall_last = CompanyStatusHistory.objects.filter(company=company).order_by('-changed_at').first()
        can_edit = bool(hist and overall_last and hist.id == overall_last.id)

        status_info.append({
            'status':             st,
            'hist':               hist,
            'days':               workdays,
            'overdue':            is_over,
            'docs_count':         docs_count,
            'is_current':         company.status_id == st.id,
            'can_edit':           can_edit,
            'expected_end':       expected_end,
            'stage_comments':     stage_comments,
            'stage_comment_form': stage_comment_form,
        })

    # 3) Общие комментарии
    company_comments = Comment.objects.filter(company=company, status__isnull=True)\
                                      .order_by('created_at')

    # 4) Полная история
    full_history = CompanyStatusHistory.objects.filter(company=company)\
                                              .order_by('-changed_at')

    # 5) Вычисляем next_status
    ordered = list(statuses)
    current_order = company.status.order if company.status else -1
    next_status = None
    for st in ordered:
        if st.order > current_order:
            next_status = st
            break

    return render(request, 'main/company_detail.html', {
        'company':          company,
        'days_in_status':   days_in_status,
        'form':             form,
        'status_info':      status_info,
        'company_comments': company_comments,
        'full_history':     full_history,
        'next_status':      next_status,
    })



@login_required
@require_POST
def add_status_comment(request, company_id, status_id):
    """
    Эндпоинт для POST-запроса из формы «Добавить комментарий к этапу».
    """
    company = get_object_or_404(Company, pk=company_id)
    status = get_object_or_404(Status, pk=status_id)

    form = CommentForm(request.POST)
    if form.is_valid():
        com = form.save(commit=False)
        com.company = company
        com.status = status
        com.author = request.user
        com.save()
    return redirect('main:company_detail', pk=company_id)


# views.py
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

@require_POST
def toggle_objection(request, company_id, hist_id):
    try:
        hist = get_object_or_404(CompanyStatusHistory, pk=hist_id, company_id=company_id)
        now = timezone.now()

        if not hist.is_paused:
            # Начать обжалование
            hist.is_paused = True
            hist.paused_at = now
        else:
            # Завершить обжалование и сбросить начало
            hist.is_paused = False
            hist.paused_at = None
            hist.changed_at = now

        hist.save()

        # Высчитаем новый expected_end (если нужно)
        expected_end = None
        if hist.status.duration_days:
            expected_end = add_workdays(hist.changed_at, hist.status.duration_days)

        return JsonResponse({
            'result': 'ok',
            'is_paused':     hist.is_paused,
            'paused_at':     hist.paused_at.strftime('%Y-%m-%d %H:%M') if hist.paused_at else '',
            'new_changed_at':    hist.changed_at.strftime('%Y-%m-%d %H:%M'),
            'new_expected_end':  expected_end.strftime('%Y-%m-%d %H:%M') if expected_end else '',
        })
    except Exception as e:
        # Отлавливаем любые исключения и возвращаем JSON
        return JsonResponse({'result': 'error', 'message': str(e)}, status=500)




from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from .models import Company, Status, CompanyStatusHistory

@login_required
@require_POST
def move_company(request):
    """
    Перемещение компании между статусами.
    Различаем AJAX (возвращаем JSON) и обычные формы (редирект + flash).
    """
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    cid = request.POST.get('company_id')
    sid = request.POST.get('status_id') or None

    # Ограничение по регионам
    if request.user.is_staff:
        qs = Company.objects
    else:
        user_regions = request.user.profile.regions.values_list('code', flat=True)
        qs = Company.objects.filter(region__in=user_regions)

    company = get_object_or_404(qs, pk=cid)
    old_status = company.status
    old_order  = old_status.order if old_status else None

    new_status = get_object_or_404(Status, pk=sid) if sid else None
    new_order  = new_status.order if new_status else None

    # Запрет на откат назад
    if (not request.user.is_staff
        and old_order is not None
        and new_order is not None
        and new_order < old_order):
        if is_ajax:
            return JsonResponse({
                'result': 'error',
                'message': 'Нельзя перевести на более ранний этап.'
            }, status=403)
        messages.error(request, "Вы не можете перевести компанию на более ранний этап.")
        return redirect('main:company_detail', pk=company.pk)

    # Если статус не изменился — ничего не делаем
    same = (old_status is None and new_status is None) or (
        old_status and new_status and old_status.id == new_status.id
    )
    if same:
        if is_ajax:
            return JsonResponse({'result': 'ok'})
        return redirect('main:company_detail', pk=company.pk)

    now = timezone.now()

    # Пропуск промежуточных этапов
    if old_status and new_status and old_order is not None and new_order is not None:
        if new_order > old_order + 1:
            skipped = Status.objects.filter(
                order__gt=old_order, order__lt=new_order
            ).order_by('order')
            for st in skipped:
                CompanyStatusHistory.objects.create(
                    company=company,
                    status=st,
                    changed_at=now,
                )

    # Запись истории и сохранение нового статуса
    CompanyStatusHistory.objects.create(
        company=company,
        status=new_status,
        changed_at=now,
    )
    company.status = new_status
    company.save(update_fields=['status'])

    # AJAX: возвращаем JSON
    if is_ajax:
        return JsonResponse({'result': 'ok'})

    # Обычный запрос: редирект + flash
    messages.success(
        request,
        f"Статус компании «{company.name}» успешно изменён на «{new_status.name if new_status else 'Без статуса'}»."
    )
    return redirect('main:company_detail', pk=company.pk)




@login_required
@require_POST
def reorder_companies(request):
    """
    Сохранение нового порядка компаний в колонке (Kanban).
    """
    payload = json.loads(request.body)
    sid = payload.get('status_id') or None
    new_order_ids = payload.get('order', [])

    new_status = get_object_or_404(Status, pk=sid) if sid else None
    new_order_value = new_status.order if new_status else None

    if request.user.is_staff:
        base_qs = Company.objects
    else:
        user_regions = request.user.profile.regions.values_list('code', flat=True)
        base_qs = Company.objects.filter(region__in=user_regions)

    now = timezone.now()

    for idx, cid in enumerate(new_order_ids):
        try:
            company = base_qs.get(pk=cid)
        except Company.DoesNotExist:
            continue

        old_status = company.status
        old_order  = old_status.order if old_status else None

        # 1) Запрет «отката назад»
        if not request.user.is_staff and old_order is not None and new_order_value is not None:
            if new_order_value < old_order:
                continue

        # 2) Проверяем, изменился ли статус
        status_changed = False
        if old_status is None and new_status is not None:
            status_changed = True
        elif old_status is not None and new_status is None:
            status_changed = True
        elif old_status is not None and new_status is not None and old_status.id != new_status.id:
            status_changed = True

        # 3) Если перескакиваем через несколько этапов вперед — создаём промежуточные записи
        if status_changed and old_status and new_status:
            if new_order_value > old_order + 1:
                skipped_statuses = Status.objects.filter(
                    order__gt=old_order, order__lt=new_order_value
                ).order_by('order')
                for skipped in skipped_statuses:
                    CompanyStatusHistory.objects.create(
                        company=company,
                        status=skipped,
                        changed_at=now
                    )

        # 4) Сохраняем новый статус и позицию
        company.status   = new_status
        company.position = idx
        company.save(update_fields=['status', 'position'])

        # 5) Если статус изменился — создаём историю
        if status_changed:
            CompanyStatusHistory.objects.create(company=company, status=new_status, changed_at=now)

    return JsonResponse({'result': 'ok'})


@login_required
def index(request):
    if request.user.is_staff:
        qs = Company.objects.all()
    else:
        user_regions = request.user.profile.regions.values_list('code', flat=True)
        qs = Company.objects.filter(region__in=user_regions)

    q       = request.GET.get('q', '').strip()
    st_id   = request.GET.get('status')
    region  = request.GET.get('region')
    overdue = request.GET.get('overdue') == '1'

    if q:
        qs = qs.filter(name__icontains=q)
    if st_id:
        qs = qs.filter(status_id=st_id)
    if request.user.is_staff and region:
        qs = qs.filter(region=region)

    companies = []
    now = timezone.now()

    for c in qs.order_by('position'):
        last = c.history.first()
        if last and c.status and c.status.duration_days:
            workdays_elapsed = count_workdays(last.changed_at, now)
            is_overdue       = workdays_elapsed > c.status.duration_days
            days_in_status   = workdays_elapsed
        else:
            is_overdue     = False
            days_in_status = None

        if overdue and not is_overdue:
            continue

        c.days_in_status = days_in_status
        c.is_overdue     = is_overdue
        companies.append(c)

    return render(request, 'main/index.html', {
        'title':    'Список компаний',
        'companies': companies,
        'statuses': Status.objects.order_by('order'),
        'regions':  REGION_CHOICES,
    })


@login_required
def board(request):
    if request.user.is_staff:
        qs = Company.objects.all().order_by('position')
    else:
        user_regions = request.user.profile.regions.values_list('code', flat=True)
        qs = Company.objects.filter(region__in=user_regions).order_by('position')

    companies = list(qs)
    statuses  = list(Status.objects.order_by('order'))
    now = timezone.now()

    for c in companies:
        last = c.history.first()
        if last and c.status and c.status.duration_days:
            workdays_elapsed = count_workdays(last.changed_at, now)
            c.is_overdue = (workdays_elapsed > c.status.duration_days)
        else:
            c.is_overdue = False

    if request.GET.get('overdue') == '1':
        companies = [c for c in companies if c.is_overdue]

    groups = {st.id: [] for st in statuses}
    groups[None] = []
    for c in companies:
        groups.setdefault(c.status_id, []).append(c)

    board_data = [(st, groups.get(st.id, [])) for st in statuses]
    if groups.get(None):
        board_data.append((None, groups.get(None)))

    half_index = len(board_data) // 2
    board_data1 = board_data[:half_index]
    board_data2 = board_data[half_index:]

    return render(request, 'main/board.html', {
        'title':       'Kanban Board',
        'board_data1': board_data1,
        'board_data2': board_data2,
    })


@login_required
def add_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Компания добавлена")
            return redirect('main:index')
    else:
        form = CompanyForm(user=request.user)
    return render(request, 'main/add_company.html', {'title': 'Добавить компанию', 'form': form})


# main/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Company, Status
from .forms import CompanyForm

# views.py

@login_required
def edit_company(request, pk):
    # 1. Получаем компанию
    if request.user.is_staff:
        company = get_object_or_404(Company, pk=pk)
    else:
        regions = request.user.profile.regions.values_list('code', flat=True)
        company = get_object_or_404(Company, pk=pk, region__in=regions)

    old_status = company.status
    old_order  = old_status.order if old_status else -1

    # 2. Обработка POST-запроса редактирования полей (название, БИН и т. д.)
    if request.method == 'POST' and 'save_details' in request.POST:
        form = CompanyForm(request.POST, instance=company, user=request.user)
        if form.is_valid():
            new_status = form.cleaned_data.get('status')
            new_order  = new_status.order if new_status else -1

            if not request.user.is_staff and new_order < old_order:
                messages.error(request, "Нельзя выбрать более ранний этап.")
            else:
                c = form.save(commit=False)
                if not request.user.is_staff:
                    c.region = regions[0] if regions else c.region
                c.save()
                messages.success(request, "Данные компании сохранены.")
                return redirect('main:company_detail', company.pk)
    else:
        form = CompanyForm(instance=company, user=request.user)

    # 3. Вариант POST для смены статуса идёт в отдельный view move_company,
    #    поэтому здесь мы просто готовим шаблон.

    # Список всех статусов
    statuses = Status.objects.all().order_by('order')

    return render(request, 'main/company_form.html', {
        'title':   'Редактировать компанию',
        'company': company,
        'form':    form,
        'statuses': statuses,
    })




@login_required
def delete_company(request, pk):
    if request.user.is_staff:
        company = get_object_or_404(Company, pk=pk)
    else:
        user_regions = request.user.profile.regions.values_list('code', flat=True)
        company = get_object_or_404(Company, pk=pk, region__in=user_regions)

    if request.method == 'POST':
        company.delete()
        return redirect('main:index')

    return render(request, 'main/company_confirm_delete.html', {
        'title':   'Удалить компанию',
        'company': company,
    })


@login_required
def add_status_history(request, company_id):
    """
    Форма «Добавить историю»: создаёт запись в CompanyStatusHistory 
    и обновляет поле company.status.
    """
    if request.user.is_staff:
        company = get_object_or_404(Company, pk=company_id)
    else:
        user_regions = request.user.profile.regions.values_list('code', flat=True)
        company = get_object_or_404(Company, pk=company_id, region__in=user_regions)

    if request.method == 'POST':
        form = CompanyStatusHistoryForm(request.POST)
        if form.is_valid():
            h = form.save(commit=False)
            h.company = company
            h.save()
            company.status = h.status
            company.save(update_fields=['status'])
            return redirect('main:company_detail', pk=company_id)
    else:
        form = CompanyStatusHistoryForm()

    return render(request, 'main/history_form.html', {
        'title':   f'Добавить историю для {company.name}',
        'form':    form,
        'company': company,
    })


# main/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import CompanyStatusHistory, Status
from .forms import CompanyStatusHistoryForm

@login_required
def edit_status_history(request, history_id):
    """
    Редактирование записи истории CompanyStatusHistory.
    Запрет для обычных (не-staff) пользователей переключаться «назад».
    """
    if request.user.is_staff:
        h = get_object_or_404(CompanyStatusHistory, pk=history_id)
    else:
        user_regions = request.user.profile.regions.values_list('code', flat=True)
        h = get_object_or_404(
            CompanyStatusHistory,
            pk=history_id,
            company__region__in=user_regions
        )

    # Сохраним текущий порядок статуса, чтобы сравнить после изменений
    old_status = h.status
    old_order = old_status.order if old_status else -1

    if request.method == 'POST':
        form = CompanyStatusHistoryForm(request.POST, instance=h)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            new_order = new_status.order if new_status else -1

            # Если пользователь не является staff, запрещаем менять на статус с меньшим order
            if not request.user.is_staff and new_order < old_order:
                messages.error(request, "Вы не можете изменить запись истории на более ранний статус.")
                return redirect('main:company_detail', pk=h.company.pk)

            # Сохраняем изменения (в том числе, если просто изменили changed_at)
            form.save()
            messages.success(request, "Запись истории успешно обновлена.")
            return redirect('main:company_detail', pk=h.company.pk)
    else:
        form = CompanyStatusHistoryForm(instance=h)

    return render(request, 'main/history_form.html', {
        'title': f'Редактировать историю для {h.company.name}',
        'form': form,
        'company': h.company,
    })


from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def delete_status_history(request, history_id):
    # выбор объекта, проверки регионов те же, что и было
    h = get_object_or_404(CompanyStatusHistory, pk=history_id, 
        **(request.user.is_staff and {} or {
            'company__region__in': request.user.profile.regions.values_list('code', flat=True)
        })
    )
    company = h.company
    latest = CompanyStatusHistory.objects.filter(company=company).order_by('-changed_at').first()

    # нельзя удалить последнюю запись
    if h.pk == latest.pk:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'result':'error','message':'Нельзя удалить текущую запись.'}, status=400)
        messages.error(request, "Нельзя удалить текущую запись истории.")
        return redirect('main:company_detail', pk=company.pk)

    # удаляем
    h.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'result':'ok'})

    messages.success(request, "Запись истории удалена.")
    return redirect('main:company_detail', pk=company.pk)



def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("main:index")
    else:
        form = SignUpForm()
    return render(request, "main/signup.html", {"form": form, "title": "Регистрация"})


@login_required
def companies_table(request):
    q              = request.GET.get('q', '').strip()
    overdue_filter = request.GET.get('overdue') == '1'
    sort_field     = request.GET.get('sort') or ''
    sort_dir       = request.GET.get('dir') or 'asc'
    current_region = request.GET.get('region', '')

    # --- Группировка статусов ---
    group1 = Status.objects.filter(order__lt=9).order_by('order')
    group2 = Status.objects.filter(order__gte=9).order_by('order')
    grouped_statuses = [
        ("Блок 1: Претензия - исковая работа", list(group1)),
        ("Блок 2: Исполнительное производство", list(group2)),
    ]

    if request.user.is_staff:
        companies_qs = Company.objects.all()
    else:
        user_regions = request.user.profile.regions.values_list('code', flat=True)
        companies_qs = Company.objects.filter(region__in=user_regions)

    if current_region:
        companies_qs = companies_qs.filter(region=current_region)

    companies_qs = companies_qs.select_related('status')
    max_order_subquery = (
        CompanyStatusHistory.objects
            .filter(company=OuterRef('pk'), status__isnull=False)
            .values('company')
            .annotate(max_order=Max('status__order'))
            .values('max_order')
    )
    companies_qs = (
        companies_qs
        .annotate(
            passed_max_order=Subquery(max_order_subquery, output_field=IntegerField()),
            curr_order=Coalesce('status__order', Value(0))
        )
        .annotate(
            max_reached=Greatest('curr_order', Coalesce('passed_max_order', Value(0)))
        )
    )

    companies = list(companies_qs)
    now = timezone.now()
    for c in companies:
        if c.curr_order == 0 or not c.status or c.status.duration_days == 0:
            c.is_overdue = False
        else:
            last_rec = (
                CompanyStatusHistory.objects
                    .filter(company=c, status__order=c.max_reached)
                    .order_by('-changed_at')
                    .first()
            )
            c.is_overdue = bool(last_rec and count_workdays(last_rec.changed_at, now) > c.status.duration_days)

        last_current = (
            CompanyStatusHistory.objects
                .filter(company=c, status=c.status)
                .order_by('-changed_at')
                .first()
        )
        c.is_paused = bool(last_current and last_current.is_paused)

    if q:
        ql = q.lower()
        companies = [
            c for c in companies
            if ql in c.name.lower() or (c.bin_number and ql in str(c.bin_number).lower())
        ]
    if overdue_filter:
        companies = [c for c in companies if c.is_overdue]

    if sort_field == 'name':
        reverse = (sort_dir == 'desc')
        companies.sort(key=lambda c: c.name.lower(), reverse=reverse)

    regions = Region.objects.values_list('code', 'name')

    return render(request, 'main/companies_table.html', {
        'grouped_statuses': grouped_statuses,
        'companies':        companies,
        'q':                q,
        'current_region':   current_region,
        'regions':          regions,
        'overdue_filter':   overdue_filter,
        'sort_field':       sort_field,
        'sort_dir':         sort_dir,
    })


# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Company, Status, CompanyStatusDocument

@login_required
def attach_docs(request, company_id, status_id):
    """
    Загрузка и просмотр PDF-файлов для Company + Status.
    Поддерживает множественный выбор.
    """
    # 1) Получаем компанию с проверкой прав по региону
    if request.user.is_staff:
        company = get_object_or_404(Company, pk=company_id)
    else:
        user_regions = request.user.profile.regions.values_list('code', flat=True)
        company = get_object_or_404(Company, pk=company_id, region__in=user_regions)

    # 2) И статус
    status = get_object_or_404(Status, pk=status_id)

    # 3) Уже загруженные документы, чтобы их вывести на странице
    docs = CompanyStatusDocument.objects.filter(
        company=company,
        status=status
    ).order_by('-uploaded_at')

    # 4) Обработка POST — сохраняем каждый файл из списка
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        if not files:
            messages.error(request, "Вы не выбрали ни одного файла.")
        else:
            saved = 0
            for f in files:
                if f.content_type != 'application/pdf':
                    messages.warning(request, f"«{f.name}» пропущен — не PDF.")
                    continue
                CompanyStatusDocument.objects.create(
                    company=company,
                    status=status,
                    file=f
                )
                saved += 1
            messages.success(request, f"Успешно загружено {saved} файл(ов).")
        # Редирект, чтобы не дублировать POST при F5
        return redirect('main:attach_docs', company_id=company.pk, status_id=status.pk)

    # 5) GET — показываем шаблон
    return render(request, 'main/attach_docs.html', {
        'company': company,
        'status':  status,
        'docs':    docs,
    })


@login_required
def delete_doc(request, company_id, status_id, doc_id):
    if request.user.is_staff:
        company = get_object_or_404(Company, pk=company_id)
    else:
        user_regions = request.user.profile.regions.values_list('code', flat=True)
        company = get_object_or_404(Company, pk=company_id, region__in=user_regions)

    status = get_object_or_404(Status, pk=status_id)
    doc = get_object_or_404(
        CompanyStatusDocument,
        pk=doc_id,
        company=company,
        status=status
    )

    if request.method == 'POST':
        doc.delete()
        messages.success(request, "Файл успешно удалён.")
        return redirect('main:attach_docs', company_id=company.pk, status_id=status.pk)

    return redirect('main:attach_docs', company_id=company.pk, status_id=status.pk)


from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.shortcuts import render
from .models import Company, REGION_CHOICES

@login_required
def company_dashboard(request):
    if request.user.is_staff:
        companies = Company.objects.all()
    else:
        user_regions = request.user.profile.regions.values_list('code', flat=True)
        companies = Company.objects.filter(region__in=user_regions)

    # Группировка по коду региона
    region_raw = (
        companies
        .values("region")
        .annotate(
            count=Count("id"),
            total_debt=Sum("debt_amount"),
            total_repaid=Sum("repaid_amount")
        )
        .order_by("region")
    )

    # Преобразование кодов регионов в названия
    region_stats = []
    for r in region_raw:
        debt = r["total_debt"] or 0
        paid = r["total_repaid"] or 0
        region_stats.append({
            "region": dict(REGION_CHOICES).get(r["region"], r["region"]),
            "count": r["count"],
            "debt": float(debt),
            "paid": float(paid),
            "remaining": float(debt - paid),
        })
    
    status_qs = (
        companies
        .values("status__name", "status__order")
        .exclude(status__name__isnull=True)
        .annotate(count=Count("id"))
        .order_by("status__order")
    )

    context = {
        "total_companies": companies.count(),
        "total_debt": companies.aggregate(Sum("debt_amount"))["debt_amount__sum"] or 0,
        "total_repaid": companies.aggregate(Sum("repaid_amount"))["repaid_amount__sum"] or 0,
        "overdue_count": sum(
            1 for c in companies
            if c.debt_amount is not None and c.repaid_amount is not None and c.debt_amount > c.repaid_amount
        ),
        "region_stats": region_stats,
        "status_stats": list(status_qs),  # 👈 преобразуем в list

    }

    import json

    # Преобразуем QuerySet в список словарей для JS
    status_stats_raw = list(context["status_stats"])
    context["status_chart_json"] = json.dumps(status_stats_raw)


    return render(request, "main/company_dashboard.html", context)
