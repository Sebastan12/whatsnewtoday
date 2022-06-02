from django.db import models

# Create your models here.
class Articles(models.Model):
    url = models.CharField(max_length=255, unique=True)

class Image(models.Model):
    article_id = models.ForeignKey(Articles, on_delete=models.CASCADE)
    hash = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    price = models.FloatField()
    description = models.TextField()
    is_searching_for = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)