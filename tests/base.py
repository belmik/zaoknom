import os
from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.timezone import make_aware

from docbox.models import Address, Client, Mounter, Order, Price, Provider


class BaseTestCase(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user("test_user", password="test_password")
        self.test_user.save()
        self.client.force_login(self.test_user)

        self.total_price = 5000
        self.provider = Provider.objects.create(name=os.getenv("DEFAULT_PROVIDER", "Тестовый поставщик"))
        client = Client.objects.create(name="Тестовый Заказчик", phone="0990000111")
        client_mounter = Client.objects.create(name="Тестовый монтажник")
        mounter = Mounter.objects.create(name=client_mounter)
        price = Price.objects.create(total=self.total_price, added_expenses=3500, delivery=100, mounting=400)
        address = Address.objects.create(town="Тестовый город", street="Тестовая", building="10", apartment="1")

        self.order = Order.objects.create(
            date_created=make_aware(datetime(2019, 11, 11)),
            client=client,
            price=price,
            address=address,
            mounter=mounter,
            provider=self.provider,
            provider_code="1111,1112",
            status="finished",
            category="pvc",
            date_changed=make_aware(datetime(2019, 10, 1)),
            date_delivery=make_aware(datetime(2019, 10, 10)),
            date_mounting=make_aware(datetime(2019, 10, 11)),
            date_finished=make_aware(datetime(2019, 10, 12)),
        )
