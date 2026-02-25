from django.contrib import admin
from .models import Author, Book, Sale, AuthorBook

# Register your models here.
admin.site.register(Author)
admin.site.register(Book)
admin.site.register(Sale)
admin.site.register(AuthorBook)