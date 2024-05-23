# core/management/commands/load_meetings_data.py

from django.core.management.base import BaseCommand
import requests
import json
import pandas as pd

class Command(BaseCommand):
    help = "Fetch EP meetings data for a specific year"

    def add_arguments(self, parser):
        parser.add_argument('year', type=int, help='Year to fetch the data for')

    def handle(self, *args, **options):
        year = options['year']
        meetings_data = self.fetch_meetings_for_year(year)
        if meetings_data:
            self.save_meetings_data(meetings_data, year)
            all_votes_data = self.fetch_votes_for_all_meetings(meetings_data)
            if all_votes_data:
                self.save_all_votes_data(all_votes_data, year)

    def fetch_meetings_for_year(self, year):
        # Construct the URL based on the provided year
        meetings_url = f"https://data.europarl.europa.eu/api/v2/meetings?year={year}&format=application%2Fld%2Bjson"
        response = requests.get(meetings_url)
        
        if response.status_code == 200:
            return response.json()
        else:
            self.stderr.write(self.style.ERROR(f"Failed to fetch meetings data for year {year}"))
            return None

    def save_meetings_data(self, meetings_data, year):
        # Extract the relevant fields from the JSON response like id, type, activity_id, had_activity_type
        meetings = []
        for meeting in meetings_data['data']:
            meetings.append({
                'id': meeting['id'],
                'type': meeting['type'],
                'activity_id': meeting['activity_id'],
                'had_activity_type': meeting['had_activity_type']
            })

        #Create a Dataframe from  extracted data
        df = pd.DataFrame(meetings)

        #save the dataframe to a csv file
        csv_file_path = f"meetings_{year}.csv"
        df.to_csv(csv_file_path, index=False)
        self.stdout.write(self.style.SUCCESS(f"Meetings data saved to {csv_file_path}"))

    def fetch_votes_for_all_meetings(self, meetings_data):
        all_votes = []
        for meeting in meetings_data['data']:
            event_id = meeting['activity_id']
            votes_data = self.fetch_votes_for_meeting(event_id)
            if votes_data:
                for vote in votes_data['data']:
                    vote['meeting_activity_id'] = event_id  # Add the meeting's activity_id to each vote item
                    all_votes.append(vote)
        return all_votes

    def fetch_votes_for_meeting(self, event_id):
        votes_url = f"https://data.europarl.europa.eu/api/v2/meetings/{event_id}/vote-results?format=application%2Fld%2Bjson"
        response = requests.get(votes_url)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 204:
            self.stdout.write(self.style.WARNING(f"No vote results available for meeting {event_id}."))
            return None
        else:
            self.stderr.write(self.style.ERROR(f"Failed to fetch votes data for meeting {event_id}"))
            return None

    def save_all_votes_data(self, all_votes_data, year):
        # Extract the relevant fields from the JSON response
        votes = []
        for vote in all_votes_data:
            votes.append({
                'id': vote.get('id'),
                'type': vote.get('type'),
                'activity_id': vote.get('activity_id'),
                'activity_start_date': vote.get('activity_start_date'),
                'decision_method': vote.get('decision_method'),
                'had_decision_outcome': vote.get('had_decision_outcome'),
                'had_voter_abstention': vote.get('had_voter_abstention'),
                'had_voter_against': vote.get('had_voter_against'),
                'had_voter_favor': vote.get('had_voter_favor'),
                'meeting_activity_id': vote.get('meeting_activity_id')  # Add the meeting's activity_id to each vote item
            })

        # Create a DataFrame from the extracted data
        df = pd.DataFrame(votes)

        # Save the DataFrame to a CSV file
        csv_file_path = f"votes_{year}.csv"
        df.to_csv(csv_file_path, index=False)
        self.stdout.write(self.style.SUCCESS(f"All votes data saved to {csv_file_path}"))

