from django.db import models


class Video(models.Model):
    video_id = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    channel_id = models.CharField(max_length=100)
    channel_name = models.CharField(max_length=200)
    view_count = models.IntegerField()

    def __str__(self):
        return self.title
