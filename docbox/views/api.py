import json
import os
from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.http import HttpResponseBadRequest, JsonResponse
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

        self.error_messages = []

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        if self.auth:
            return super().dispatch(request, *args, **kwargs)
        return HttpResponseBadRequest()

    def return_errors(self, message=False):
        if message:
            self.error_messages.append(message)
        return JsonResponse({"status": "error", "error_messages": self.error_messages})


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


class BulkUpdateProviderOrder(ApiBaseView):
    def post(self, request, **args):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return self.return_errors("Parametr 'orders' contains not valid json")

        provider_orders = ProviderOrder.objects.exclude(status="finished")
        for provider_code, new_info in data.items():
            try:
                provider_order = provider_orders.get(code=provider_code)
            except ObjectDoesNotExist:
                self.error_messages.append(f"Provider code '{provider_code}' doesn't exist.")
                continue

            self.update_info(provider_order, new_info)

        if self.error_messages:
            return self.return_errors()

        return JsonResponse({"status": "ok"})

    def update_info(self, provider_order, new_info):
        if "status" in new_info:
            provider_order = self.update_status(provider_order, new_info)

        if "delivery_date" in new_info:
            provider_order = self.update_delivery_date(provider_order, new_info)

        provider_order.save()

    def update_status(self, provider_order, new_info):
        new_status = new_info.get("status")
        if new_status in Order.Status.values:
            provider_order.status = new_status
        else:
            self.error_messages.append(f"Status '{new_status}' is not allowed")
        return provider_order

    def update_delivery_date(self, provider_order, new_info):
        try:
            new_delivery_date = date.fromisoformat(new_info["delivery_date"])
        except ValueError:
            self.error_messages.append("Delivery date expected to be in iso format like 'YYYY-MM-DD'")
        else:
            provider_order.delivery_date = new_delivery_date
        return provider_order


class SearchOrder(ApiBaseView):
    def get(self, request, *args, **kwargs):
        provider_code = request.GET.get("provider_code")
        queryset = self.get_filtered_queryset(provider_code)
        if not queryset:
            self.error_messages.append("Nothing found")
            return JsonResponse({"status": "error", "error_messages": self.error_messages})

        search_results = []
        for order in queryset:
            search_results.append(
                {
                    "id": order.pk,
                    "provider_order": order.provider_orders_str,
                    "client": order.client.name,
                    "comment": order.comment,
                    "price_total": order.price.total,
                    "price_remaining": order.remaining,
                    "status": order.status,
                    "creation_date": order.date_created,
                    "delivery_date": order.date_delivery or "",
                }
            )

        return JsonResponse({"status": "ok", "search_results": search_results})

    def get_filtered_queryset(self, provider_code):
        if not provider_code:
            self.error_messages.append("The search query parametr 'provider_code' is not set")
            return False

        query = models.Q(providerorder__code__contains=provider_code)
        legacy_query = models.Q(provider_code__contains=provider_code)
        return Order.objects.filter(query | legacy_query)
