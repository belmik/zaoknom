# Generated by Django 3.2.8 on 2022-01-10 10:41

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docbox', '0014_auto_20220110_1235'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime.today, null=True, verbose_name='Дата оформления'),
        ),
    ]
