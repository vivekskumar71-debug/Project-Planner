from django.db import models

from django.contrib.auth.models import AbstractUser

class RoleChoices(models.TextChoices) :

    DEVELOPER = 'Dveloper','Developer'

    ADMIN = 'Admin','Admin'

    PROJECT_COORDINATOR = 'Project Coordinator','Project Coordinator'
        
class Profile(AbstractUser) :

    role = models.CharField(max_length=20,choices=RoleChoices.choices)

    class Meta :

        verbose_name = 'Profiles'

        verbose_name_plural = 'Profiles'

    def __str__(self) :

        return self.username

     