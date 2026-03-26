"""
Tests for the ISBN lookup feature.

Covers:
  - bookapp.utils.isbn_normalizer  (pure functions, no DB)
  - bookapp.utils.isbn_lookup      (external HTTP, mocked)
  - bookapp.utils.author_matcher   (DB — Author model)
  - GET  /api/books/isbn-lookup/         (IsbnLookupView)
  - GET  /api/books/isbn-lookup/cover/   (IsbnCoverProxyView)
  - POST /api/books/download-cover/      (CoverImageDownloadView)

Run with:
    pytest bookapp/tests/test_isbn_lookup.py -v
"""

from unittest.mock import MagicMock, patch, mock_open

import pytest
import requests as req
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from bookapp.models import Author
from bookapp.utils.isbn_normalizer import normalize_volume_info
from bookapp.utils.isbn_lookup import IsbnLookup, IsbnLookupError
from bookapp.utils.author_matcher import match_author, FUZZY_MATCH_THRESHOLD


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _mock_response(status_code=200, json_body=None, content=b"", content_type="image/jpeg"):
    mock = MagicMock()
    mock.status_code = status_code
    mock.ok = status_code < 400
    mock.json.return_value = json_body or {}
    mock.content = content
    mock.headers = {"Content-Type": content_type}
    return mock


def _google_books_response(title="Dune", isbn_13="9780441172719", isbn_10="0441172717"):
    """Minimal Google Books API response with one item."""
    return {
        "totalItems": 1,
        "items": [{
            "volumeInfo": {
                "title": title,
                "authors": ["Frank Herbert"],
                "publishedDate": "1990-09-01",
                "industryIdentifiers": [
                    {"type": "ISBN_13", "identifier": isbn_13},
                    {"type": "ISBN_10", "identifier": isbn_10},
                ],
                "imageLinks": {
                    "thumbnail": "http://books.google.com/books/content?id=abc&zoom=1",
                },
            }
        }]
    }


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="pass12345")


@pytest.fixture
def authed_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


# ─────────────────────────────────────────────────────────────────────────────
# isbn_normalizer
# ─────────────────────────────────────────────────────────────────────────────

class TestIsbnNormalizerHappyPath:

    def test_title_extracted(self):
        info = {"title": "Dune", "authors": []}
        assert normalize_volume_info(info)["title"] == "Dune"

    def test_isbn_13_extracted(self):
        info = {
            "industryIdentifiers": [
                {"type": "ISBN_13", "identifier": "9780441172719"},
                {"type": "ISBN_10", "identifier": "0441172717"},
            ]
        }
        assert normalize_volume_info(info)["isbn_13"] == "9780441172719"
        assert normalize_volume_info(info)["isbn_10"] == "0441172717"

    def test_authors_extracted_as_list(self):
        info = {"authors": ["Frank Herbert", "Willis McNelly"]}
        assert normalize_volume_info(info)["authors"] == ["Frank Herbert", "Willis McNelly"]

    def test_cover_image_prefers_large_over_thumbnail(self):
        info = {
            "imageLinks": {
                "thumbnail": "http://books.google.com/thumb",
                "large": "http://books.google.com/large",
            }
        }
        assert normalize_volume_info(info)["cover_image_url"] == "http://books.google.com/large"

    def test_cover_image_falls_back_to_thumbnail(self):
        info = {"imageLinks": {"thumbnail": "http://books.google.com/thumb"}}
        assert normalize_volume_info(info)["cover_image_url"] == "http://books.google.com/thumb"


class TestIsbnNormalizerMissingFields:

    def test_missing_title_returns_none(self):
        assert normalize_volume_info({})["title"] is None

    def test_missing_isbn_returns_none(self):
        result = normalize_volume_info({})
        assert result["isbn_13"] is None
        assert result["isbn_10"] is None

    def test_missing_authors_returns_empty_list(self):
        assert normalize_volume_info({})["authors"] == []

    def test_missing_cover_returns_none(self):
        assert normalize_volume_info({})["cover_image_url"] is None

    def test_missing_date_returns_none(self):
        assert normalize_volume_info({})["publication_date"] is None


