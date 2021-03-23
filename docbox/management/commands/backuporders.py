import io
from datetime import date

from django.core.management.base import BaseCommand

from docbox.models import Order, Transaction

from ._gdrive import upload_file


class Command(BaseCommand):
    help = "Make backup and upload it to google-drive"

    def handle(self, *args, **options):
        today = date.today().strftime("%Y%m%d")
        self.upload_csv_to_gdrive(Order, f"orders_{today}.csv")
        self.upload_csv_to_gdrive(Transaction, f"transactions_{today}.csv")

    def upload_csv_to_gdrive(self, model, filename):
        """Dump all items from model to csv file and upload it to gdrive.

        `model` must have data_for_csv attribute, which is list of values needed for backup.
        """
        csv_file_obj = io.BytesIO()
        for item in model.objects.all():
            csv_line = ";".join(map(str, item.data_for_csv))
            csv_line += "\n"
            csv_file_obj.write(bytes(csv_line, "utf=8"))

        id, name, size = upload_file(filename, csv_file_obj, "text/csv")
        self.stdout.write(f"File {name} ({size} bytes) uploaded to gdrive with id: '{id}'")
