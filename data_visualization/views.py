from django.shortcuts import render, get_object_or_404
from core.models import MEP, VoteInfo, VoteMapping, Membership
from collections import defaultdict

def index(request):
    query = request.GET.get('q') #gets the query from the search bar
    results = None
    if query:
        results = VoteInfo.objects.filter(vote_id=query)
    return render(request, 'data_visualization/index.html', {'results': results, 'query': query})

def vote_detail(request, vote_id):
    vote = get_object_or_404(VoteInfo, vote_id=vote_id)
    vote_mappings = VoteMapping.objects.filter(vote=vote)
    
    political_groups = defaultdict(list)
    total_yes = 0
    total_no = 0
    total_abstain = 0
    total_votes = vote_mappings.count()
    
    for mapping in vote_mappings:
        mep = mapping.mep
        mep_name = f"{mep.first_name} {mep.last_name}"

        #vote counts
        if mapping.vote_type == 'Yes':
            total_yes += 1
        elif mapping.vote_type == 'No':
            total_no += 1
        elif mapping.vote_type == 'Abstain':
            total_abstain += 1

        # Find the correct political group for the MEP at the time of the vote
        mep_memberships = Membership.objects.filter(
            mep_id=mep.mep_id,
            start_date__lte=vote.date,
            end_date__gte=vote.date
        )

        if mep_memberships.exists():
            mep_membership = mep_memberships.first()
            political_groups[mep_membership.group.group].append({
                'mep_name': mep_name,
                'mep_id': mep.mep_id,
                'vote_type': mapping.vote_type
            })
            print(f"MEP {mep_name} voted with {mep_membership.group.group} on {vote.date}")
        else:
            print(f"No membership found for MEP {mep_name} at the time of the vote on {vote.date}")

    # prints to remove later
    for group_key, meps in political_groups.items():
        print(f"Group: {group_key}")
        for mep in meps:
            print(f"  MEP Name: {mep['mep_name']}, MEP ID: {mep['mep_id']}, Vote Type: {mep['vote_type']}, Group: {group_key}")

    print(political_groups)
    return render(request, 'data_visualization/vote_detail.html', {
        'vote': vote,
        'total_votes': total_votes,
        'total_yes': total_yes,
        'total_no': total_no,
        'total_abstain': total_abstain,
        'political_groups': dict(political_groups)
    })