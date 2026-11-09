from django.contrib import admin

# Register your models here.
from . models import AssignedProjects,Project,Task

admin.site.register(Project)

admin.site.register(AssignedProjects)

admin.site.register(Task)