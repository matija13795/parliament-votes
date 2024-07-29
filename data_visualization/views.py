from django.shortcuts import render, get_object_or_404
from core.models import MEP, VoteInfo, VoteMapping, Membership
from collections import defaultdict
from io import BytesIO
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import textwrap
import json
import datetime
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q
import pycountry

# libraries to install
# numpy, matplotlib, textwrap, pycountry

def wrap_text(text, width):
    return "\n".join(textwrap.wrap(text, width))

def get_country_name(alpha_3_code):
    try:
        return pycountry.countries.get(alpha_3=alpha_3_code).name
    except AttributeError:
        return None

def index(request):
    query = request.GET.get('q')  # gets the query from the search bar
    results = None
    if query:
        try:
            # to parse the query as a date
            query_date = datetime.datetime.strptime(query, '%Y-%m-%d')
            results = VoteInfo.objects.filter(date=query_date)
        except ValueError:
            # if in case query is not a date, search by year or description
            if query.isdigit():
                results = VoteInfo.objects.filter(date__year=query)
            else:
                results = VoteInfo.objects.filter(label__icontains=query)
    
    # get all vote dates and their votes to highlight in the calendar
    all_votes = VoteInfo.objects.all()
    votes_by_date = {}
    for vote in all_votes:
        date_str = vote.date.strftime('%Y-%m-%d')
        if date_str not in votes_by_date:
            votes_by_date[date_str] = []
        votes_by_date[date_str].append({
            'vote_id': vote.vote_id,
            'label': vote.label
        })
    
    return render(request, 'data_visualization/index.html', {
        'results': results,
        'query': query,
        'votes_by_date': json.dumps(votes_by_date, cls=DjangoJSONEncoder)
    })

def get_country_name(alpha_3_code):
    try:
        return pycountry.countries.get(alpha_3=alpha_3_code).name
    except AttributeError:
        return None

