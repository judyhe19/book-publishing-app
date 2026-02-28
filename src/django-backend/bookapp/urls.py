from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.auth import LoginView, LogoutView
from .views.registration import RegisterView
from .views.change_password import ChangePasswordView
from .views.account import MeView
from .views.csrf import csrf

from .views.book import BookViewSet
from .views.sales import SaleViewSet, BookSalesTotalsView
from .views.author import AuthorViewSet
from .views.author_payments import AuthorPaymentsViewSet
from .views.cover_upload import CoverImageUploadView
from .views.cover_thumbnail import CoverThumbnailView
from .views.cover_image import CoverImageView
from .views.series import SeriesListView, SeriesReorderView

# ----- DRF Router -----
router = DefaultRouter(trailing_slash=True)
router.register(r"books", BookViewSet, basename="book")
router.register(r"sales", SaleViewSet, basename="sale")
router.register(r"authors", AuthorViewSet, basename="author")

urlpatterns = [
    # Auth / user endpoints (not model-backed, keep as plain paths)
    path("csrf", csrf),
    path("user/login", LoginView.as_view()),
    path("user/logout", LogoutView.as_view()),
    path("user/register", RegisterView.as_view()),
    path("user/changepassword", ChangePasswordView.as_view()),
    path("user/me", MeView.as_view()),

    # Author payments (custom ViewSet, manually routed)
    path(
        "author/payments/grouped",
        AuthorPaymentsViewSet.as_view({"get": "list"}),
        name="author-payments-grouped",
    ),

    # Book sales totals (book-scoped, not sale-scoped)
    path(
        "sales/book/<int:book_pk>/totals",
        BookSalesTotalsView.as_view({"get": "retrieve"}),
        name="book-sales-totals",
    ),

    # Cover image upload
    path(
        "books/upload-cover/",
        CoverImageUploadView.as_view(),
        name="upload-cover",
    ),

    # Cover image thumbnail (resized for table/list views)
    path(
        "books/cover-thumbnail/",
        CoverThumbnailView.as_view(),
        name="cover-thumbnail",
    ),

    # Cover image full-size (for detail views)
    path(
        "books/cover-image/",
        CoverImageView.as_view(),
        name="cover-image",
    ),

    # Series list and bulk reorder
    path("series/", SeriesListView.as_view(), name="series-list"),
    path("series/reorder/", SeriesReorderView.as_view(), name="series-reorder"),

    # Router-generated URLs for books, sales, authors
    path("", include(router.urls)),
]