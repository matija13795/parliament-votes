from django.db import models

class MEP(models.Model):
    mep_id = models.IntegerField()
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True)
    gender = models.CharField(max_length=6, null=True)
    combined_name = models.CharField(max_length=100, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Vote(models.Model):
    vote_id = models.CharField(max_length=250)
    mep_id = models.IntegerField()
    mep_name = models.CharField(max_length=255)
    description = models.TextField()
    vote_type = models.CharField(max_length=255)

    def __str__(self):
        return self.label
