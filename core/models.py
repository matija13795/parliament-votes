from django.db import models

class MEP(models.Model):
    unique_identifier = models.IntegerField()
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True)
    gender = models.CharField(max_length=6, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# Meeting model to store meeting data
class Meeting(models.Model):
    activity_id = models.CharField(max_length=255, unique=True)
    activity_type = models.CharField(max_length=255)

class Vote(models.Model):
    unique_identifier = models.CharField(max_length=250)
    outcome = models.CharField(max_length=50)
    number_of_attendees = models.IntegerField()
    number_of_favor = models.IntegerField()
    number_of_against = models.IntegerField()
    number_of_abstention = models.IntegerField()

    def __str__(self):
        return self.label


class MEPVoteMapping(models.Model):
    mep = models.ForeignKey(MEP, on_delete=models.CASCADE)
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=50)  # 'favor', 'against', 'abstention', 'no_vote'

    def __str__(self):
        return f"{self.mep} - {self.vote} ({self.vote_type})"
