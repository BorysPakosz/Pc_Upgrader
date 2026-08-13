"""
URL configuration for pcassistant project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', include(('hardware.urls', 'hardware'), namespace='hardware')),
    path('admin/', admin.site.urls),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done_custom.html',
         ),
         name='password_reset_done'),

    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_custom.html",
            subject_template_name="registration/password_reset_subject_custom.txt",
            html_email_template_name="registration/password_reset_email_custom.html",
            email_template_name="registration/password_reset_email_custom.txt",
            extra_email_context={
                "site_name": "PC Assistant",
                "domain": "127.0.0.1:8000",
                "protocol": "http",
            },
        ),
        name="password_reset",
    ),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm_custom.html',
         ),
         name='password_reset_confirm'),

    path('reset/<uidb64>/set-password/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm_custom.html',
         ),
         name='password_reset_set_password'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete_custom.html',
         ),
         name='password_reset_complete'),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html"
        ),
        name="login",
    ),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
