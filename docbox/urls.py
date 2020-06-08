from django.contrib.auth.views import LogoutView
from django.urls import include, path

from . import views

docbox_patterns = (
    [
        path("", views.HomeView.as_view(), name="home"),
        path("logout", LogoutView.as_view(), name="logout"),
        path("clients", views.ClientsList.as_view(), name="clients-list"),
        path("client/<uuid:pk>", views.ClientDetail.as_view(), name="client-detail"),
        path("client/<uuid:pk>/edit", views.EditClient.as_view(), name="client-edit"),
        path("providers", views.ProvidersList.as_view(), name="providers-list"),
        path("provider/new", views.NewProvider.as_view(), name="new-provider"),
        path("provider/<uuid:pk>", views.ProviderDetail.as_view(), name="provider-detail"),
        path("provider/<uuid:pk>/edit", views.EditProvider.as_view(), name="provider-edit"),
        path("orders", views.OrdersList.as_view(), name="orders-list"),
        path("orders/export", views.CsvExport.as_view(), name="export-csv"),
        path(
            "orders/<uuid:client_pk>/", views.OrdersList.as_view(), name="client-orders-list",
        ),
        path(
            "bookkeeping/orders", views.BookkeepingOrders.as_view(), name="bookkeeping-orders"
        ),
        path(
            "bookkeeping/order/<uuid:pk>/edit",
            views.BookkeepingEditOrder.as_view(),
            name="bookkeeping-order-edit",
        ),
        path("order/<uuid:pk>", views.OrderDetail.as_view(), name="order-detail"),
        path("order/<uuid:pk>/edit", views.EditOrder.as_view(), name="order-edit"),
        path("order/new", views.NewOrder.as_view(), name="new-order"),
        path("transactions", views.TransactionList.as_view(), name="transactions-list"),
        path("transaction/new", views.NewTransaction.as_view(), name="new-transaction"),
        path(
            "transaction/<uuid:pk>/edit",
            views.EditTransaction.as_view(),
            name="edit-transaction",
        ),
        path(
            "transaction/<uuid:pk>/delete",
            views.DeleteTransaction.as_view(),
            name="delete-transaction",
        ),
    ],
    "docbox",
)


urlpatterns = [
    path("", views.ZaoknomView.as_view(), name="zaoknom-home"),
    path("docbox/", include(docbox_patterns)),
    path("", include("social_django.urls", namespace="social")),
]
