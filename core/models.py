from django.db import models

class MEP(models.Model):
    mep_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=6, null=True)
    date_of_birth = models.DateField(null=True)
    date_of_death = models.DateField(null=True)
    hometown = models.CharField(max_length=58, null=True)
    country_of_representation = models.CharField(max_length=3, null=True)
    combined_name = models.CharField(max_length=100, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Vote(models.Model):
    vote_id = models.CharField(max_length=250)
    label = models.CharField(max_length=250)
    outcome = models.CharField(max_length=50)
    number_of_attendees = models.IntegerField()
    number_of_favor = models.IntegerField()
    number_of_against = models.IntegerField()
    number_of_abstention = models.IntegerField()

    def __str__(self):
        return self.label


class PoliticalGroup(models.Model):
    group = models.CharField(primary_key=True, max_length=89)

    def __str__(self):
        return self.group


class Membership(models.Model):
    mep = models.ForeignKey(MEP, on_delete=models.CASCADE)
    group = models.ForeignKey(PoliticalGroup, on_delete=models.CASCADE)
    start_date = models.DateField(null=True)
    end_date   = models.DateField(null=True)

    def __str__(self):
        return f"{self.mep} - {self.vote} ({self.vote_type})"