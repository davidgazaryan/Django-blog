from django.db import models
from django.contrib.auth.models import User


class Topic(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Room(models.Model):  # Given they are foreignkeys you will see you can only select those topics and hosts that are
    # in the sqlite database, whereas name and description appear as text fields in the room-form page
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Foreignkey is field in one table that refers to primary key of another
    # table, primarykeys are unique
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)  # We refer to the Topic class up above
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=False)  #allows Database to have null value and allows for description to be blank on actual website
    participants = models.ManyToManyField(User, related_name='participant', blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']  # Orders the room so that newest show up at the top, or descending order

    def __str__(self):
        return self.name


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    body = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.body[:2]


class Likes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.room.name




