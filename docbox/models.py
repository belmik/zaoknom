from decimal import ROUND_HALF_UP
from uuid import uuid4

from django.db import models
from django.urls import reverse
from django.utils import timezone

from docbox.validators import validate_phone


class Client(models.Model):

    client_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(verbose_name="Имя", max_length=64)
    phone = models.CharField(verbose_name="Телефон", blank=True, max_length=10, validators=[validate_phone])
    info = models.TextField(verbose_name="Заметка", max_length=1024, blank=True)

    def __str__(self):
        phone = ""
        if self.phone:
            phone = f" ({self.phone[:3]}) {self.phone[3:6]} {self.phone[6:]}"
        return self.name + phone

    @property
    def transactions(self):
        return self.transaction_set.all()

    @property
    def last_orders(self):
        return self.client_orders.order_by("-date_created")[:15]

    @property
    def last_transactions(self):
        return self.transactions.order_by("-date")[:15]

    @property
    def transactions_sum(self):
        if self.transactions:
            return self.transactions.aggregate(models.Sum("amount"))["amount__sum"]
        return 0

    @property
    def orders_sum(self):
        if self.client_orders:
            return self.client_orders.aggregate(models.Sum("price__total"))["price__total__sum"]
        return 0

    @property
    def remaining(self):
        return self.orders_sum - self.transactions_sum

    @property
    def products_price(self):
        orders_price = self.client_orders.aggregate(sum=models.Sum("price__total"))["sum"]
        mounting_price = self.client_orders.aggregate(sum=models.Sum("price__mounting"))["sum"]
        delivery_price = self.client_orders.aggregate(sum=models.Sum("price__delivery"))["sum"]
        if mounting_price:
            orders_price -= mounting_price
        if delivery_price:
            orders_price -= delivery_price
        return orders_price

    @property
    def provider_orders_price(self):
        return self.client_orders.aggregate(sum=models.Sum("providerorder__price"))["sum"] or 0

    @property
    def orders_added_expenses_sum(self):
        return self.client_orders.aggregate(sum=models.Sum("price__added_expenses"))["sum"] or 0

    @property
    def expenses(self):
        return self.provider_orders_price + self.orders_added_expenses_sum

    @property
    def profit(self):
        if self.expenses:
            return self.products_price - self.expenses
        return 0

    @property
    def extra_charge(self):
        if self.profit:
            extra_charge_percents = self.profit / self.expenses * 100
            return extra_charge_percents.quantize(0, rounding=ROUND_HALF_UP)
        return 0

    def get_absolute_url(self):
        return reverse("docbox:client-detail", kwargs={"pk": self.pk})

    def get_absolute_edit_url(self):
        return reverse("docbox:client-edit", kwargs={"pk": self.pk})

    def natural_key(self):
        return (self.name, self.phone)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ["name"]
        unique_together = ["name", "phone"]


class Mounter(models.Model):

    mounter_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.ForeignKey("Client", verbose_name="Клиент", on_delete=models.CASCADE)
    info = models.TextField(verbose_name="Заметка", max_length=1024, blank=True)

    class Meta:
        verbose_name = "Монтажник"
        verbose_name_plural = "Монтажники"

    def __str__(self):
        return str(self.name)


class Provider(models.Model):

    provider_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(verbose_name="Название", max_length=64)

    def get_absolute_url(self):
        return reverse("docbox:provider-detail", kwargs={"pk": self.pk})

    def get_absolute_edit_url(self):
        return reverse("docbox:provider-edit", kwargs={"pk": self.pk})

    @property
    def deletable(self):
        if self.providerorder_set.count() or self.order_set.count() or self.transaction_set.count():
            return False
        return True

    @property
    def pk_str(self):
        return str(self.pk)

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"

    def __str__(self):
        return self.name


class Address(models.Model):
    STREET_TYPES = [
        ("lane", "пер."),
        ("street", "ул."),
        ("avenue", "п-т"),
        ("boulevard", "б-р"),
    ]

    address_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    town = models.CharField(verbose_name="Насел. пункт", max_length=64, default="Белгород-Днестровский")
    street_type = models.CharField(max_length=16, choices=STREET_TYPES, default="street", blank=True)
    street = models.CharField(verbose_name="Улица", max_length=64, blank=True)
    building = models.CharField(verbose_name="Дом", max_length=8, blank=True)
    apartment = models.PositiveIntegerField(verbose_name="Квартира", blank=True, null=True)
    address_info = models.TextField(verbose_name="Заметка", max_length=1024, blank=True)

    def __str__(self):
        address = self.town
        if self.street:
            address += f", {self.get_street_type_display()} {self.street}"
        if self.building:
            address += f", д. {self.building}"
        if self.apartment:
            address += f", кв. {self.apartment}"
        if self.address_info:
            address += f", {self.address_info}"

        return address

    class Meta:
        verbose_name = "Адрес"
        verbose_name_plural = "Адреса"


