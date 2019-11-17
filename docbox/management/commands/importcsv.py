from pathlib import Path
from pprint import pprint
import csv

from django.core.management.base import BaseCommand, CommandError
from docbox.models import Client, Mounter, Provider, Address, Price, Transaction, Order
from ._order import OrderData


class Command(BaseCommand):
    help = "Imports orders from .csv file"
    missing_args_message = "Missing path to csv file."
    orders = []

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        self.read_csv_file(options["file"])

        for order in self.orders:
            if not order.valid:
                print(f"Order {order} is invalid. Skiping.")
                continue

            try:
                order.clean()
            except ValueError:
                print(f"Order {order} can't be cleaned. Skiping.")
                continue

            self.save_order(order)

    def read_csv_file(self, csv_file: str) -> list:
        """ Read `csv_file` and return list of Order instances."""
        csv_path = Path(csv_file).expanduser()

        if csv_path.suffix != ".csv":
            raise AttributeError("Expected csv file.")

        with csv_path.open(newline="") as csvfile:
            orders = [OrderData(*line) for line in csv.reader(csvfile)]

        self.orders = orders

    def save_order(self, order):
        """ Saves cleaned order to the database. """

        order_defaults = {}
        client, created = Client.objects.get_or_create(name=order.client, phone=order.phone)

        if order.mounter:
            try:
                mounter = Mounter.objects.get(name__name=order.mounter)
            except Mounter.DoesNotExist:
                client_and_mounter, created = Client.objects.get_or_create(name=order.mounter)
                mounter = Mounter.objects.create(name=client_and_mounter)

        if order.address:
            address, created = Address.objects.get_or_create(info=order.address)

        try:
            new_order = Order.objects.get(
                date_created=order.date_created,
                client=client,
                provider_code=order.provider_code,
            )
        except Order.DoesNotExist:
            price = Price.objects.create(
                total=order.total_price, mounting=order.mounting_price
            )
            new_order = Order(
                date_created=order.date_created,
                client=client,
                provider_code=order.provider_code,
                price=price,
                status=order.status,
            )
            if order.address:
                new_order.address = address

            if order.mounter:
                new_order.mounter = mounter
            new_order.save()
        for transaction in order.transactions:
            Transaction.objects.get_or_create(
                amount=transaction[0], date=transaction[1], client=client, order=new_order
            )
