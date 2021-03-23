from django.contrib.auth.views import LogoutView
from django.urls import include, path

from .views import api as api_views
from .views import site as views

docbox_patterns = (
    [
        path("", views.OrdersList.as_view(), name="home"),
        path("logout", LogoutView.as_view(), name="logout"),
        path("clients", views.ClientsList.as_view(), name="clients-list"),
        path("client/<uuid:pk>", views.ClientDetail.as_view(), name="client-detail"),
        path("client/<uuid:pk>/edit", views.EditClient.as_view(), name="client-edit"),
        path("client/<uuid:pk>/delete", views.DeleteClient.as_view(), name="delete-client"),
        path("providers", views.ProvidersList.as_view(), name="providers-list"),
        path("provider/new", views.NewProvider.as_view(), name="new-provider"),
        path("provider/<uuid:pk>", views.ProviderDetail.as_view(), name="provider-detail"),
        path("provider/<uuid:pk>/edit", views.EditProvider.as_view(), name="provider-edit"),
        path("orders", views.OrdersList.as_view(), name="orders-list"),
        path("orders/export", views.CsvExport.as_view(), name="export-csv"),
        path("orders/<uuid:client_pk>/", views.OrdersList.as_view(), name="client-orders-list",),
        path("bookkeeping/orders", views.BookkeepingOrders.as_view(), name="bookkeeping-orders"),
        path("bookkeeping/order/<uuid:pk>/edit", views.BookkeepingEditOrder.as_view(), name="bookkeeping-order-edit",),
        path("order/<uuid:pk>", views.OrderDetail.as_view(), name="order-detail"),
        path("order/<uuid:pk>/new-provider-order", views.NewProviderOrder.as_view(), name="new-provider-order",),
        path("provider-order/<uuid:pk>/edit", views.EditProviderOrder.as_view(), name="edit-provider-order",),
        path("provider-order/<uuid:pk>/delete", views.DeleteProviderOreder.as_view(), name="delete-provider-order",),
        path("order/<uuid:pk>/edit", views.EditOrder.as_view(), name="order-edit"),
        path("order/<uuid:pk>/delete", views.DeleteOrder.as_view(), name="delete-order"),
        path("order/new", views.NewOrder.as_view(), name="new-order"),
        path("transactions", views.TransactionList.as_view(), name="transactions-list"),
        path("transaction/new", views.NewTransaction.as_view(), name="new-transaction"),
        path("transaction/<uuid:pk>/edit", views.EditTransaction.as_view(), name="edit-transaction",),
        path("transaction/<uuid:pk>/delete", views.DeleteTransaction.as_view(), name="delete-transaction",),
    ],
    "docbox",
)

docbox_api_patterns = (
    [
        path("balance", api_views.GetBalance.as_view(), name="get-balance"),
        path("provider-order/list", api_views.ListProviderOrders.as_view(), name="list-provider-orders"),
        path("provider-order/<uuid:pk>/update", api_views.UpdateProviderOrder.as_view(), name="update-provider-order"),
    ],
    "docbox-api",
)


urlpatterns = [
    path("", views.ZaoknomView.as_view(), name="zaoknom-home"),
    path("docbox/", include(docbox_patterns)),
    path("docbox/api/", include(docbox_api_patterns)),
    path("", include("social_django.urls", namespace="social")),
]
