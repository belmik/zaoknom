import csv
import logging
import os
from datetime import date, datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Sum
from django.db.models.query import Prefetch
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import HttpResponseNotFound
from django.shortcuts import redirect
from django.urls import resolve, reverse, reverse_lazy
from django.utils import formats
from django.utils.timezone import make_aware
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
    NewProviderOrderForm,
    NewTransactionForm,
    ProviderForm,
)
from docbox.models import Client, Order, Provider, ProviderOrder, Transaction

logger = logging.getLogger(__name__)
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", False)


class DocboxFormViewBase(FormView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.add_error_classes(context)
        return context

    def add_error_classes(self, context):
        """Add error class to the form fields."""
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


class DocboxListViewBase(ListView):
    paginate_by = 50

    date_format = formats.get_format_lazy("DATE_INPUT_FORMATS")[0]

    def post(self, request, *args, **kwargs):
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        start_date = datetime.strptime(start_date, self.date_format)
        end_date = datetime.strptime(end_date, self.date_format)

        request.session["start_date"] = start_date.strftime(self.date_format)
        request.session["end_date"] = end_date.strftime(self.date_format)

    def get(self, request, *args, **kwargs):
        today = date.today()
        quarter = timedelta(weeks=13)
        def_start_date = (today - quarter).replace(day=1)
        def_start_date = def_start_date.strftime(self.date_format)
        def_end_date = date(today.year + 1, 1, 1).strftime(self.date_format)

        start_date = request.session.get("start_date", def_start_date)
        end_date = request.session.get("end_date", def_end_date)

        self.start_date = make_aware(datetime.strptime(start_date, self.date_format))
        self.end_date = make_aware(datetime.strptime(end_date, self.date_format))

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["start_date"] = self.start_date.strftime(self.date_format)
        context["end_date"] = self.end_date.strftime(self.date_format)
        return context


class ZaoknomView(TemplateView):
    template_name = "zaoknom/index.html"


class ClientsList(LoginRequiredMixin, ListView):
    template_name = "docbox/clients-list.html"
    model = Client


class ClientDetail(LoginRequiredMixin, DetailView):
    template_name = "docbox/client-detail.html"
    model = Client

    def render_to_response(self, context, **response_kwargs):
        if not self.object.client_orders and not self.object.transactions:
            return redirect("docbox:delete-client", pk=self.object.pk)

        return super().render_to_response(context, **response_kwargs)


class EditClient(LoginRequiredMixin, DocboxFormViewBase, UpdateView):
    template_name = "docbox/edit-client.html"
    form_class = EditClientForm
    model = Client

    def get_success_url(self):
        return reverse("docbox:client-detail", args=[self.object.pk])


class DeleteClient(LoginRequiredMixin, DeleteView):
    template_name = "docbox/delete-client.html"
    model = Client
    success_url = "/docbox/orders"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.object.client_orders and not self.object.transactions:
            context["client_clean"] = True

        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.client_orders and not self.object.transactions:
            success_url = self.get_success_url()
            self.object.delete()
            return HttpResponseRedirect(success_url)

        return redirect("docbox:delete-client", pk=self.object.pk)


class ProvidersList(LoginRequiredMixin, ListView):
    template_name = "docbox/providers-list.html"
    model = Provider


class EditProvider(LoginRequiredMixin, DocboxFormViewBase, UpdateView):
    template_name = "docbox/edit-provider.html"
    form_class = ProviderForm
    model = Provider

    def get_success_url(self):
        return reverse("docbox:provider-detail", args=[self.object.pk])


class NewProvider(LoginRequiredMixin, DocboxFormViewBase):
    template_name = "docbox/new-provider.html"
    form_class = ProviderForm
    success_url = reverse_lazy("docbox:providers-list")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class DeleteProvider(LoginRequiredMixin, DeleteView):
    template_name = "docbox/delete-provider.html"
    model = Provider
    success_url = "/docbox/providers"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.deletable:
            success_url = self.get_success_url()
            self.object.delete()
            return HttpResponseRedirect(success_url)

        return redirect("docbox:delete-provider", pk=self.object.pk)


class NewProviderOrder(LoginRequiredMixin, DocboxFormViewBase):
    template_name = "docbox/new-provider-order.html"
    form_class = NewProviderOrderForm
    success_url = reverse_lazy("docbox:orders-list")

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.order = Order.objects.get(order_id=kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        context["providers_list"] = Provider.objects.all()
        context["default_provider_name"] = DEFAULT_PROVIDER
        return context

    def get_initial(self):
        initial_data = super().get_initial()
        initial_data.update({"order": self.order.pk})
        initial_data.update({"price": ""})

        default_provider = self.get_default_provider()
        if default_provider:
            initial_data.update({"provider": default_provider.pk})
        return initial_data

    def get_default_provider(self):
        """Loading default provider from environment option.
        This should be replased with proper setting in the UI"""

        if not DEFAULT_PROVIDER:
            return False

        try:
            default_provider_obj = Provider.objects.get(name=DEFAULT_PROVIDER)
        except ObjectDoesNotExist:
            logger.warning(f"Default provider with name {DEFAULT_PROVIDER} doesn't exist")
            return False

        return default_provider_obj

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class EditProviderOrder(LoginRequiredMixin, DocboxFormViewBase, UpdateView):
    template_name = "docbox/edit-provider-order.html"
    form_class = NewProviderOrderForm
    model = ProviderOrder
    success_url = reverse_lazy("docbox:orders-list")

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
        context["next"] = self.next
        context["order"] = self.object.order
        context["providers_list"] = Provider.objects.all()
        return context


class DeleteProviderOreder(LoginRequiredMixin, DeleteView):
    model = ProviderOrder
    template_name = "docbox/delete-provider-order.html"
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
        context["next"] = self.next
        return context


class OrdersList(LoginRequiredMixin, DocboxListViewBase):
    template_name = "docbox/orders-list.html"
    model = Order

    status_choices = Order.Status.choices.copy()
    status_choices.append(("all", "все"))
    status_choices.append(("not_finished", "не завершен"))

    type_choices = Order.ORDER_TYPE_CHOICES.copy()
    type_choices.append(("all", "все"))

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.search_q = ""

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        status = request.POST.get("status", "all")
        order_type = request.POST.get("type", "all")
        self.search_q = request.POST.get("search_q")
        request.session["status"] = status
        request.session["type"] = order_type

        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.status = request.session.get("status", "all")
        self.order_type = request.session.get("type", "all")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.status
        context["selected_type"] = self.order_type
        context["search_q"] = self.search_q
        context["status_choices"] = self.status_choices
        context["type_choices"] = self.type_choices
        return context

    def get_queryset(self):

        queryset = super().get_queryset()
        queryset = queryset.filter(date_created__range=(self.start_date, self.end_date))

        if self.search_q:
            query = Q(providerorder__code__contains=self.search_q)
            legacy_query = Q(provider_code__contains=self.search_q)
            queryset = queryset.filter(query | legacy_query)

        if self.order_type != "all":
            queryset = queryset.filter(category=self.order_type)

        if self.status == "not_finished":
            return queryset.exclude(status="finished")

        if self.status != "all":
            queryset = queryset.filter(status=self.status)

        return queryset


class ProviderDetail(OrdersList):
    template_name = "docbox/provider-detail.html"

    def get(self, request, *args, **kwargs):
        try:
            self.provider = Provider.objects.get(pk=self.kwargs.get("pk"))
        except Provider.DoesNotExist:
            return HttpResponseNotFound()

        if self.provider.deletable:
            return redirect("docbox:delete-provider", pk=self.provider.pk)

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.provider:
            queryset = queryset.filter(providerorder__provider=self.provider)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["provider"] = self.provider
        return context


class OrdersClient(OrdersList):
    def get(self, request, *args, **kwargs):
        self.client_pk = self.kwargs.get("client_pk")
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.client_pk:
            queryset = queryset.filter(client=self.client_pk)

        return queryset


class OrderDetail(LoginRequiredMixin, DetailView):
    template_name = "docbox/order-detail.html"
    model = Order


class TransactionList(LoginRequiredMixin, DocboxListViewBase):
    template_name = "docbox/transactions_list.html"
    model = Transaction

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.search_q = ""

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        request.session["provider"] = request.POST.get("provider", "all")
        self.search_q = request.POST.get("search_q")
        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.provider = request.session.get("provider", "all")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cashbox_sum = Transaction.objects.filter(cashbox=True).aggregate(Sum("amount"))
        context["cashbox_sum"] = cashbox_sum.get("amount__sum", 0)
        context["providers"] = Provider.objects.all()
        context["selected_provider"] = self.provider
        context["search_q"] = self.search_q

        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(date__range=(self.start_date, self.end_date))
        if self.provider != "all":
            queryset = queryset.filter(provider__pk=self.provider)

        if self.search_q:
            queryset = queryset.filter(comment__contains=self.search_q)

        return queryset


class NewTransaction(LoginRequiredMixin, FormView):
    template_name = "docbox/new-transaction.html"
    form_class = NewTransactionForm
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

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["orders_list"] = Order.objects.all().exclude(status="finished")
        context["clients_list"] = Client.objects.all()
        context["providers_list"] = Provider.objects.all()
        return context

    def get_initial(self):
        if isinstance(self.object, Order):
            self.initial = [{"order": self.object.order_id, "client": self.object.client.client_id}]
        if isinstance(self.object, Client):
            self.initial = [{"client": self.object.pk}]
        return super().get_initial()


class EditTransaction(LoginRequiredMixin, DocboxFormViewBase, UpdateView):
    template_name = "docbox/edit-transaction.html"
    form_class = NewTransactionForm
    model = Transaction

    def get_success_url(self):
        return reverse("docbox:transactions-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["orders_list"] = Order.objects.all().exclude(status="finished")
        context["clients_list"] = Client.objects.all()
        context["providers_list"] = Provider.objects.all()
        return context


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
        context["next"] = self.next
        return context


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

        status = request.GET.get("status", default=False)
        if status in Order.Status.values:
            self.order.status = status
            self.order.save()
            return redirect("docbox:orders-list")

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
        context["order"] = self.order
        context["transactions_sum"] = self.order.transactions_sum
        return context


class DeleteOrder(LoginRequiredMixin, DeleteView):
    template_name = "docbox/delete-order.html"
    model = Order
    success_url = "/docbox/orders"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.provider_orders and not self.object.transactions:
            success_url = self.get_success_url()
            self.object.delete()
            return HttpResponseRedirect(success_url)

        return redirect("docbox:delete-order", pk=self.object.pk)


class BookkeepingOrders(OrdersList):
    template_name = "docbox/bookkeeping-orders.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["total_price"] = 0
        context["total_expenses"] = 0
        context["total_profit"] = 0
        for order in self.object_list:
            context["total_price"] += order.price.products
            context["total_expenses"] += order.price.expenses
            context["total_profit"] += order.price.profit

        return context


class BookkeepingClients(LoginRequiredMixin, DocboxListViewBase):
    template_name = "docbox/bookkeeping-clients.html"
    model = Client

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        return self.get(request, *args, **kwargs)

    def get_queryset(self):
        clients = super().get_queryset()
        queryset = (
            clients.filter(client_orders__date_created__range=(self.start_date, self.end_date))
            .distinct()
            .prefetch_related(
                Prefetch("client_orders", Order.objects.filter(date_created__range=(self.start_date, self.end_date)))
            )
        )

        return sorted(
            queryset,
            key=lambda client: client.profit,
            reverse=True,
        )


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
