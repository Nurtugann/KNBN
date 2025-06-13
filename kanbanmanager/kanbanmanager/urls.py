# kanbanmanager/urls.py

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from main import views as main_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # ─── Аутентификация (вход/выход) ─────────────────────────────────────────
    path('login/', auth_views.LoginView.as_view(
            template_name='registration/login.html'
        ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
            next_page='login'
        ), name='logout'),

    # ─── Регистрация ─────────────────────────────────────────────────────────
    # Только для /accounts/signup/ → main_views.signup
    path('accounts/signup/', main_views.signup, name='signup'),

    # ─── Основное приложение “main” ──────────────────────────────────────────
    # Все остальные маршруты (index, company/<pk>/, board/, и т. д.)
    path('', include(('main.urls', 'main'), namespace='main')),
]

if settings.DEBUG:
    # здесь — именно в корневом urls.py !
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)