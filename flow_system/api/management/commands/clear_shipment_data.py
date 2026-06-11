from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Shipment, ProductionTimeSlot

class Command(BaseCommand):
    help = 'Deletes all Shipment and ProductionTimeSlot records from the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt and proceed with deletion.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        confirm = options['confirm']

        shipment_count = Shipment.objects.count()
        slot_count = ProductionTimeSlot.objects.count()

        if shipment_count == 0 and slot_count == 0:
            self.stdout.write(self.style.SUCCESS('No shipment or production time slot data to delete.'))
            return

        self.stdout.write(self.style.WARNING(
            f"This command will permanently delete {shipment_count} Shipment record(s) "
            f"and {slot_count} ProductionTimeSlot record(s)."
        ))

        if not confirm:
            confirmation = input("Are you sure you want to proceed? (yes/no): ")
            if confirmation.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Deletion cancelled by user.'))
                return

        ProductionTimeSlot.objects.all().delete()
        Shipment.objects.all().delete() # Delete Shipments after slots due to potential FK constraints if defined that way

        self.stdout.write(self.style.SUCCESS(
            f"Successfully deleted {shipment_count} Shipment records and {slot_count} ProductionTimeSlot records."
        ))
