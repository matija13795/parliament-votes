from django.core.management.base import BaseCommand
from core.models import MEP, Vote, MEP_Vote_Mapping
import requests

class Command(BaseCommand):

    def handle(self, *args, **options):

        url = "https://data.europarl.europa.eu/api/v2/meps"
        POLITICAL_GROUPS = ["PPE", "NI", "S_D", "VERTS_ALE", "ECR", "RENEW", "THE_LEFT", "ID"]

        for political_group in POLITICAL_GROUPS:
            params = {
                "political-group": [political_group],     #array[string]
                "format": "application/ld+json",          #string
                "offset": 0,                              #integer

                #"limit": 10,                           #integer
                #"parliamentary-term": [0],             #array[integer]
                #"gender": ["MALE"],                    #array[string]
                #"country-of-representation": ["DE"]    #array[string]
            }

            response = requests.get(url, params=params)
            json_data = response.json()

            for item in json_data["data"]:

                unique_id  = int(item["id"][7:]) #item["id"] is of type "person/1234". So I am accessing the begining of a number, and then typecasting it
            
                # Use .get() to retrieve values with default values if keys are missing
                first_name = item.get("givenName", "")  # Default to an empty string if givenName is missing
                last_name = item.get("familyName", "")  # Default to an empty string if familyName is missing

                mep = MEP(unique_identifier=unique_id, first_name=first_name, last_name=last_name, political_party=political_group)
                mep.save()                