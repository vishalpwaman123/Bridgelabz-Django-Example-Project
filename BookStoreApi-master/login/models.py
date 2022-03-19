from django.db import models

# Create your models here.
class User:

    def __init__(self):
        self.id = None
        self.username = None
        self.email = None
        self.mobilenum = None
        self.password = None

    def save(self):
        if self.id is not None:
            self.objects.update(self)
        else:
            self.objects.insert(self)