class Price(models.Model):
    price_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    total = models.DecimalField(verbose_name="Сумма заказа", max_digits=10, decimal_places=0)
    added_expenses = models.DecimalField(
        verbose_name="Дополнительные расходы",
        max_digits=10,
        decimal_places=0,
        blank=True,
        null=True,
    )
    delivery = models.DecimalField(verbose_name="Доставка", max_digits=10, decimal_places=0, blank=True, null=True)
    mounting = models.DecimalField(verbose_name="Монтаж", max_digits=10, decimal_places=0, blank=True, null=True)

    @property
    def products(self):
        products = self.total
        if self.mounting:
            products = products - self.mounting

        if self.delivery:
            products = products - self.delivery

        return products

    @property
    def provider_orders_price(self):
        provider_orders = self.order.providerorder_set
        if provider_orders.count() == 0:
            return 0
        return provider_orders.aggregate(models.Sum("price"))["price__sum"]

    @property
    def profit(self):
        if self.expenses:
            return self.products - self.expenses
        return 0

    @property
    def expenses(self):
        if self.added_expenses:
            return self.provider_orders_price + self.added_expenses
        return self.provider_orders_price

    @property
    def extra_charge(self):
        if self.profit:
            extra_charge_percents = self.profit / self.expenses * 100
            return extra_charge_percents.quantize(0, rounding=ROUND_HALF_UP)
        return 0

    class Meta:
        verbose_name = "Цена"
        verbose_name_plural = "цены"

    def __str__(self):
        return f"{str(self.total)} грн."


