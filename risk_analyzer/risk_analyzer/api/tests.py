import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from .models import Prediction


class RiskAnalyzerSecurityTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="analyst",
            password="strong-test-password"
        )
        self.client.force_login(self.user)

    def test_delete_account_requires_post(self):
        response = self.client.get(reverse("delete_account"))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_account_post_removes_user(self):
        response = self.client.post(reverse("delete_account"))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_profile_picture_requires_post(self):
        response = self.client.get(reverse("delete_profile_picture"))

        self.assertEqual(response.status_code, 405)

    def test_predict_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        response = csrf_client.post(
            reverse("predict_risk"),
            data=json.dumps({"text": "stable cash flow"}),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 403)

    @patch("api.views.predict_text_risk", return_value=("Low Risk", 91))
    def test_predict_saves_authenticated_prediction(self, mock_predict):
        response = self.client.post(
            reverse("predict_risk"),
            data=json.dumps({"text": "stable cash flow"}),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["prediction"], "Low Risk")
        self.assertEqual(
            Prediction.objects.filter(user=self.user).count(),
            1
        )
        mock_predict.assert_called_once_with("stable cash flow")

    def test_pdf_upload_rejects_non_pdf_extension(self):
        upload = SimpleUploadedFile(
            "notes.txt",
            b"not a pdf",
            content_type="text/plain"
        )

        response = self.client.post(
            reverse("upload_pdf"),
            data={"pdf": upload}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Only PDF files", response.json()["error"])

    @patch("api.views.get_stock_history")
    def test_market_search_returns_stock_data(self, mock_stock):
        mock_stock.return_value = {
            "symbol": "MSFT",
            "name": "Microsoft",
            "currency": "USD",
            "price": 420.12,
            "change": 3.4,
            "change_percent": 0.82,
            "points": [{"date": "Jan 01", "price": 420.12}],
        }

        response = self.client.get(
            reverse("market_search"),
            {"symbol": "MSFT"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["symbol"], "MSFT")
        mock_stock.assert_called_once_with("MSFT")

    @patch("api.views.get_top_company_snapshots")
    def test_market_top_returns_companies(self, mock_top):
        mock_top.return_value = [{
            "symbol": "NVDA",
            "name": "NVIDIA",
            "currency": "USD",
            "price": 100,
            "change": 5,
            "change_percent": 5,
            "points": [],
        }]

        response = self.client.get(reverse("market_top"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["companies"][0]["symbol"], "NVDA")

    @patch("api.views.get_finance_news")
    def test_news_returns_articles(self, mock_news):
        mock_news.return_value = [{
            "title": "Markets rally",
            "link": "https://example.com/story",
            "source": "Example",
            "published": "Today",
        }]

        response = self.client.get(
            reverse("market_news"),
            {"q": "markets"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["articles"][0]["title"], "Markets rally")
        mock_news.assert_called_once_with("markets")
