from django.core.management.base import BaseCommand
import pandas as pd
import psycopg2


class Command(BaseCommand):
    help = 'Not sure yet how to describe this'

    def handle(self, *args, **options):

        # Load the Excel file
        file_path = 'votes.xlsx'

        # Read the Excel file into a DataFrame
        df = pd.read_excel(file_path)

        # Extract the "MEPNAME" column and convert it to a list
        name_list = df['MEPNAME'].tolist()

        for name in name_list:
            # Split the name by spaces
            parts = name.split()
            # Initialize variables to collect the last name and first name parts
            last_name_parts = []
            first_name_parts = []
            
            # Iterate over the parts to classify them into last name and first name
            for part in parts:
                if part.isupper():
                    last_name_parts.append(part)
                else:
                    first_name_parts.append(part)
            
            # Join the parts to form the full first name and last name
            last_name = ' '.join(last_name_parts)
            first_name = ' '.join(first_name_parts)
            print(first_name + " " + last_name)
            