class TestPublicationDateNormalization:

    def _date(self, raw):
        return normalize_volume_info({"publishedDate": raw})["publication_date"]

    def test_year_only(self):
        assert self._date("2018") == "2018-01-01"

    def test_year_month(self):
        assert self._date("2018-03") == "2018-03-01"

    def test_full_date_unchanged(self):
        assert self._date("2018-03-15") == "2018-03-15"

    def test_unparseable_returns_none(self):
        assert self._date("not-a-date") is None

    def test_empty_string_returns_none(self):
        assert self._date("") is None

    def test_zero_padded_month_and_day(self):
        assert self._date("2005-06-07") == "2005-06-07"


# ─────────────────────────────────────────────────────────────────────────────
# isbn_lookup utility
# ─────────────────────────────────────────────────────────────────────────────

class TestIsbnLookupUtil:

    @patch("bookapp.utils.isbn_lookup.requests.get")
    def test_happy_path_returns_volume_info(self, mock_get):
        mock_get.return_value = _mock_response(json_body=_google_books_response())
        result = IsbnLookup().fetch("9780441172719")
        assert result["title"] == "Dune"

    @patch("bookapp.utils.isbn_lookup.requests.get")
    def test_hyphens_stripped_from_isbn(self, mock_get):
        mock_get.return_value = _mock_response(json_body=_google_books_response())
        IsbnLookup().fetch("978-0-441-17271-9")
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["q"] == "isbn:9780441172719"

    @patch("bookapp.utils.isbn_lookup.requests.get")
    def test_no_results_raises(self, mock_get):
        mock_get.return_value = _mock_response(json_body={"totalItems": 0})
        with pytest.raises(IsbnLookupError, match="No results"):
            IsbnLookup().fetch("0000000000000")

    @patch("bookapp.utils.isbn_lookup.requests.get")
    def test_http_error_raises(self, mock_get):
        mock_get.return_value = _mock_response(status_code=500)
        with pytest.raises(IsbnLookupError, match="HTTP 500"):
            IsbnLookup().fetch("9780441172719")

    @patch("bookapp.utils.isbn_lookup.requests.get")
    def test_network_error_raises(self, mock_get):
        mock_get.side_effect = req.ConnectionError("refused")
        with pytest.raises(IsbnLookupError, match="Network error"):
            IsbnLookup().fetch("9780441172719")

    @patch("bookapp.utils.isbn_lookup.requests.get")
    def test_timeout_raises(self, mock_get):
        mock_get.side_effect = req.Timeout("timed out")
        with pytest.raises(IsbnLookupError, match="Network error"):
            IsbnLookup().fetch("9780441172719")

    @patch("bookapp.utils.isbn_lookup.requests.get")
    def test_invalid_json_raises(self, mock_get):
        mock = MagicMock()
        mock.ok = True
        mock.json.side_effect = ValueError("bad json")
        mock_get.return_value = mock
        with pytest.raises(IsbnLookupError, match="Invalid JSON"):
            IsbnLookup().fetch("9780441172719")


