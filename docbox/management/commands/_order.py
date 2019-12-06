import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class OrderData:
    """
    Takes fields from csv file and prepares them for saving in django db.
    Attributes fields should map to the fields in csv file.
    """

    date_created: date
    provider_code: str
    status: str
    client: str
    address: str
    phone: str
    mounter: str
    mounting_price: Decimal
    products_price: Decimal
    transaction0_amount: Decimal
    transaction0_date: date
    transaction1_amount: Decimal
    transaction1_date: date
    transaction2_amount: Decimal
    transaction2_date: date
    rest: Decimal
    transactions: list = field(default_factory=list)

    @property
    def valid(self) -> bool:
        """ Checks some cases were order should be skiped. """
        if not self.client or self.client == "Заказчик":
            return False

        if not self.status:
            return False

        if "долг" in self.provider_code:
            return False

        if not self.products_price:
            return False

        return True

    @property
    def total_price(self) -> Decimal:
        return self.mounting_price + self.products_price

    def clean(self):
        """ Performs type conversion for the order attributes """
        self.normalize_dates()
        self.normalize_prices()
        self.normalize_phone()
        self.normalize_transactions()
        self.normalize_status()

    def normalize_dates(self):
        self.date_created = self.str_to_date(self.date_created)
        self.transaction0_date = self.str_to_date(self.transaction0_date)
        self.transaction1_date = self.str_to_date(self.transaction1_date)
        self.transaction2_date = self.str_to_date(self.transaction2_date)

    def normalize_prices(self):
        self.mounting_price = self.str_to_decimal(self.mounting_price)
        self.products_price = self.str_to_decimal(self.products_price)
        self.transaction0_amount = self.str_to_decimal(self.transaction0_amount)
        self.transaction1_amount = self.str_to_decimal(self.transaction1_amount)
        self.transaction2_amount = self.str_to_decimal(self.transaction2_amount)
        self.rest = self.str_to_decimal(self.rest)

    def normalize_phone(self):
        if self.phone:
            self.phone = re.sub(r"\s*?", "", self.phone).rjust(10, "0")

    def normalize_transactions(self):
        transactions = [
            (self.transaction0_amount, self.transaction0_date),
            (self.transaction1_amount, self.transaction1_date),
            (self.transaction2_amount, self.transaction2_date),
        ]

        if self.transactions:
            return

        for transaction in transactions:
            amount, t_date = transaction
            if not t_date:
                t_date = self.date_created

            if amount:
                self.transactions.append((amount, t_date))

    def normalize_status(self):
        status_whitelist = ["Прогресс", "Гуцан"]
        new_status = ""

        if self.status == "TRUE":
            new_status = "delivered"

        if self.status == "FALSE":
            new_status = "in_production"

        if self.status == "TRUE" and self.rest <= 0:
            new_status = "finished"

        if self.status == "TRUE" and self.client in status_whitelist:
            new_status = "finished"

        self.status = new_status

    def str_to_date(self, str_date: str) -> date:
        """ If str_date is not empty convert to date obj and return it."""
        if not str_date:
            return ""

        date_parts = str_date.split(".")
        date_parts.reverse()

        try:
            date_obj = date(*list(map(int, date_parts)))
        except ValueError:
            exit(f"Can't convert {str_date} to the date obj.")

        return date_obj

    def str_to_decimal(self, str_decimal: str) -> Decimal:
        """ If str_decimal is not empty convert to Decimal obj and return it."""
        str_decimal = re.sub(r"\s*?", "", str_decimal)
        if not str_decimal:
            return Decimal(0)

        try:
            decimal_obj = Decimal(str_decimal)
        except ValueError:
            exit(f"Can't convert {str_decimal} to the Decimal obj.")
        return decimal_obj

    def __repr__(self):
        """ Returns order string representation. """
        return f"[{self.date_created}, {self.client}, {self.products_price}]"
