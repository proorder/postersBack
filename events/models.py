from django.db import models
from django import forms
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from rest_framework import serializers
import uuid


class UserManager(BaseUserManager):
    def create_user(self, password, **fields):
        user = self.model(**fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, password, **fields):
        user = self.create_user(password=password, **fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    full_name = models.CharField(max_length=100)
    objects = UserManager()

    def __str__(self):
        return self.full_name


class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ('id', 'full_name', 'username', 'is_staff')


class Event(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=100, default='Title')
    place = models.CharField(max_length=100, default='Place name')
    date = models.DateField()
    info = models.TextField(blank=True)
    cost_of_entry = models.DecimalField(max_digits=7, decimal_places=2)
    latitude = models.DecimalField(max_digits=32, decimal_places=16)
    longitude = models.DecimalField(max_digits=32, decimal_places=16)


def get_file_path(instance, filename, path):
    ext = filename.split('.')[-1]
    filename = '%s.%s' % (uuid.uuid4(), ext)
    return path + filename

def event_image_path(inst, fn):
    return get_file_path(inst, fn, 'events/')

def infrastructures_image_path(inst, fn):
    return get_file_path(inst, fn, 'infrastructures/')


class UploadImagesForm(forms.Form):
    image = forms.ImageField()


class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=event_image_path, null=True, blank=True)

    def __str__(self):
        return str(self.image)


class EventSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(required=False)
    images = serializers.StringRelatedField(many=True)

    class Meta:
        model = Event
        fields = ('id', 'owner', 'title', 'place',
                'date', 'info', 'cost_of_entry', 'latitude',
                'longitude', 'images')


class Infrastructure(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='infrastructures', default=None)
    title = models.CharField(max_length=100, default='Title')
    place = models.CharField(max_length=100, default='Place name')
    info = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=32, decimal_places=16)
    longitude = models.DecimalField(max_digits=32, decimal_places=16)


class InfrastructureSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(required=False)
    images = serializers.StringRelatedField(many=True)

    class Meta:
        model = Infrastructure
        fields = ('id', 'owner', 'title', 'place',
                'info', 'latitude',
                'longitude', 'images')


class InfrastructureImage(models.Model):
    event = models.ForeignKey(Infrastructure, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=infrastructures_image_path, null=True, blank=True)

    def __str__(self):
        return str(self.image)
