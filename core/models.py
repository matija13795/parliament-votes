from django.db import models

#Member of European Parlament
class MEP(models.Model):
    unique_identifier = models.IntegerField(unique=True)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    date_of_birth = models.DateField(null=True)
    gender = models.CharField(max_length=6, null=True)
    political_party = models.CharField(max_length=10, null=True)

    def __str__(self):
        return self.first_name + " " + self.last_name


class Vote(models.Model):
    unique_identifier = models.CharField(max_length=250)
    label = models.CharField(max_length=250)

    outcome = models.CharField(max_length=50)
    
    number_of_attendees = models.IntegerField()
    number_of_favor = models.IntegerField()
    number_of_against = models.IntegerField()
    number_of_abstention = models.IntegerField()

    def __str__(self):
        return self.label


class MEP_Vote_Mapping(models.Model):

    choice = models.CharField(max_length=30, null=True)
    mep = models.ForeignKey(MEP, on_delete=models.CASCADE)
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE)