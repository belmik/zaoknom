# Generated by Django 3.1.3 on 2021-01-11 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docbox', '0010_auto_20210111_1719'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='price',
            name='added',
        ),
        migrations.AlterField(
            model_name='price',
            name='added_expenses',
            field=models.DecimalField(blank=True, decimal_places=0, max_digits=10, null=True, verbose_name='Дополнительные расходы'),
        ),
    ]
