import csv
from datetime import date, datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.urls import resolve, reverse, reverse_lazy
from django.utils import formats
from django.views.generic import (
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from docbox.forms import (
    BookkeepingEditOrderForm,
    EditClientForm,
    EditOrderForm,
    NewOrderForm,
    NewTransactionForm,
)
from docbox.models import Client, Order, Transaction


class DocboxFormViewBase(FormView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.add_error_classes(context)
        return context

    def add_error_classes(self, context):
        """ Add error class to the form fields. """
        form = context["form"]
        if not getattr(form, "errors", False):
            return

        for bound_field in form:
            if not getattr(bound_field, "errors", False):
                continue
            attrs = bound_field.field.widget.attrs
            field_class = attrs.get("class", "")
            field_class += f" {form.error_css_class}"
            attrs.update({"class": field_class.strip()})


class ZaoknomView(TemplateView):
    template_name = "zaoknom/index.html"


class HomeView(LoginRequiredMixin, ListView):
    template_name = "docbox/home.html"
    model = Order

    def get_queryset(self):
        return super().get_queryset().exclude(status="finished")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["transactions"] = Transaction.objects.all().order_by("-date")[:25]
        return context


class ClientsList(LoginRequiredMixin, ListView):
    template_name = "docbox/clients-list.html"
    model = Client


class ClientDetail(LoginRequiredMixin, DetailView):
    template_name = "docbox/client-detail.html"
    model = Client

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        TransactionsFormSet = modelformset_factory(Transaction, form=NewTransactionForm)
        formset = TransactionsFormSet(
            queryset=self.object.transactions.order_by("-date")[:5],
            initial=[{"client": self.object.pk}],
        )

        # It's not possible to rearange only initial forms in queryset, so I did this.
        forms = list(reversed(formset.forms[:-1]))
        forms.append(formset.forms[-1])
        formset.forms = forms
        context["formset"] = formset
        return context


class EditClient(LoginRequiredMixin, DocboxFormViewBase, UpdateView):
    template_name = "docbox/edit-client.html"
    form_class = EditClientForm
    model = Client

    def get_success_url(self):
        return reverse("docbox:client-detail", args=[self.object.pk])


class OrdersList(LoginRequiredMixin, ListView):
    template_name = "docbox/orders-list.html"
    model = Order
    paginate_by = 50

    date_format = formats.get_format_lazy("DATE_INPUT_FORMATS")[0]

    def post(self, request, *args, **kwargs):
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        start_date = datetime.strptime(start_date, self.date_format)
        end_date = datetime.strptime(end_date, self.date_format)

        request.session["start_date"] = start_date.strftime(self.date_format)
        request.session["end_date"] = end_date.strftime(self.date_format)

        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        today = date.today()
        quarter = timedelta(weeks=13)
        def_strat_date = (today - quarter).replace(day=1)
        def_strat_date = def_strat_date.strftime(self.date_format)
        def_end_date = date(today.year + 1, 1, 1).strftime(self.date_format)
        self.start_date = request.session.get("start_date", def_strat_date)
        self.end_date = request.session.get("end_date", def_end_date)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["start_date"] = self.start_date
        context["end_date"] = self.end_date
        return context

    def get_queryset(self):
        start_date = datetime.strptime(self.start_date, self.date_format)
        end_date = datetime.strptime(self.end_date, self.date_format)

        queryset = super().get_queryset()
        queryset = queryset.filter(date_created__range=(start_date, end_date))
        return queryset


class OrderDetail(LoginRequiredMixin, DetailView):
    template_name = "docbox/order-detail.html"
    model = Order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        TransactionsFormSet = modelformset_factory(Transaction, form=NewTransactionForm)
        formset = TransactionsFormSet(
            queryset=self.object.transactions,
            initial=[{"order": self.object.pk, "client": self.object.client.pk}],
        )
        context["formset"] = formset
        return context


class NewTransaction(LoginRequiredMixin, FormView):
    template_name = "docbox/new-transaction.html"
    form_class = modelformset_factory(Transaction, form=NewTransactionForm)
    success_url = reverse_lazy("docbox:orders-list")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = False
        self.next = False

    def post(self, request, *args, **kwargs):

        self.next = self.request.POST.get("next", False)

        if self.next:
            match = resolve(self.next)
            if match.url_name == "order-detail":
                self.object = Order.objects.get(pk=match.kwargs["pk"])
            if match.url_name == "client-detail":
                self.object = Client.objects.get(pk=match.kwargs["pk"])

        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return self.next or str(self.success_url)

    def form_valid(self, formset):
        formset.save()
        return super().form_valid(formset)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.object:
            kwargs.update({"queryset": self.object.transactions})

        return kwargs

    def get_initial(self):
        if isinstance(self.object, Order):
            self.initial = [
                {"order": self.object.order_id, "client": self.object.client.client_id}
            ]
        if isinstance(self.object, Client):
            self.initial = [{"client": self.object.pk}]
        return super().get_initial()


class DeleteTransaction(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = "docbox/delete-transaction.html"
    success_url = "/"

    def get(self, request, *args, **kwargs):
        self.next = self.request.GET.get("next", False)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.next = self.request.POST.get("next", False)
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return self.next or str(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["info_fields"] = [
            self.get_field(self.object.client, "name"),
            self.get_field(self.object, "date"),
            self.get_field(self.object, "amount"),
            self.get_field(self.object, "order"),
        ]
        context["next"] = self.next
        return context

    def get_field(self, obj, field_name):
        value = getattr(obj, field_name)
        verbose_name = obj._meta.get_field(field_name).verbose_name
        return (verbose_name, value)


class NewOrder(LoginRequiredMixin, DocboxFormViewBase):
    template_name = "docbox/new-order.html"
    form_class = NewOrderForm
    initial = {"town": "Белгород-Днестровский"}
    success_url = reverse_lazy("docbox:orders-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clients_list"] = Client.objects.all()
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class EditOrder(LoginRequiredMixin, DocboxFormViewBase):
    template_name = "docbox/edit-order.html"
    form_class = EditOrderForm
    success_url = reverse_lazy("docbox:orders-list")

    def get(self, request, *args, **kwargs):
        order_pk = request.resolver_match.kwargs["pk"]
        self.order = Order.objects.get(order_id=order_pk)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        order_pk = request.resolver_match.kwargs["pk"]
        self.order = Order.objects.get(order_id=order_pk)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.save(self.order)
        return super().form_valid(form)

    def get_initial(self):
        data = {
            "name": self.order.client.name,
            "phone": self.order.client.phone,
            "total": self.order.price.total,
            "date_created": self.order.date_created,
            "date_delivery": getattr(self.order, "date_delivery", ""),
            "date_mounting": getattr(self.order, "date_mounting", ""),
            "provider_code": getattr(self.order, "provider_code", ""),
            "status": getattr(self.order, "status", ""),
            "provider_name": getattr(self.order.provider, "name", ""),
            "category": getattr(self.order, "category", ""),
            "mounter_name": getattr(self.order, "mounter", ""),
            "delivery_price": self.order.price.delivery,
            "mounting_price": self.order.price.mounting,
            "comment": self.order.comment,
        }

        if self.order.address:
            data.update(
                {
                    "town": self.order.address.town,
                    "street_type": self.order.address.street_type,
                    "street": self.order.address.street,
                    "building": self.order.address.building,
                    "apartment": self.order.address.apartment,
                    "address_info": self.order.address.address_info,
                }
            )
        return data.copy()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clients_list"] = Client.objects.all()
        context["transactions_sum"] = self.order.transactions_sum
        return context


class BookkeepingOrders(LoginRequiredMixin, ListView):
    template_name = "docbox/bookkeeping-orders.html"
    model = Order
    paginate_by = 50

    date_format = formats.get_format_lazy("DATE_INPUT_FORMATS")[0]

    def get(self, request, *args, **kwargs):
        today = date.today()
        quarter = timedelta(weeks=13)
        def_strat_date = (today - quarter).replace(day=1)
        def_strat_date = def_strat_date.strftime(self.date_format)
        def_end_date = date(today.year + 1, 1, 1).strftime(self.date_format)
        self.start_date = request.session.get("start_date", def_strat_date)
        self.end_date = request.session.get("end_date", def_end_date)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        start_date = datetime.strptime(start_date, self.date_format)
        end_date = datetime.strptime(end_date, self.date_format)

        request.session["start_date"] = start_date.strftime(self.date_format)
        request.session["end_date"] = end_date.strftime(self.date_format)

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["start_date"] = self.start_date
        context["end_date"] = self.end_date
        return context

    def get_queryset(self):
        start_date = datetime.strptime(self.start_date, self.date_format)
        end_date = datetime.strptime(self.end_date, self.date_format)

        queryset = super().get_queryset()
        queryset = queryset.filter(date_created__range=(start_date, end_date))
        return queryset


class BookkeepingEditOrder(LoginRequiredMixin, DocboxFormViewBase):
    template_name = "docbox/bookkeeping-edit-order.html"
    success_url = reverse_lazy("docbox:bookkeeping-orders")
    form_class = BookkeepingEditOrderForm

    def get(self, request, *args, **kwargs):
        order_pk = request.resolver_match.kwargs["pk"]
        self.order = Order.objects.get(order_id=order_pk)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        order_pk = request.resolver_match.kwargs["pk"]
        self.order = Order.objects.get(order_id=order_pk)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": self.order.price})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        return context


class CsvExport(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        today = date.today().strftime("%Y%m%d")
        filename = f"orders_{today}.csv"

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        for order in Order.objects.all():
            writer.writerow(order.data_for_csv)

        return response
