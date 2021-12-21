import os

from django.test import override_settings
from django.urls import reverse

from docbox.models import ProviderOrder

from .base import BaseTestCase

DOCBOX_TOKEN = f"Bearer {os.getenv('API_TOKEN')}"


class BulkUpdateProviderOrderCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse("docbox-api:bulk-update-provider-order")
        self.order1 = ProviderOrder.objects.create(order=self.order, provider=self.provider, code="322001", price=2000)
        self.order2 = ProviderOrder.objects.create(order=self.order, provider=self.provider, code="322002", price=3000)
        self.order3 = ProviderOrder.objects.create(order=self.order, provider=self.provider, code="322003", price=4000)

    @override_settings(TELEGRAM_SEND_MESSAGE_URL="")
    def test_bulk_udate(self):
        data = {
            self.order1.code: {"delivery_date": "2021-07-11"},
            self.order2.code: {"status": "in_production"},
            self.order3.code: {"delivery_date": "2021-06-19", "status": "in_production"},
        }
        self.client.post(self.url, data=data, content_type="application/json", HTTP_Authorization=DOCBOX_TOKEN)
        self.order1.refresh_from_db()
        self.order2.refresh_from_db()
        self.order3.refresh_from_db()
        updated_data = {
            self.order1.code: {"delivery_date": self.order1.delivery_date.isoformat()},
            self.order2.code: {"status": self.order2.status},
            self.order3.code: {"delivery_date": self.order3.delivery_date.isoformat(), "status": self.order3.status},
        }
        self.assertDictEqual(data, updated_data)