class Transaction(models.Model):
    transaction_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    amount = models.DecimalField(verbose_name="Сумма", max_digits=10, decimal_places=0)
    date = models.DateTimeField(verbose_name="Дата", default=timezone.now)
    client = models.ForeignKey("Client", verbose_name="Клиент", on_delete=models.PROTECT, blank=True, null=True)
    provider = models.ForeignKey("Provider", verbose_name="Поставщик", on_delete=models.PROTECT, blank=True, null=True)
    comment = models.TextField(verbose_name="Комментарий", max_length=1024, blank=True)
    order = models.ForeignKey("Order", verbose_name="Заказ", on_delete=models.PROTECT, blank=True, null=True)
    cashbox = models.BooleanField(verbose_name="Касса", null=True, default=True)

    def __str__(self):
        return f"{self.amount} грн."

    @property
    def data_for_csv(self):
        cashbox = "да" if self.cashbox else "нет"
        client = self.client.name if self.client else ""
        provider = self.provider.name if self.provider else ""
        order = self.order.provider_orders_str if self.order else ""

        data = {
            "Касса": cashbox,
            "Дата": self.date,
            "Сумма": self.amount,
            "Клиент": client,
            "Поставщик": provider,
            "Заказ": order,
            "Комментарий": self.comment,
        }

        return data

    def get_absolute_edit_url(self):
        return reverse("docbox:edit-transaction", kwargs={"pk": self.pk})

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
        ordering = ["-date"]


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "новый"
        WAITING_FOR_PAYMENT = "waiting_for_payment", "ожидает оплаты"
        IN_PRODUCTION = "in_production", "в работе"
        DELIVERED = "delivered", "доставлен"
        MOUNTED = "mounted", "установлен"
        FINISHED = "finished", "завершен"

    ORDER_TYPE_CHOICES = [
        ("pvc", "ПВХ изделия"),
        ("blinds", "шторы и жалюзи"),
        ("addons", "дополнения"),
        ("aluminum", "алюминий"),
        ("glass", "стеклопакеты"),
        ("steel_doors", "стальные двери"),
    ]

    order_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    date_created = models.DateTimeField(verbose_name="Дата оформления", default=timezone.now, null=True)
    client = models.ForeignKey("Client", related_name="client_orders", verbose_name="Клиент", on_delete=models.PROTECT)
    price = models.OneToOneField("Price", verbose_name="Цены", on_delete=models.CASCADE)
    address = models.ForeignKey("Address", verbose_name="Адрес", null=True, on_delete=models.PROTECT, blank=True)
    mounter = models.ForeignKey("Mounter", verbose_name="Монтажник", on_delete=models.PROTECT, blank=True, null=True)
    provider = models.ForeignKey(
        "Provider",
        verbose_name="Производитель",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    provider_code = models.CharField(verbose_name="Производственный номер", max_length=1024, blank=True, default="б/н")
    status = models.SlugField(verbose_name="Статус", choices=Status.choices, default="new", blank=True)
    category = models.SlugField(
        verbose_name="Категория",
        choices=ORDER_TYPE_CHOICES,
        default="pvc",
        blank=True,
        null=True,
    )
    comment = models.TextField(verbose_name="Комментарий", max_length=1024, blank=True, default="", null=True)
    date_changed = models.DateField(verbose_name="Изменен", auto_now=True, null=True)
    date_delivery = models.DateField(verbose_name="Дата доставки", blank=True, null=True)
    date_mounting = models.DateField(verbose_name="Дата монтажа", blank=True, null=True)
    date_finished = models.DateField(verbose_name="Дата закрытия заказа", blank=True, null=True)

    @property
    def remaining(self):
        if self.transactions_sum:
            return self.price.total - self.transactions_sum
        return self.price.total

    @property
    def transactions(self):
        return self.transaction_set.all().order_by("date")

    @property
    def transactions_sum(self):
        if self.transactions:
            return self.transactions.aggregate(models.Sum("amount"))["amount__sum"]
        return 0

    @property
    def data_for_csv(self):
        data = {
            "Дата создания": self.date_created,
            "Номера заводских заказов": self.provider_orders_str,
            "Статус": self.get_status_display(),
            "Клиент": self.client.name,
            "Адрес": self.address,
            "Телефон": (self.client.phone or ""),
            "Монтажник": getattr(self.mounter, "name", ""),
            "Сумма монтажа": (self.price.mounting or 0),
            "Цена без монтажа": self.price.total - (self.price.mounting or 0),
        }

        return data

    @property
    def bookkeeping_data_for_csv(self):
        data = {
            "Дата создания": self.date_created,
            "Номера заводских заказов": self.provider_orders_str,
            "Клиент": self.client.name,
            "Статус": self.get_status_display(),
            "Цена изделий": self.price.products,
            "Цена поставщика": self.price.provider_orders_price,
            "Дополнительные расходы": (self.price.added_expenses or 0),
            "Прибыль": self.price.profit,
            "Наценка": self.price.extra_charge,
        }

        return data

    @property
    def provider_orders(self):
        return self.providerorder_set.all()

    @property
    def provider_orders_str(self):
        if self.providerorder_set.count() == 0:
            return self.provider_code
        return ", ".join([provider_order.code for provider_order in self.provider_orders])

    @property
    def deletable(self):
        if self.provider_orders or self.transactions:
            return False
        return True

    def get_provider_orders_statuses(self):
        if not self.provider_orders:
            return False
        statuses = set()
        for provider_order in self.provider_orders:
            statuses.add(provider_order.status)
        return statuses

    def __str__(self):
        order = f"{self.client.name}"
        if hasattr(self, "price"):
            order += f"; {self.price.total}"
        if self.address:
            order += f"; {self.address}"
        return order

    def get_absolute_url(self):
        return reverse("docbox:order-detail", kwargs={"pk": self.pk})

    def get_absolute_edit_url(self):
        return reverse("docbox:order-edit", kwargs={"pk": self.pk})

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-date_created"]


class ProviderOrder(models.Model):
    provider_order_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Заказ")
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT, verbose_name="Поставщик")
    code = models.CharField(verbose_name="Номер заказа", max_length=16)
    price = models.DecimalField(verbose_name="Сумма заказа", max_digits=10, decimal_places=0, blank=True, default=0)
    order_content = models.TextField(verbose_name="Состав заказа", max_length=1024, blank=True, default="")
    creation_date = models.DateTimeField(verbose_name="Дата добавления", default=timezone.now)
    delivery_date = models.DateField(verbose_name="Дата доставки", blank=True, null=True)
    status = models.SlugField(verbose_name="Статус", choices=Order.Status.choices, default="new", blank=True)

    def __str__(self):
        return self.code

    def get_absolute_edit_url(self):
        return reverse("docbox:edit-provider-order", kwargs={"pk": self.pk})

    class Meta:
        verbose_name = "Заказ поставщика"
        verbose_name_plural = "Заказы поставщика"
        ordering = ["-creation_date"]
