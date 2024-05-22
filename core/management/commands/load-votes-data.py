from django.core.management.base import BaseCommand
from core.models import MEP, Vote, MEP_Vote_Mapping
import requests


class Command(BaseCommand):

    def handle(self, *args, **options):

        url = "https://data.europarl.europa.eu/api/v2/meetings/MTG-PL-2024-01-16/vote-results?format=application%2Fld%2Bjson"
        response = requests.get(url)
        json_data = response.json()


        for item in json_data['data']:  #data is a list of dictionaries. Inside those dictionaries there are keys whose values are dictionaries also
            print(item['activity_label']['hr'])

