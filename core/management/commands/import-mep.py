from django.core.management.base import BaseCommand
from core.models import MEP
import requests

class Command(BaseCommand):
    help = 'Fetch and store MEP data'

    def handle(self, *args, **kwargs):
        url = "https://data.europarl.europa.eu/api/v2/meps"
        params = {
            "format": "application/ld+json",
            "offset": 0,
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Check for HTTP request errors
            json_data = response.json()

            for item in json_data["data"]:
                unique_id = int(item["id"][7:])  # Extract numeric ID from "person/1234"
                first_name = item.get("givenName", "")  # Default to empty string if missing
                last_name = item.get("familyName", "")  # Default to empty string if missing
                combined_name = f"{first_name} {last_name}".strip()

                mep, created = MEP.objects.update_or_create(
                    mep_id=unique_id,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'combined_name': combined_name  # Set the combined name
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created MEP {combined_name}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Updated MEP {combined_name}'))

        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f'HTTP Request failed: {e}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An error occurred: {e}'))
