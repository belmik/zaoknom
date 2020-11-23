import os

from django.db import models
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.generic import View

from docbox.models import Transaction


class ApiBaseView(View):
    token = os.getenv("API_TOKEN")

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.auth = False
        auth_header = request.headers.get("Authorization", False)
        if auth_header == f"Bearer {self.token}":
            self.auth = True

    def dispatch(self, request, *args, **kwargs):
        if self.auth:
            return super().dispatch(request, *args, **kwargs)

        return HttpResponseBadRequest()


class GetBalance(ApiBaseView):
    def get(self, request, *args, **kwargs):
        cashbox_sum = Transaction.objects.filter(cashbox=True).aggregate(models.Sum("amount"))
        return JsonResponse({"balance": cashbox_sum.get("amount__sum", 0)})
