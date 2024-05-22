import os
import csv
import psycopg2
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Import CSV data into the database'

    def handle(self, *args, **kwargs):
        # Define the path to the CSV file relative to the BASE_DIR
        csv_file_path = os.path.join(settings.BASE_DIR, 'mep_data', 'meps.csv')
        
        # Establish a connection to the PostgreSQL database using settings
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()

        try:
            # Execute the \copy command
            with open(csv_file_path, 'r') as f:
                next(f)  # Skip the header row
                cursor.copy_expert("COPY customers (id, gender) FROM STDIN WITH CSV HEADER DELIMITER ','", f)
            conn.commit()
            self.stdout.write(self.style.SUCCESS('Successfully imported CSV data'))
        except Exception as e:
            conn.rollback()
            self.stderr.write(self.style.ERROR(f'Error importing CSV data: {e}'))
        finally:
            cursor.close()
            conn.close()