# ─────────────────────────────────────────────────────────────────────────────
# author_matcher
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAuthorMatcher:

    def _author(self, name):
        return Author.objects.create(name=name)

    def test_exact_match(self):
        author = self._author("Frank Herbert")
        result = match_author("Frank Herbert", Author.objects.all())
        assert result["author_id"] == author.id
        assert result["match_type"] == "exact"
        assert result["confidence"] == 100

    def test_normalized_exact_last_first(self):
        """'Herbert, Frank' should normalize-match 'Frank Herbert'."""
        author = self._author("Frank Herbert")
        result = match_author("Herbert, Frank", Author.objects.all())
        assert result["author_id"] == author.id
        assert result["match_type"] == "exact"

    def test_fuzzy_match_close_name(self):
        """A name with a small typo should still match via fuzzy."""
        author = self._author("Aldous Huxley")
        result = match_author("Aldous Huxly", Author.objects.all())
        assert result is not None
        assert result["author_id"] == author.id
        assert result["match_type"] == "fuzzy"
        assert result["confidence"] >= FUZZY_MATCH_THRESHOLD

    def test_no_match_below_threshold(self):
        self._author("Frank Herbert")
        result = match_author("J. K. Rowling", Author.objects.all())
        assert result is None

    def test_empty_candidates_returns_none(self):
        result = match_author("Frank Herbert", Author.objects.none())
        assert result is None

    def test_picks_best_match_among_multiple_authors(self):
        self._author("Isaac Newton")
        target = self._author("Isaac Asimov")
        result = match_author("Isaac Asimov", Author.objects.all())
        assert result["author_id"] == target.id

    def test_result_contains_expected_keys(self):
        author = self._author("Ursula K. Le Guin")
        result = match_author("Ursula K. Le Guin", Author.objects.all())
        assert set(result.keys()) == {"author_id", "name", "confidence", "match_type"}
        assert result["name"] == author.name


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/books/isbn-lookup/
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestIsbnLookupView:

    def test_missing_isbn_param_returns_400(self, authed_client):
        response = authed_client.get("/api/books/isbn-lookup/")
        assert response.status_code == 400
        assert "error" in response.data

    @patch("bookapp.utils.isbn_lookup.requests.get")
    def test_lookup_error_returns_400(self, mock_get, authed_client):
        mock_get.return_value = _mock_response(json_body={"totalItems": 0})
        response = authed_client.get("/api/books/isbn-lookup/?isbn=0000000000000")
        assert response.status_code == 400
        assert "error" in response.data

    @patch("bookapp.utils.isbn_lookup.requests.get")
    def test_happy_path_returns_normalized_data(self, mock_get, authed_client):
        mock_get.return_value = _mock_response(json_body=_google_books_response())
        response = authed_client.get("/api/books/isbn-lookup/?isbn=9780441172719")
        assert response.status_code == 200
        data = response.data
        assert data["title"] == "Dune"
        assert data["isbn_13"] == "9780441172719"
        assert data["isbn_10"] == "0441172717"
        assert data["publication_date"] == "1990-09-01"
        assert "author_match" in data

    @patch("bookapp.utils.isbn_lookup.requests.get")
    def test_author_match_populated_when_author_exists(self, mock_get, authed_client):
        Author.objects.create(name="Frank Herbert")
        mock_get.return_value = _mock_response(json_body=_google_books_response())
        response = authed_client.get("/api/books/isbn-lookup/?isbn=9780441172719")
        assert response.status_code == 200
        assert response.data["author_match"] is not None
        assert response.data["author_match"]["name"] == "Frank Herbert"

    @patch("bookapp.utils.isbn_lookup.requests.get")
    def test_author_match_null_when_no_authors_in_db(self, mock_get, authed_client):
        mock_get.return_value = _mock_response(json_body=_google_books_response())
        response = authed_client.get("/api/books/isbn-lookup/?isbn=9780441172719")
        assert response.status_code == 200
        assert response.data["author_match"] is None


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/books/isbn-lookup/cover/
# ─────────────────────────────────────────────────────────────────────────────

