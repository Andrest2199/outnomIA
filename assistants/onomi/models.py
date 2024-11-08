# Create your models here.
from django.db import models
import json


class QuestionToAnswer(models.Model):
    question = models.CharField(max_length=5000)
    compania = models.CharField(max_length=10)
    database = models.CharField(max_length=50)
    response = models.TextField()
    tokens = models.FloatField()

    def to_json(self):
        return {
            "question": self.question,
            "compania": self.compania,
            "database": self.database,
            "response": self.response,
        }

    def __str__(self):
        return self.question
