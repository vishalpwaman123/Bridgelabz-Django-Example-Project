from django.db import models


# Create your models here.
class Register(models.Model):
    username = models.CharField(blank=False, max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=20)
    confirm_password = models.CharField(max_length=20)

    def __str__(self):
        return self.username
