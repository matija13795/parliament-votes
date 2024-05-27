from django.core.management.base import BaseCommand
from core.models import Meeting, Vote, MEP, MEPVoteMapping
import requests
import time

class Command(BaseCommand):
    help = 'Fetch and store meetings and votes data for all available years'

    def handle(self, *args, **kwargs):
        self.fetch_and_store_all_meetings()

    def fetch_and_store_all_meetings(self):
        # years for which to fetch data 
        start_year = 2014
        end_year = 2024

        for year in range(start_year, end_year + 1):
            self.fetch_and_store_meetings_for_year(year)

    def fetch_and_store_meetings_for_year(self, year):
        url = "https://data.europarl.europa.eu/api/v2/meetings"
        params = {
            "format": "application/ld+json",
            "year": year,
            "offset": 0,
            "limit": 100 # number of meetings to fetch per request
        }

        while True:
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                meetings_data = response.json()

                if not meetings_data.get("data"):
                    break # if no meetings for the year

                meetings = meetings_data["data"]
                self.process_meetings(meetings)

                params["offset"] += params["limit"]  # Move to the next page

                # Check if there are more pages
                if params["offset"] >= meetings_data.get("total", 0):
                    break

            except requests.RequestException as e:
                self.stderr.write(self.style.ERROR(f'HTTP Request failed for year {year}, offset {params["offset"]}: {e}'))
                break
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'An error occurred: {e}'))
                break

    def process_meetings(self, meetings):
        meetings_to_save = []
        for meeting in meetings:
            meeting_obj, created = Meeting.objects.update_or_create(
                activity_id=meeting['activity_id'],
                defaults={'activity_type': meeting['had_activity_type']}
            )
            meetings_to_save.append(meeting_obj)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created meeting {meeting["activity_id"]}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated meeting {meeting["activity_id"]}'))

        Meeting.objects.bulk_create(meetings_to_save, ignore_conflicts=True)

        for meeting_obj in meetings_to_save:
            self.fetch_and_store_votes_for_meeting(meeting_obj.activity_id)

    def fetch_and_store_votes_for_meeting(self, meeting_id):
        votes_url = f"https://data.europarl.europa.eu/api/v2/meetings/{meeting_id}/vote-results"
        votes_params = {"format": "application/ld+json"}

        try:
            votes_response = self.retry_request(votes_url, votes_params)
            votes_data = votes_response.json()

            for vote_info in votes_data["data"]:
                for vote in vote_info.get("consists_of", []):
                    vote_obj = self.save_vote_data(vote)
                    self.create_mep_vote_mappings(vote, vote_obj)

        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f'Failed to fetch votes data for meeting {meeting_id}: {e}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An error occurred while processing meeting {meeting_id}: {e}'))


    # GPT suggested i add this to handle request errors, it basically just retries the request
    def retry_request(self, url, params, retries=3, delay=5):
        for i in range(retries):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if i < retries - 1:
                    self.stderr.write(self.style.WARNING(f'Retry {i+1}/{retries} for {url}: {e}'))
                    time.sleep(delay)
                else:
                    raise

    def save_vote_data(self, vote):
        self.stdout.write(self.style.SUCCESS(f'Processing vote {vote["id"]}'))

        vote_obj, created = Vote.objects.update_or_create(
            unique_identifier=vote["activity_id"],
            defaults={
                'outcome': vote.get('had_decision_outcome', ''),
                'number_of_attendees': vote.get('number_of_attendees', 0),
                'number_of_favor': vote.get('number_of_votes_favor', 0),
                'number_of_against': vote.get('number_of_votes_against', 0),
                'number_of_abstention': vote.get('number_of_votes_abstention', 0)
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created vote {vote["activity_id"]}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated vote {vote["activity_id"]}'))

        return vote_obj

    def create_mep_vote_mappings(self, vote, vote_obj):
        mappings_to_save = []

        for mep_id in vote.get("had_voter_favor", []):
            mappings_to_save.append(MEPVoteMapping(
                mep_id=self.get_mep_id(mep_id),
                vote=vote_obj,
                vote_type='favor'
            ))

        for mep_id in vote.get("had_voter_against", []):
            mappings_to_save.append(MEPVoteMapping(
                mep_id=self.get_mep_id(mep_id),
                vote=vote_obj,
                vote_type='against'
            ))

        for mep_id in vote.get("had_voter_abstention", []):
            mappings_to_save.append(MEPVoteMapping(
                mep_id=self.get_mep_id(mep_id),
                vote=vote_obj,
                vote_type='abstention'
            ))
        print("done")

        MEPVoteMapping.objects.bulk_create(mappings_to_save, ignore_conflicts=True)
        print("mapping created")

    def get_mep_id(self, mep_identifier):
        mep, created = MEP.objects.get_or_create(
            unique_identifier=int(mep_identifier.split("/")[1])
        )
        return mep.id  
