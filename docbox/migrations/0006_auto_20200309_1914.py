# Generated by Django 2.2.8 on 2020-03-09 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("docbox", "0005_auto_20200213_2136"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="transaction",
            options={
                "ordering": ["-date"],
                "verbose_name": "Транзация",
                "verbose_name_plural": "Транзакции",
            },
        ),
        migrations.AlterField(
            model_name="order",
            name="provider_code",
            field=models.CharField(
                blank=True,
                default="б/н",
                max_length=1024,
                verbose_name="Производственный номер",
            ),
        ),
    ]
