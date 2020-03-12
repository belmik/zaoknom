from django.core.exceptions import ObjectDoesNotExist
from django.forms import (
    CharField,
    CheckboxInput,
    ChoiceField,
    DateField,
    DecimalField,
    Form,
    HiddenInput,
    IntegerField,
    ModelChoiceField,
    ModelForm,
    Textarea,
    TextInput,
)

from docbox.models import Address, Client, Mounter, Order, Price, Provider, Transaction
from docbox.validators import validate_phone


class DocboxFormMixin(object):
    error_css_class = "is-invalid"
    required_css_class = "required"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_html_attributes()

    def update_html_attributes(self):
        """ Update fields widget html attributes.

            add form-conrol to the class html attribute
            set autocomplete attruibute to off
            set placeholder attribute with value of label
        """

        for name, field in self.fields.items():
            attrs = {}
            # Only textarea doesn't have input_type attribute.
            input_type = getattr(field.widget, "input_type", "textarea")

            field_class = field.widget.attrs.get("class", "")
            field_class += " form-control"
            if input_type == "select":
                field_class += " custom-select"
            attrs.update({"class": field_class.strip()})

            if input_type in ["text", "tel"]:
                attrs.update({"autocomplete": "off"})

            if not field.widget.attrs.get("noplaceholder"):
                attrs.update({"placeholder": field.label})

            if isinstance(field, DateField):
                del attrs["placeholder"]

            field.widget.attrs.update(attrs)


class NewOrderForm(DocboxFormMixin, Form):
    name = CharField(
        label="Заказчик",
        max_length=64,
        error_messages={"required": "Пожалуйста, введите имя заказчика."},
        widget=TextInput({"class": "js-typeahead", "autofocus": True}),
    )
    phone = CharField(
        label="Телефон",
        max_length=10,
        required=False,
        widget=TextInput({"type": "tel"}),
        validators=[validate_phone],
    )
    town = CharField(label="Населенный пункт", max_length=64, required=False)
    street_type = ChoiceField(choices=Address.STREET_TYPES, initial="street", required=False)
    street = CharField(label="Название", max_length=64, required=False)
    building = CharField(label="д.", max_length=8, required=False)
    apartment = IntegerField(label="кв", min_value=0, required=False, widget=TextInput())
    total = DecimalField(
        label="Сумма",
        max_digits=10,
        decimal_places=0,
        error_messages={
            "required": "Введите сумму заказа.",
            "invalid": "Сумма должна состоять только из цифр.",
        },
        widget=TextInput({"class": "text-right"}),
    )
    advance_amount = DecimalField(
        label="Аванс",
        max_digits=10,
        decimal_places=0,
        required=False,
        widget=TextInput({"class": "text-right"}),
    )
    comment = CharField(
        label="Комментарий", max_length=1024, required=False, widget=Textarea({"rows": 3})
    )

    def save(self):
        data = self.cleaned_data
        client, created = Client.objects.get_or_create(name=data["name"], phone=data["phone"])

        address = Address.objects.create(
            town=data["town"],
            street_type=data["street_type"],
            street=data["street"],
            building=data["building"],
            apartment=data["apartment"],
        )

        price = Price.objects.create(total=data["total"])

        order = Order.objects.create(
            client=client, address=address, price=price, comment=data["comment"]
        )

        if data["advance_amount"]:
            Transaction.objects.get_or_create(
                amount=data["advance_amount"], client=client, order=order
            )


