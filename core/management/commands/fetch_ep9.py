from datetime import datetime
import aiohttp # for async requests so we can fetch multiple URLs at the same time
import asyncio
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from core.models import VoteInfo, VoteMapping, MEP, PoliticalGroup

class Command(BaseCommand):
    help = 'Fetch and store voting data from the European Parliament'

    async def fetch_xml_async(self, session, url):
        async with session.get(url) as response:
            if response.status == 200:
                # self.stdout.write(f"Fetched XML data from {url}")
                return await response.text(), url
            else:
                # self.stdout.write(f"Failed to fetch XML data from {url}. Status code: {response.status}")
                return None, url

    async def fetch_all_xml(self, urls):
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_xml_async(session, url) for url in urls]
            return await asyncio.gather(*tasks)

    def handle(self, *args, **kwargs):
        base_url = 'https://www.europarl.europa.eu/plenary/en/ajax/getSessionCalendar.html'
        params = {
            'family': 'PV',
            'termId': '9',  # term ID for 2019-2024
            'source': '',
            'dateRef': '',
            'calendarLanguage': 'en'
        }

        def fetch_calendar_data(term_id):
            params['termId'] = term_id
            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                self.stdout.write(f"Failed to fetch data for term {term_id}. Status code: {response.status_code}")
                return None

        def parse_xml(xml_content, vote_date):
            soup = BeautifulSoup(xml_content, 'xml')
            results = soup.find_all('RollCallVote.Result')

            # Preliminary check for missing PersId
            for result in results:
                for group in ['Result.For', 'Result.Against', 'Result.Abstentions', 'Result.Abstention']:
                    political_groups = result.find(group)
                    if political_groups:
                        for political_group in political_groups.find_all('Result.PoliticalGroup.List'):
                            for member in political_group.find_all('PoliticalGroup.Member.Name'):
                                mep_id = member.get('PersId')
                                mep_name = member.text.strip()
                                if not mep_id:
                                    print(f"Warning: PersId is missing for {mep_name} on date {vote_date}")
                                    return  # exit the function if PersId is missing (need to do smth abt this)

            vote_mappings = []
            mep_cache = {mep.mep_id: mep for mep in MEP.objects.all()}

            for result in results:
                vote_id = result['Identifier']
                vote_title = result.find('RollCallVote.Description.Text').text.strip()

                # delete existing VoteMapping records for this vote_id (adding this while testing code)
                VoteMapping.objects.filter(vote__vote_id=vote_id).delete()

                #update or create vote info
                vote_info, created = VoteInfo.objects.update_or_create(
                    vote_id=vote_id,
                    defaults={
                        'date': vote_date,
                        'label': vote_title,
                    }
                )

                def process_group(vote_type, group):
                    for political_group in group.find_all('Result.PoliticalGroup.List'):
                        for member in political_group.find_all('PoliticalGroup.Member.Name'):
                            mep_id = member.get('PersId')
                            mep_name = member.text.strip()

                            # Skip if MEP ID is 'UNKNOWN'
                            if mep_id == 'UNKNOWN':
                                print(f"Warning: Missing PersId for {mep_name} on date {vote_date}")
                                continue

                            # Fetch the MEP object from cache
                            mep = mep_cache.get(mep_id)

                            if mep:
                                vote_mappings.append(VoteMapping(
                                    vote=vote_info[0],
                                    mep=mep,
                                    vote_type=vote_type
                                ))
                    return True

                for_group = result.find('Result.For')
                if for_group:
                    process_group('Yes', for_group)

                against_group = result.find('Result.Against')
                if against_group:
                    process_group('No', against_group)

                abstentions_group = result.find('Result.Abstentions') or result.find('Result.Abstention')
                if abstentions_group:
                    process_group('Abstain', abstentions_group)

            #Bulk create VoteMapping instances
            VoteMapping.objects.bulk_create(vote_mappings)

            return

        term_id = '9'
        calendar_data = fetch_calendar_data(term_id)

        if calendar_data:
            start_date = datetime.strptime(calendar_data['startDate'], '%d/%m/%Y')
            end_date = datetime.strptime(calendar_data['endDate'], '%d/%m/%Y')

            # checking to see if start and end dates are correct (comment out later)
            # print(f"Start Date: {start_date}, End Date: {end_date}")

            session_calendar = calendar_data.get('sessionCalendar', [])
            urls = []
            date_str_map = {}  # map URLs to their date strings

            for session in session_calendar:
                date_str = f"{session['year']}-{int(session['month']):02d}-{int(session['day']):02d}"
                session_date = datetime.strptime(date_str, '%Y-%m-%d')

                if session_date >= start_date and session_date <= end_date:
                    url = f"https://www.europarl.europa.eu/doceo/document/PV-9-{date_str}-RCV_EN.xml"
                    urls.append(url)
                    date_str_map[url] = date_str

            # print(f"Total URLs to fetch: {len(urls)}")

            loop = asyncio.get_event_loop()
            xml_results = loop.run_until_complete(self.fetch_all_xml(urls))

            #filter out None responses and retain corresponding session dates
            valid_xml_contents = []
            valid_dates = []

            for xml_content, url in xml_results:
                if xml_content:
                    valid_xml_contents.append(xml_content)
                    valid_dates.append(date_str_map[url])

            #verify the lengths of valid_xml_contents and valid_dates (comment out later)
            # print(f"Total valid XML contents: {len(valid_xml_contents)}")
            # print(f"Total valid dates: {len(valid_dates)}")

            for xml_content, date_str in zip(valid_xml_contents, valid_dates):
                parse_xml(xml_content, date_str)
                # print(f"Processed vote data for {date_str}")

            self.stdout.write(self.style.SUCCESS("Vote data saved"))