class TestIsbnCoverProxyView:

    def test_missing_url_returns_400(self, api_client):
        response = api_client.get("/api/books/isbn-lookup/cover/")
        assert response.status_code == 400

    def test_disallowed_host_returns_400(self, api_client):
        response = api_client.get(
            "/api/books/isbn-lookup/cover/?url=http://evil.com/image.jpg"
        )
        assert response.status_code == 400
        assert "error" in response.data

    @patch("bookapp.views.isbn_cover_proxy.requests.get")
    def test_upstream_error_returns_502(self, mock_get, api_client):
        mock_get.return_value = _mock_response(status_code=404)
        url = "http://books.google.com/books/content?id=abc"
        response = api_client.get(
            f"/api/books/isbn-lookup/cover/?url={url}"
        )
        assert response.status_code == 502

    @patch("bookapp.views.isbn_cover_proxy.requests.get")
    def test_network_error_returns_502(self, mock_get, api_client):
        mock_get.side_effect = req.ConnectionError("refused")
        url = "http://books.google.com/books/content?id=abc"
        response = api_client.get(
            f"/api/books/isbn-lookup/cover/?url={url}"
        )
        assert response.status_code == 502

    @patch("bookapp.views.isbn_cover_proxy.requests.get")
    def test_happy_path_streams_image(self, mock_get, api_client):
        image_bytes = b"\xff\xd8\xff"  # JPEG magic bytes
        mock_get.return_value = _mock_response(
            content=image_bytes, content_type="image/jpeg"
        )
        url = "http://books.google.com/books/content?id=abc"
        response = api_client.get(
            f"/api/books/isbn-lookup/cover/?url={url}"
        )
        assert response.status_code == 200
        assert response["Content-Type"] == "image/jpeg"


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/books/download-cover/
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCoverImageDownloadView:

    GOOGLE_URL = "http://books.google.com/books/content?id=abc"

    def test_unauthenticated_returns_403(self, api_client):
        response = api_client.post(
            "/api/books/download-cover/", {"url": self.GOOGLE_URL}, format="json"
        )
        assert response.status_code == 403

    def test_missing_url_returns_400(self, authed_client):
        response = authed_client.post("/api/books/download-cover/", {}, format="json")
        assert response.status_code == 400
        assert "error" in response.data

    def test_disallowed_host_returns_400(self, authed_client):
        response = authed_client.post(
            "/api/books/download-cover/",
            {"url": "http://evil.com/image.jpg"},
            format="json",
        )
        assert response.status_code == 400

    @patch("bookapp.views.cover_download.requests.get")
    def test_upstream_error_returns_502(self, mock_get, authed_client):
        mock_get.return_value = _mock_response(status_code=500)
        response = authed_client.post(
            "/api/books/download-cover/", {"url": self.GOOGLE_URL}, format="json"
        )
        assert response.status_code == 502

    @patch("bookapp.views.cover_download.requests.get")
    def test_unsupported_content_type_returns_400(self, mock_get, authed_client):
        mock_get.return_value = _mock_response(
            content=b"data", content_type="text/html"
        )
        response = authed_client.post(
            "/api/books/download-cover/", {"url": self.GOOGLE_URL}, format="json"
        )
        assert response.status_code == 400
        assert "Unsupported image type" in response.data["error"]

    @patch("builtins.open", mock_open())
    @patch("bookapp.views.cover_download.os.makedirs")
    @patch("bookapp.views.cover_download.requests.get")
    def test_happy_path_returns_cover_image_path(self, mock_get, mock_makedirs, authed_client):
        mock_get.return_value = _mock_response(
            content=b"\xff\xd8\xff", content_type="image/jpeg"
        )
        response = authed_client.post(
            "/api/books/download-cover/", {"url": self.GOOGLE_URL}, format="json"
        )
        assert response.status_code == 201
        path = response.data["cover_image_path"]
        assert path.startswith("/static/img/covers/")
        assert path.endswith(".jpg")

    @patch("builtins.open", mock_open())
    @patch("bookapp.views.cover_download.os.makedirs")
    @patch("bookapp.views.cover_download.requests.get")
    def test_happy_path_calls_makedirs(self, mock_get, mock_makedirs, authed_client):
        mock_get.return_value = _mock_response(
            content=b"\xff\xd8\xff", content_type="image/jpeg"
        )
        authed_client.post(
            "/api/books/download-cover/", {"url": self.GOOGLE_URL}, format="json"
        )
        mock_makedirs.assert_called_once()
