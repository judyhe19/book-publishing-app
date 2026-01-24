"""
URL configuration for backend project.

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
from django.urls import path
from .views.auth import LoginView, LogoutView
from .views.registration import RegisterView
from .views.change_password import ChangePasswordView
from .views.account import MeView
from .views.csrf import csrf

urlpatterns = [
    path("csrf", csrf),
    path("user/login", LoginView.as_view()),
    path("user/logout", LogoutView.as_view()),
    path("user/register", RegisterView.as_view()),
    path("user/changepassword", ChangePasswordView.as_view()),
    path("user/me", MeView.as_view()),
]
