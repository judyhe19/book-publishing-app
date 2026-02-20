from django.test import TestCase
from rest_framework.exceptions import ValidationError
from bookapp.serializers.book import BookCreateSerializer
from bookapp.models import Author, Book
import datetime

class BookValidationTest(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name="Test Author")

    def test_valid_book(self):
        data = {
            'title': 'Valid Book',
            'publication_date': '2023-01',
            'isbn_13': '1234567890123',
            'isbn_10': '1234567890',
            'authors': [{'author_name': self.author.name, 'royalty_rate': 0.5}]
        }
        serializer = BookCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        book = serializer.save()
        self.assertEqual(book.title, 'Valid Book')

    def test_missing_title(self):
        data = {
            'publication_date': '2023-01',
            'isbn_13': '1234567890123',
            'authors': [{'author_name': self.author.name, 'royalty_rate': 0.5}]
        }
        serializer = BookCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_missing_authors(self):
        data = {
            'title': 'No Author Book',
            'publication_date': '2023-01',
            'isbn_13': '1234567890123',
            'authors': []
        }
        serializer = BookCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('authors', serializer.errors)

    def test_invalid_isbn_length(self):
        data = {
            'title': 'Bad ISBN Book',
            'publication_date': '2023-01',
            'isbn_13': '123', # Too short
            'authors': [{'author_name': self.author.name, 'royalty_rate': 0.5}]
        }
        serializer = BookCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('isbn_13', serializer.errors)
        
    def test_negative_royalty(self):
        data = {
            'title': 'Negative Royalty Book',
            'publication_date': '2023-01',
            'isbn_13': '1234567890123',
            'authors': [{'author_name': self.author.name, 'royalty_rate': -0.5}]
        }
        serializer = BookCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        # Errors are nested: {'authors': [{'royalty_rate': [...]}]}
        self.assertIn('authors', serializer.errors)
        self.assertIn('royalty_rate', serializer.errors['authors'][0])

    def test_duplicate_authors(self):
        data = {
            'title': 'Duplicate Author Book',
            'publication_date': '2023-01',
            'isbn_13': '1234567890123',
            'authors': [
                {'author_name': self.author.name, 'royalty_rate': 0.1},
                {'author_name': self.author.name, 'royalty_rate': 0.1}
            ]
        }
        serializer = BookCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('authors', serializer.errors)

    def test_invalid_royalty_format(self):
        data = {
            'title': 'Invalid Royalty Book',
            'publication_date': '2023-01',
            'isbn_13': '1234567890123',
            'authors': [
                {'author_name': self.author.name, 'royalty_rate': "not-a-number"}
            ]
        }
        serializer = BookCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        # Errors are nested: {'authors': [{'royalty_rate': [...]}]}
        self.assertIn('authors', serializer.errors)
        self.assertIn('royalty_rate', serializer.errors['authors'][0])
