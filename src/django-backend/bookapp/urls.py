from django.urls import path
from .views.auth import LoginView, LogoutView
from .views.registration import RegisterView
from .views.change_password import ChangePasswordView
from .views.account import MeView
from .views.csrf import csrf
from .views.book import BookListCreateView, BookDetailView
from .views.author_payments import AuthorPaymentsGroupedView

from .views.sales import (
    SaleGetView,
    SaleCreateView,
    SaleCreateManyView,
    SaleEditView,
    SaleDeleteView,
    SalePayAuthorsView,
    BookSalesTotalsView,  # ✅ ADDED
)

from .views.author import AuthorUnpaidSubtotalView, AuthorPayUnpaidSalesView
from .views.author import AuthorListCreateView


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

    # ✅ NEW totals endpoint for Book Detail page
    path("sale/book/<int:book_id>/totals", BookSalesTotalsView.as_view()),

    path("author/<int:author_id>/unpaid/subtotal", AuthorUnpaidSubtotalView.as_view()),
    path("author/<int:author_id>/pay_unpaid_sales", AuthorPayUnpaidSalesView.as_view()),
    path("authors/", AuthorListCreateView.as_view()),
    path("author/payments/grouped", AuthorPaymentsGroupedView.as_view()),
]
