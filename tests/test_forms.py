from datetime import date, timedelta

from django.urls import reverse

from docbox.models import Client

from .base import BaseTestCase


class NewOrderFormTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.form_url = reverse("docbox:new-order")
        cls.valid_data = {
            "name": "Новый Заказчик",
            "phone": "0970000000",
            "town": "Шабо",
            "street_type": "street",
            "street": "Тестовая",
            "building": "111",
            "apartment": "11",
            "total": "5000",
            "advance_amount": "2000",
        }
        return super().setUpTestData()

    def test_redirect(self):
        r = self.client.post(self.form_url, data=self.valid_data)
        self.assertRedirects(r, reverse("docbox:orders-list"))

    def test_client_name_save(self):
        self.client.post(self.form_url, data=self.valid_data)
        r = self.client.get(reverse("docbox:orders-list"))
        self.assertContains(r, self.valid_data["name"])

    def test_client_phone_save(self):
        self.client.post(self.form_url, data=self.valid_data)
        r = self.client.get(reverse("docbox:orders-list"))
        self.assertContains(r, "(097) 000 0000")

    def test_town_save(self):
        self.client.post(self.form_url, data=self.valid_data)
        r = self.client.get(reverse("docbox:orders-list"))
        self.assertContains(r, self.valid_data["town"])

    def test_name_field_required(self):
        r = self.client.post(self.form_url, data={})
        self.assertFormError(r, "form", "name", "Пожалуйста, введите имя заказчика.")

    def test_total_field_required(self):
        r = self.client.post(self.form_url, data={})
        self.assertFormError(r, "form", "total", "Введите сумму заказа.")

    def test_total_field_invalid(self):
        r = self.client.post(self.form_url, data={"total": "200грн."})
        self.assertFormError(r, "form", "total", "Сумма должна состоять только из цифр.")

    def test_phone_field_error(self):
        r = self.client.post(self.form_url, data={"phone": "802000"})
        self.assertFormError(r, "form", "phone", "Номер должен состоять из десяти цифр.")


class EditOrderFormCase(BaseTestCase):
    def setUp(self):
        self.new_client = Client.objects.create(name="Новый заказчик", phone="0990000111")
        self.post_data = {
            "name": self.new_client.name,
            "phone": self.new_client.phone,
            "total": "5000",
            "date_created": "02.11.2019",
            "status": "finished",
        }
        return super().setUp()

    def test_valid_redirect(self):
        r = self.client.post(self.order.get_absolute_edit_url(), self.post_data)
        self.assertRedirects(r, reverse("docbox:orders-list"))

    def test_client_switch(self):
        self.client.post(self.order.get_absolute_edit_url(), self.post_data)
        self.order.refresh_from_db()
        self.assertEqual(self.order.client.name, self.new_client.name)

    def test_order_charfields(self):
        today = date.today()
        order_nonref_fields = {
            "date_created": today,
            "status": "finished",
            "category": "pvc",
            "date_delivery": today + timedelta(days=10),
            "date_mounting": today + timedelta(days=11),
        }
        self.post_data.update(order_nonref_fields)

        self.client.post(self.order.get_absolute_edit_url(), self.post_data)
        self.order.refresh_from_db()

        for key, value in order_nonref_fields.items():
            self.assertEqual(getattr(self.order, key), value)

    def test_order_price_change(self):
        price_fields = {
            "total": self.order.price.total + 1000,
            "mounting_price": self.order.price.mounting + 500,
            "delivery_price": self.order.price.delivery + 50,
        }
        self.post_data.update(price_fields)

        self.client.post(self.order.get_absolute_edit_url(), self.post_data)
        self.order.refresh_from_db()

        self.assertEqual(self.order.price.total, price_fields["total"])
        self.assertEqual(self.order.price.mounting, price_fields["mounting_price"])
        self.assertEqual(self.order.price.delivery, price_fields["delivery_price"])

    def test_order_address_change(self):
        address_fields = {
            "town": "Новый Тестовый город",
            "street": "Новая Тестовая",
            "building": "101",
            "apartment": 10,
        }
        self.post_data.update(address_fields)

        self.client.post(self.order.get_absolute_edit_url(), self.post_data)
        self.order.refresh_from_db()

        for key, value in address_fields.items():
            self.assertEqual(getattr(self.order.address, key), value)


class NewTransactionFormCase(BaseTestCase):
    def test_new_transaction_save(self):
        amount = 2000
        data = {
            "amount": amount,
            "date": date.today(),
            "client": self.order.client.pk,
            "comment": "тестовая транзакция",
            "order": self.order.pk,
        }
        url = reverse("docbox:new-transaction")
        self.client.post(url, data=data, follow=True)
        self.order.refresh_from_db()
        self.assertEqual(self.order.remaining, self.total_price - amount)


class NewTransactionForProviderFormCase(BaseTestCase):
    def test_new_transaction_provider_save(self):
        amount = 2000
        data = {
            "amount": amount,
            "date": date.today(),
            "provider": self.order.provider.pk,
        }
        url = reverse("docbox:new-transaction")
        self.client.post(url, data=data, follow=True)
        self.order.refresh_from_db()
        self.assertEqual(self.order.provider.transaction_set.first().amount, amount)


class NewProviderFormCase(BaseTestCase):
    def test_new_provider_save(self):
        provider_name = "Новый поставщик"
        data = {
            "name": provider_name,
        }
        url = reverse("docbox:new-provider")
        r = self.client.post(url, data=data, follow=True)
        self.assertContains(r, provider_name)


class NewProviderOrderFormCase(BaseTestCase):
    def test_new_transaction_save(self):
        provider_code = "123456"
        data = {
            "order": self.order.pk,
            "provider": self.provider.pk,
            "code": provider_code,
            "price": 1000,
            "order_content": "два изделия",
        }
        url = reverse("docbox:new-provider-order", args=[self.order.pk])
        self.client.post(url, data=data, follow=True)
        self.order.refresh_from_db()
        self.assertEqual(self.order.provider_orders_str, provider_code)
