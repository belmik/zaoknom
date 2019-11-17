"""docbox URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from . import views


urlpatterns = [
    path('', include('social_django.urls', namespace='social')),
    path('', views.HomeView.as_view(), name="home"),
    path('logout', LogoutView.as_view(), name="logout"),
    path('clients/', views.ClientsList.as_view(), name="clients-list"),
    path('client/<uuid:pk>', views.ClientDetail.as_view(), name="client-detail"),
    path('client/<uuid:pk>/edit', views.EditClient.as_view(), name="client-edit"),
    path('orders/', views.OrdersList.as_view(), name="orders-list"),
    path('orders/export', views.CsvExport.as_view(), name="export-csv"),
    path('order/<uuid:pk>', views.OrderDetail.as_view(), name="order-detail"),
    path('order/<uuid:pk>/edit', views.EditOrder.as_view(), name="order-edit"),
    path('order/new', views.NewOrder.as_view(), name="new-order"),
    path('transaction/new', views.NewTransaction.as_view(), name="new-transaction"),
    path('transaction/<uuid:pk>/delete', views.DeleteTransaction.as_view(), name="delete-transaction"),
]
