# Create your models here.
from django.db import models
import json


class QuestionToAnswer(models.Model):
    question = models.CharField(max_length=5000)
    id_employee = models.TextField(max_length=10)
    compania = models.CharField(max_length=10)
    database = models.CharField(max_length=50)
    response = models.JSONField()
    thread_id = models.CharField(max_length=100)
    tokens = models.FloatField()

    def to_json(self):
        return {
            "question": self.question,
            "id_employee": self.id_employee,
            "compania": self.compania,
            "database": self.database,
            "response": self.response,
            "thread_id": self.thread_id,
            "tokens_use": self.tokens
        }

    def __str__(self):
        return self.question
