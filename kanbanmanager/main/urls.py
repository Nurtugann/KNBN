from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'main'

urlpatterns = [
    # Главная страница — список компаний (index view)
    path('', views.index, name='index'),
    # Табличный обзор компаний (альтернативный URL)
    path('companies_table/', views.companies_table, name='companies_table'),

    # Kanban-доска
    # path('board/', views.board, name='board'),

    # CRUD для компаний
    path('add/', views.add_company, name='add_company'),
    path('edit/<int:pk>/', views.edit_company, name='edit_company'),
    path('delete/<int:pk>/', views.delete_company, name='delete_company'),

    # urls.py
    path(
        'history/<int:history_id>/delete/',
        views.delete_status_history,
        name='delete_status_history'
    ),





    # Перемещение и переупорядочивание компаний на Kanban-доске
    path('move/', views.move_company, name='move_company'),
    path('reorder/', views.reorder_companies, name='reorder_companies'),

    # Деталь компании с историей и комментариями
    path('company/<int:pk>/', views.company_detail, name='company_detail'),
    path('company/<int:company_id>/history/add/', views.add_status_history, name='add_status_history'),
    path('history/<int:history_id>/edit/', views.edit_status_history, name='edit_status_history'),
    path('history/<int:history_id>/delete/', views.delete_status_history, name='delete_status_history'),

    # Загрузка и удаление документов для этапов
    path(
        'company/<int:company_id>/status/<int:status_id>/docs/',
        views.attach_docs,
        name='attach_docs'
    ),
    path(
        'company/<int:company_id>/status/<int:status_id>/docs/<int:doc_id>/delete/',
        views.delete_doc,
        name='delete_doc'
    ),

    # Комментарии к этапам статуса
    path(
        'company/<int:company_id>/status/<int:status_id>/add_comment/',
        views.add_status_comment,
        name='add_status_comment'
    ),

    # AJAX-пауза для записи истории
    # urls.py
    path(
    'company/<int:company_id>/history/<int:hist_id>/toggle_objection/',
    views.toggle_objection,
    name='toggle_objection'
    ),


    # Страницы профиля и регистрации
    path('profile/', views.profile, name='profile'),
    path('signup/', views.signup, name='signup'),
]

# Поддержка статики и медиа в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
