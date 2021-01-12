import os
from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.http import HttpResponseBadRequest, HttpResponseNotFound, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from docbox.models import Order, ProviderOrder, Transaction


class ApiBaseView(View):
    token = os.getenv("API_TOKEN")

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.auth = False
        auth_header = request.headers.get("Authorization", False)
        if auth_header == f"Bearer {self.token}":
            self.auth = True

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        if self.auth:
            return super().dispatch(request, *args, **kwargs)

        return HttpResponseBadRequest()


class GetBalance(ApiBaseView):
    def get(self, request, *args, **kwargs):
        cashbox_sum = Transaction.objects.filter(cashbox=True).aggregate(models.Sum("amount"))
        return JsonResponse({"balance": cashbox_sum.get("amount__sum", 0)})


class ListProviderOrders(ApiBaseView):
    def get(self, request, *args, **kwargs):
        data = {"provider_order_list": []}
        for provider_order in ProviderOrder.objects.all()[:50]:
            data["provider_order_list"].append(
                {
                    "id": provider_order.pk,
                    "provider": provider_order.provider.name,
                    "code": provider_order.code,
                    "price": provider_order.price or "",
                    "status": provider_order.status or "",
                    "creation_date": provider_order.creation_date,
                    "delivery_date": provider_order.delivery_date or "",
                }
            )
        return JsonResponse(data)


class UpdateProviderOrder(ApiBaseView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.error_messages = []

    def post(self, request, *args, **kwargs):
        provider_order_uuid = kwargs.get("pk")
        try:
            provider_order = ProviderOrder.objects.get(pk=provider_order_uuid)
        except ObjectDoesNotExist:
            return HttpResponseNotFound()

        new_status = self.get_new_status(request)
        new_delivery_date = self.get_delivery_date(request)

        if self.error_messages:
            return JsonResponse({"status": "error", "error_messages": self.error_messages})

        if new_status:
            provider_order.status = new_status

        if new_delivery_date:
            provider_order.date_delivery = new_delivery_date

        provider_order.save()

        return JsonResponse({"status": "ok"})

    def get_new_status(self, request):
        new_status = request.POST.get("status")
        if new_status and new_status not in Order.Status.values:
            self.error_messages.append(f"Status '{new_status}' is not defined")
        return new_status

    def get_delivery_date(self, request):
        new_delivery_date = False
        delivery_date_data = request.POST.get("delivery_date")
        if delivery_date_data:
            try:
                new_delivery_date = date.fromisoformat(delivery_date_data)
            except ValueError:
                self.error_messages.append(
                    "Delivery date expected to be in iso format like 'YYYY-MM-DD'"
                )

        return new_delivery_date
