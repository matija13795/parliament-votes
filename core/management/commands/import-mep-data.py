from core.models import MEP
from django.core.management.base import BaseCommand
from django.conf import settings
import datetime
import psycopg2
import csv
import os

class Command(BaseCommand):
    help = 'Imports MEP data from a CSV file into the database'

    def handle(self, *args, **options):
        # Define the path to the CSV file relative to the BASE_DIR
        csv_file_path = os.path.join(settings.BASE_DIR, 'meps.csv')

        try:
            # Open the CSV file and read it row by row
            with open(csv_file_path, 'r') as f:
                reader = csv.DictReader(f)

                # Process each row and save it to the database
                for row in reader:
                    mep_id = row.get('mep_id')
                    first_name = row.get('first_name', '')
                    last_name = row.get('last_name', '')

                    if first_name == '':
                        combined_name = last_name

                    elif last_name == '':
                        combined_name = first_name

                    else:
                        combined_name = row.get('first_name') + " " + row.get('last_name')
                    
                    gender = row.get('gender', '')

                    date_of_birth = row.get('date_of_birth')
                    date_of_death = row['date_of_death']
                    
                    if date_of_death == '':
                        date_of_death = None

                    if date_of_birth == '':
                        date_of_birth = None

                    hometown = row.get('hometown', '')
                    country_of_representation = row.get('country_of_representation', '')

                    mep = MEP(mep_id=mep_id, first_name=first_name, last_name=last_name, combined_name=combined_name, gender=gender, date_of_birth=date_of_birth, date_of_death=date_of_death, hometown=hometown, country_of_representation=country_of_representation)
                    mep.save()

            self.stdout.write(self.style.SUCCESS('Successfully imported CSV data'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error importing CSV data: {e}'))