class EditOrderForm(NewOrderForm):

    date_created = DateField(
        label="Дата создания заказа",
        error_messages={
            "required": "Введите дату создания заказа",
            "invalid": "Дата должна быть в формате дд.мм.гггг",
        },
    )
    date_delivery = DateField(
        label="Дата доставки заказа",
        required=False,
        error_messages={"invalid": "Дата должна быть в формате дд.мм.гггг"},
    )
    date_mounting = DateField(
        label="Дата монтажа заказа",
        required=False,
        error_messages={"invalid": "Дата должна быть в формате дд.мм.гггг"},
    )
    provider_code = CharField(
        label="Номер заказа у поставщика", max_length=1024, required=False
    )
    status = ChoiceField(label="Статус", choices=Order.STATUS_CHOICES)
    provider_name = ModelChoiceField(
        label="Поставщик",
        queryset=Provider.objects.all(),
        required=False,
        to_field_name="name",
        empty_label="Поставщик",
    )
    category = ChoiceField(
        label="Тип заказа", choices=Order.ORDER_TYPE_CHOICES, required=False
    )
    mounter_name = ModelChoiceField(
        label="Монтажник",
        empty_label="Монтажник",
        queryset=Mounter.objects.all(),
        required=False,
        to_field_name="name",
    )
    mounting_price = DecimalField(
        label="Монтаж",
        min_value=0,
        max_digits=10,
        decimal_places=0,
        required=False,
        error_messages={"invalid": "Цена монтажа должна состоять только из цифр."},
        widget=TextInput({"class": "text-right"}),
    )
    delivery_price = DecimalField(
        label="Доставка",
        min_value=0,
        max_digits=10,
        decimal_places=0,
        required=False,
        error_messages={"invalid": "Цена доставки должна состоять только из цифр."},
        widget=TextInput({"class": "text-right"}),
    )

    address_info = CharField(
        label="Дополнительная информация",
        max_length=1024,
        required=False,
        widget=Textarea({"rows": 3}),
    )

    def save(self, order):
        self.order = order

        for changed_field in self.changed_data:
            if hasattr(self.order, changed_field):
                setattr(self.order, changed_field, self.cleaned_data[changed_field])

        self.change_or_update_client()
        self.update_price()
        self.update_address()

        if "provider_name" in self.changed_data:
            try:
                self.order.provider = Provider.objects.get(
                    name=self.cleaned_data["provider_name"]
                )
            except Provider.DoesNotExist:
                pass

        if "mounter_name" in self.changed_data:
            try:
                self.order.mounter = Mounter.objects.get(
                    name__name=self.cleaned_data["mounter_name"]
                )
            except Mounter.DoesNotExist:
                pass

        self.order.save()

    def change_or_update_client(self):
        """
        Change client to another or just update his phone.

        This form can only change user to another from db or change the phone of existing user.
        Because if user changed name in the form and this name not in the db it's imposible
        to know what user trying to do.
        """
        if "name" not in self.changed_data and "phone" not in self.changed_data:
            return

        try:
            client = Client.objects.get(
                name=self.cleaned_data["name"], phone=self.cleaned_data["phone"]
            )
        except ObjectDoesNotExist:
            if self.order.client.name == self.cleaned_data["name"]:
                self.order.client.phone = self.cleaned_data["phone"]
                self.order.client.save()
                return
        else:
            self.order.client = client
            return

    def update_price(self):
        """ Update prices if they changed, then save Price model. """

        price_changed = False
        if "total" in self.changed_data:
            self.order.price.total = self.cleaned_data["total"]
            price_changed = True

        if "delivery_price" in self.changed_data:
            self.order.price.delivery = self.cleaned_data["delivery_price"]
            price_changed = True

        if "mounting_price" in self.changed_data:
            self.order.price.mounting = self.cleaned_data["mounting_price"]
            price_changed = True

        if price_changed:
            self.order.price.save()

    def update_address(self):
        """ Update address if it changed, then save Address model. """

        address = self.order.address or Address()
        address_changed = False
        for changed_field in self.changed_data:
            if hasattr(address, changed_field):
                setattr(address, changed_field, self.cleaned_data[changed_field])
                address_changed = True

        if address_changed:
            address.save()


class NewTransactionForm(DocboxFormMixin, ModelForm):
    class Meta:
        model = Transaction
        fields = ["amount", "date", "comment", "order", "client", "cashbox"]
        widgets = {
            "amount": TextInput(
                {"class": "text-right", "noplaceholder": "on", "autofocus": True}
            ),
            "comment": Textarea({"rows": "3"}),
            "order": HiddenInput(),
            "client": HiddenInput(),
            "cashbox": CheckboxInput({"class": "custom-control-input"}),
        }


class EditClientForm(DocboxFormMixin, ModelForm):
    class Meta:
        model = Client
        fields = ["name", "phone", "info"]
        widgets = {
            "info": Textarea({"rows": "3"}),
        }


class BookkeepingEditOrderForm(DocboxFormMixin, ModelForm):
    class Meta:
        model = Price
        fields = ["provider"]
        labels = {
            "provider": "0",
        }
        widgets = {
            "provider": TextInput({"class": "text-right", "autofocus": True}),
        }
