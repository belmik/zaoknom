from django.contrib.auth.views import LogoutView
from django.urls import include, path

from . import views

docbox_patterns = (
    [
        path("", views.HomeView.as_view(), name="home"),
        path("logout", LogoutView.as_view(), name="logout"),
        path("clients", views.ClientsList.as_view(), name="clients-list"),
        path("client/<uuid:pk>", views.ClientDetail.as_view(), name="client-detail"),
        path(
            "client/<uuid:pk>/orders",
            views.CleintOrdersList.as_view(),
            name="client-orders-list",
        ),
        path("client/<uuid:pk>/edit", views.EditClient.as_view(), name="client-edit"),
        path("orders", views.OrdersList.as_view(), name="orders-list"),
        path("orders/export", views.CsvExport.as_view(), name="export-csv"),
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
        path("transaction/new", views.NewTransaction.as_view(), name="new-transaction"),
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
