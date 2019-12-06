from django.test import TestCase

from docbox.models import Client, Order, Price, Transaction


class OrderModelTestCase(TestCase):
    def setUp(self):
        self.buyer = Client.objects.create(name="Заказчик")
        self.price = Price.objects.create(total=5000)
        self.order = Order.objects.create(client=self.buyer, price=self.price)
        return super().setUp()

    def test_remaining_calculation(self):
        Transaction.objects.bulk_create(
            [
                Transaction(amount="2000", order=self.order, client=self.buyer),
                Transaction(amount="1500", order=self.order, client=self.buyer),
            ]
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.remaining, 1500)

    def test_remaining_with_no_transactions(self):
        self.assertEqual(self.order.remaining, 5000)

    def test_remaining_with_fully_paid_order(self):
        Transaction.objects.bulk_create(
            [
                Transaction(amount="2000", order=self.order, client=self.buyer),
                Transaction(amount="3000", order=self.order, client=self.buyer),
            ]
        )
        self.order.refresh_from_db()
        self.assertAlmostEqual(self.order.remaining, 0)

    def test_remaining_with_negative_value(self):
        Transaction.objects.bulk_create(
            [
                Transaction(amount="2000", order=self.order, client=self.buyer),
                Transaction(amount="3500", order=self.order, client=self.buyer),
            ]
        )
        self.order.refresh_from_db()
        self.assertAlmostEqual(self.order.remaining, -500)
