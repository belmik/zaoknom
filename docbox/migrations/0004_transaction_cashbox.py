# Generated by Django 2.2.8 on 2020-02-13 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("docbox", "0003_auto_20200126_2311"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="cashbox",
            field=models.BooleanField(null=True, verbose_name="Касса"),
        ),
    ]