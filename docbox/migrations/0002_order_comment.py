# Generated by Django 2.2.8 on 2020-01-26 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("docbox", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="comment",
            field=models.TextField(
                blank=True, default="", max_length=1024, null=True, verbose_name="Комментарий"
            ),
        ),
    ]
