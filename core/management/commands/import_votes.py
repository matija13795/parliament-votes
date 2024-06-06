from django.core.management.base import BaseCommand
import pandas as pd
from django.db import transaction
from core.models import MEP, Vote

class Command(BaseCommand):
    help = 'Imports vote data into the database'

    def handle(self, *args, **options):
        vote_mapping_ep1_ep2_ep5 = {
            1: 'Yes',
            2: 'No',
            3: 'Abstain',
            4: 'Present but did not vote',
            0: 'Absent',
            5: 'Not an MEP'
        }

        vote_mapping_ep3_ep4 = {
            1: 'Yes',
            2: 'No',
            3: 'Abstain',
            4: 'Present but did not vote',
            0: 'Absent or Not an MEP'
        }

        # List of CSV files and corresponding vote mappings
        csv_files = [
            ('votes/rcv_ep1.csv', 'EP1', vote_mapping_ep1_ep2_ep5),
            ('votes/rcv_ep2.csv', 'EP2', vote_mapping_ep1_ep2_ep5),
            ('votes/rcv_ep3.csv', 'EP3', vote_mapping_ep3_ep4),
            ('votes/rcv_ep4.csv', 'EP4', vote_mapping_ep3_ep4),
            ('votes/rcv_ep5.csv', 'EP5', vote_mapping_ep1_ep2_ep5)
        ]

        #reading VOTE information from the excel file
        vote_info_df = pd.read_excel('vote_info_Jun2010.xls', sheet_name=None)
        print("Sheets in the Excel file:", vote_info_df.keys())

        @transaction.atomic
        def process_csv(file_info):
            file_name, sheet_name, vote_mapping = file_info
            print(f"Processing {file_name}...")
            # Read the votes data from the CSV file with encoding specified
            votes_df = pd.read_csv(file_name, encoding='ISO-8859-1')

            #melt the votes_df to transform columns V1, V2, ... Vn into rows
            votes_melted_df = votes_df.melt(id_vars=['MEPID', 'MEPNAME', 'MS', 'NP', 'EPG'],
                                            var_name='Vote', value_name='Decision')

            # extract vote number from the 'Vote' column (e.g., V1 -> 1)
            votes_melted_df['Vote No'] = votes_melted_df['Vote'].str.extract('(\d+)').astype(int)

            # merge melted votes data with the vote information data
            right_on_col = f'Vote No. in RCV_{sheet_name} file'
            combined_df = pd.merge(votes_melted_df, vote_info_df[sheet_name], how='left',
                                   left_on='Vote No', right_on=right_on_col)

            #map the vote decisions
            combined_df['Vote Decision'] = combined_df['Decision'].map(vote_mapping)

            #include MEPNAME in the final dataframe
            combined_df['Vote No'] = combined_df['Vote No.']  # Ensure Vote No is taken from the Excel file
            combined_df = combined_df[['Vote No.', 'Long Description', 'MEPID', 'MEPNAME', 'EPG', 'Vote Decision']]
            print("Combined DataFrame:", combined_df.head())

            # iterate over the rows and save the data to the database
            for _, row in combined_df.iterrows():
                # extract the first and last name from mep_name where the all caps is the last name
                first_name = row['MEPNAME'].split(' ')[1:]
                last_name = row['MEPNAME'].split(' ')[0]
                print("first name: ", first_name, "last name: ", last_name)

                #combine the first_name and last_name into 1 string
                combined_name = ' '.join(first_name) + ' ' + last_name 
                print("combined name: ", combined_name)

                #compare the combined name string to the combined_name string from the mep table (Case insensitive) and retreive mep id from mep table
                mep = MEP.objects.filter(combined_name__iexact=combined_name).first()

                #if mep is not found, keep the same mep_id???
                if mep is None:
                    print("skipping mep:", combined_name)
                    mep = MEP(mep_id=row['MEPID'], first_name=first_name, last_name=last_name, combined_name=combined_name)
                    mep.save()
                else: 
                    mep_id = mep.mep_id
                

                vote = Vote(
                    vote_id=row['Vote No.'],
                    description=row['Long Description'],
                    mep_id= mep_id ,
                    mep_name=row['MEPNAME'],
                    vote_type=row['Vote Decision']
                )
                print(row['Vote No.'], row['Long Description'], row['MEPID'], row['MEPNAME'], row['Vote Decision'])
                vote.save()
            print(f"Processed {file_name}")

        # go over each each csv file and process it
        for file_info in csv_files:
            process_csv(file_info)

        self.stdout.write(self.style.SUCCESS("Database has been populated with vote data."))
