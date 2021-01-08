# Generated by Django 3.1.3 on 2021-01-06 15:18

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("docbox", "0006_auto_20200309_1914"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProviderOrder",
            fields=[
                (
                    "provider_order_id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("code", models.CharField(max_length=16, verbose_name="Номер заказа")),
                (
                    "price",
                    models.DecimalField(
                        blank=True,
                        decimal_places=0,
                        max_digits=10,
                        verbose_name="Сумма заказа",
                    ),
                ),
                (
                    "order_content",
                    models.TextField(
                        blank=True,
                        default="",
                        max_length=1024,
                        null=True,
                        verbose_name="Состав заказа",
                    ),
                ),
                (
                    "creation_date",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Дата добавления"
                    ),
                ),
                (
                    "delivery_date",
                    models.DateField(blank=True, null=True, verbose_name="Дата доставки"),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="docbox.order",
                        verbose_name="Заказ",
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="docbox.provider",
                        verbose_name="Поставщик",
                    ),
                ),
            ],
        ),
    ]
