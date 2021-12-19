import codecs
import csv
import io
from datetime import date

from django.core.management.base import BaseCommand

from docbox.models import Order, Transaction

from ._gdrive import upload_file


class Command(BaseCommand):
    help = "Make backup and upload it to google-drive"

    def handle(self, *args, **options):
        today = date.today().strftime("%Y%m%d")
        self.upload_csv_to_gdrive(Order, "data_for_csv", f"orders_{today}.csv")
        self.upload_csv_to_gdrive(Transaction, "data_for_csv", f"transactions_{today}.csv")
        self.upload_csv_to_gdrive(Order, "bookkeeping_data_for_csv", f"BookkeepingOrders_{today}.csv")

    def upload_csv_to_gdrive(self, model, csv_dict, filename):
        """Dump all items from model to csv file and upload it to gdrive.

        `model` must have data_for_csv attribute, which is list of values needed for backup.
        """
        with io.BytesIO() as csv_file_obj:

            # Need to do this because googleapiclient accepts only bytes objects,
            # and csv module only works with text objects
            wrapper = codecs.getwriter("utf-8")
            csv_file_obj_wraper = wrapper(csv_file_obj)

            csv_fieldnames = getattr(model.objects.first(), csv_dict).keys()
            writer = csv.DictWriter(csv_file_obj_wraper, fieldnames=csv_fieldnames)
            writer.writeheader()
            for item in model.objects.all():
                writer.writerow(getattr(item, csv_dict))

            id, name, size = upload_file(filename, csv_file_obj, "text/csv")

        self.stdout.write(f"File {name} ({size} bytes) uploaded to gdrive with id: '{id}'")
