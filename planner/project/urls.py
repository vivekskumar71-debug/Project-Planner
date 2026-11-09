from django.urls import path

from . import views

urlpatterns = [

    path('projects/',views.ProjectListCreateView.as_view()),
    path('projects/<str:uuid>/',views.ProjectRetrieveUpdateDestroyView.as_view()),
    path('assigned-projects/',views.AssignedProjectsListCreateView.as_view()),
    path('assigned-projects/<str:uuid>/',views.AssignedProjectsRetrieveUpdateDestroyView.as_view()),
    path('tasks/<str:uuid>/',views.TaskListCreateView.as_view()),
    path('task-retrieve-update-destroy/<str:uuid>/',views.TaskRetrieveUpdateDestroyView.as_view()),
    path('generate-tasks/<str:uuid>/',views.GenerateTaskWithAIView.as_view())
]