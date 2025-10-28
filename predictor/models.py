from django.db import models

class Team(models.Model):
    api_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True, null=True)
    rating = models.FloatField(default=1500.0)

    def __str__(self):
        return self.name

from django.db import models

class Match(models.Model):
    api_id = models.IntegerField(unique=True)
    competition = models.CharField(max_length=100)
    date = models.DateTimeField()
    status = models.CharField(max_length=50)
    home_team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='away_matches')
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)

    # --- Nuevos campos de probabilidades ---
    prob_home_win = models.FloatField(default=0.0)
    prob_draw = models.FloatField(default=0.0)
    prob_away_win = models.FloatField(default=0.0)
    most_likely_home_score = models.IntegerField(default=0)
    most_likely_away_score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"