def vote_detail(request, vote_id):
    vote = get_object_or_404(VoteInfo, vote_id=vote_id)
    vote_mappings = VoteMapping.objects.filter(vote=vote)

    political_groups = defaultdict(list)
    country_votes = defaultdict(list)  # Store MEPs and their votes by country

    total_yes = 0
    total_no = 0
    total_abstain = 0
    votes_count = vote_mappings.count()

    for mapping in vote_mappings:
        mep = mapping.mep
        mep_name = f"{mep.first_name} {mep.last_name}"

        # Count votes
        if mapping.vote_type == 'Yes':
            total_yes += 1
        elif mapping.vote_type == 'No':
            total_no += 1
        elif mapping.vote_type == 'Abstain':
            total_abstain += 1

        # Find the correct political group for the MEP at the time of the vote
        mep_memberships = Membership.objects.filter(
            mep_id=mep.mep_id,
            start_date__lte=vote.date
        ).filter(
            end_date__gte=vote.date
        ) | Membership.objects.filter(
            mep_id=mep.mep_id,
            start_date__lte=vote.date,
            end_date__isnull=True
        )


        if mep_memberships.exists():
            mep_membership = mep_memberships.first()
            political_groups[mep_membership.group.group].append({
                'mep_name': mep_name,
                'mep_id': mep.mep_id,
                'vote_type': mapping.vote_type
            })
        else:
            print(f"No membership found for MEP {mep_name} at the time of the vote on {vote.date}")

        # Get MEP's country
        country = mep.country_of_representation
        if country:
            country_votes[country].append({
                'mep_name': mep_name,
                'mep_id': mep.mep_id,
                'vote_type': mapping.vote_type
            })

    vote_id = vote.vote_id
    vote_date = vote.date
    vote_label = vote.label

    # Calculate percentages
    if votes_count > 0:
        percent_yes = (total_yes / votes_count) * 100
        percent_no = (total_no / votes_count) * 100
        percent_abstain = (total_abstain / votes_count) * 100
    else:
        percent_yes = percent_no = percent_abstain = 0

    # Create the Likert plot for political groups
    category_names = ['No', 'Abstain', 'Yes']
    results = {group: [0, 0, 0] for group in political_groups.keys()}
    for group, votes in political_groups.items():
        for vote in votes:
            if vote['vote_type'] == 'No':
                results[group][0] += 1
            elif vote['vote_type'] == 'Abstain':
                results[group][1] += 1
            elif vote['vote_type'] == 'Yes':
                results[group][2] += 1

    # Create the Likert plot for countries
    country_results = {country: [0, 0, 0] for country in country_votes.keys()}
    for country, votes in country_votes.items():
        for vote in votes:
            if vote['vote_type'] == 'No':
                country_results[country][0] += 1
            elif vote['vote_type'] == 'Abstain':
                country_results[country][1] += 1
            elif vote['vote_type'] == 'Yes':
                country_results[country][2] += 1

    # Calculate the in favor percentages
    country_percentages = {}
    for country, votes in country_votes.items():
        total_votes = sum(1 for vote in votes if vote['vote_type'] != 'Present but did not vote')
        yes_votes = sum(1 for vote in votes if vote['vote_type'] == 'Yes')
        in_favor_percentage = (yes_votes / total_votes) * 100 if total_votes > 0 else 0
        country_full_name = get_country_name(country)
        if country_full_name:
            country_percentages[country_full_name] = in_favor_percentage

    def survey(results, category_names, wrap_width=20):
        labels = [wrap_text(label, wrap_width) for label in results.keys()]
        data = np.array(list(results.values()))
        data_cum = data.cumsum(axis=1)
        middle_index = data.shape[1] // 2
        offsets = data[:, range(middle_index)].sum(axis=1) + data[:, middle_index] / 2
        
        category_colors = ['#EE2233', '#FFC000', '#508D69']
        
        fig, ax = plt.subplots(figsize=(12, 7))
        
        for i, (colname, color) in enumerate(zip(category_names, category_colors)):
            widths = data[:, i]
            starts = data_cum[:, i] - widths - offsets
            rects = ax.barh(labels, widths, left=starts, height=0.5,
                            label=colname, color=color)
        
        ax.axvline(0, linestyle='--', color='black', alpha=.25)
        ax.set_xlim(-sum(max(data, key=sum)), sum(max(data, key=sum)))
        ax.xaxis.set_major_formatter(lambda x, pos: str(abs(int(x))))
        ax.invert_yaxis()
        ax.legend(ncol=len(category_names), bbox_to_anchor=(0, 1),
                  loc='lower left', fontsize='small')
        
        fig.set_facecolor('#FFFFFF')
        fig.tight_layout()

        return fig, ax

    # Political groups chart
    fig1, ax1 = survey(results, category_names)
    buf1 = BytesIO()
    fig1.savefig(buf1, format="png")
    buf1.seek(0)
    string1 = base64.b64encode(buf1.read())
    uri1 = 'data:image/png;base64,' + string1.decode('utf-8')

    # Countries chart
    fig2, ax2 = survey(country_results, category_names)
    buf2 = BytesIO()
    fig2.savefig(buf2, format="png")
    buf2.seek(0)
    string2 = base64.b64encode(buf2.read())
    uri2 = 'data:image/png;base64,' + string2.decode('utf-8')
    
    return render(request, 'data_visualization/vote_detail.html', {
        'vote': vote,
        'vote_date': vote_date,
        'vote_label': vote_label,
        'vote_id': vote_id,
        'total_votes': votes_count,
        'total_yes': total_yes,
        'total_no': total_no,
        'total_abstain': total_abstain,
        'percent_yes': percent_yes,
        'percent_no': percent_no,
        'percent_abstain': percent_abstain,
        'political_groups': dict(political_groups),
        'country_votes': dict(country_votes),
        'chart_groups': uri1,
        'chart_countries': uri2,
        'country_percentages': country_percentages  
    })
