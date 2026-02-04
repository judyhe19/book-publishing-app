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
from .views.book import BookListCreateView, BookDetailView
from .views.sales import SaleGetView, SaleCreateView, SaleCreateManyView, SaleEditView, SaleDeleteView, SalePayAuthorsView
from .views.author import AuthorUnpaidSubtotalView, AuthorPayUnpaidSalesView


urlpatterns = [
    path("csrf", csrf),
    path("user/login", LoginView.as_view()),
    path("user/logout", LogoutView.as_view()),
    path("user/register", RegisterView.as_view()),
    path("user/changepassword", ChangePasswordView.as_view()),
    path("user/me", MeView.as_view()),
    
    path("books/", BookListCreateView.as_view()),
    path("books/<int:book_id>/", BookDetailView.as_view()),
    
    path("sale/get_all", SaleGetView.as_view()),
    path("sale/<int:sale_id>/get", SaleGetView.as_view()),
    path("sale/create", SaleCreateView.as_view()),
    path("sale/createmany", SaleCreateManyView.as_view()),
    path("sale/<int:sale_id>/edit", SaleEditView.as_view()),
    path("sale/<int:sale_id>", SaleDeleteView.as_view()),
    path("sale/<int:sale_id>/pay_authors", SalePayAuthorsView.as_view()),
    
    path("author/<int:author_id>/unpaid/subtotal", AuthorUnpaidSubtotalView.as_view()),
    path("author/<int:author_id>/pay_unpaid_sales", AuthorPayUnpaidSalesView.as_view()),
]
