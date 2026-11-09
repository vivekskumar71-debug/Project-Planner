from django.shortcuts import render

from rest_framework.response import Response

from rest_framework.views import APIView

from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView,ListAPIView

from . models import Project,Task

from . models import AssignedProjects

from .serializers import AssignedProjectsSerializer,TaskSerializer,ProjectSerializer

from planner.utils import generate_tasks

from django.db import transaction

from authentication.permissions import IsAdmin,IsProjectCoordinator

from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.permissions import IsAuthenticated

# Create your views here.

class ProjectListCreateView(ListCreateAPIView) :

    authentication_classes = [JWTAuthentication]

    def get_permissions(self):

        if self.request.method == 'POST' :

            permissions = [IsAdmin]

        else :

            permissions = [IsAuthenticated]

        return [permission() for permission in permissions]
            
    queryset = Project.objects.filter(active_status=True)

    serializer_class = ProjectSerializer

class ProjectRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView) :

    authentication_classes = [JWTAuthentication]

    def get_permissions(self):

        if self.request.method == 'PATCH' or self.request.method == 'DELETE' :

            permissions = [IsAdmin]

        else :

            permissions = [IsAuthenticated]

        return [permission() for permission in permissions]
            
    lookup_field = 'uuid'

    queryset = Project.objects.filter(active_status=True)

    serializer_class = ProjectSerializer

    def perform_destroy(self, instance):  # this fuction is used to make any changes from ourself 
                                          #to the delete operation. Here we are doing only soft delete
        instance.active_status = False

        instance.save()

class AssignedProjectsListCreateView(ListCreateAPIView) :

    authentication_classes = [JWTAuthentication]

    def get_permissions(self):

        if self.request.method == 'POST' :

            permissions = [IsAdmin|IsProjectCoordinator]

        else :

            permissions = [IsAuthenticated]

        return [permission() for permission in permissions]

    queryset = AssignedProjects.objects.filter(active_status=True).select_related('project','coordinator').prefetch_related('developers')
    # select_related for foreign key , ... prefetch_related for many to many field  both for reducing time complexity

    serializer_class = AssignedProjectsSerializer

class AssignedProjectsRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView) :

    authentication_classes = [JWTAuthentication]
    
    def get_permissions(self):
    
        if self.request.method == 'PATCH' or self.request.method == 'DELETE' :
    
            permissions = [IsAdmin|IsProjectCoordinator]

        else :

            permissions = [IsAuthenticated]
    
        return [permission() for permission in permissions]

    lookup_field = 'uuid'

    queryset = AssignedProjects.objects.filter(active_status=True).select_related('project','coordinator').prefetch_related('developers')

    serializer_class = AssignedProjectsSerializer

    def perform_destroy(self, instance):

        instance.active_status = False 
 
        instance.save()

class TaskListCreateView(ListCreateAPIView) :

    authentication_classes = [JWTAuthentication]

    serializer_class = TaskSerializer

    def get_permissions(self) :

        if self.request.method == 'POST' :

            permissions = [IsProjectCoordinator]

        else : 

            permissions = [IsAuthenticated]

        return [permission() for permission in permissions]
    
    def get_queryset(self):

        uuid = self.kwargs.get('uuid')

        assigned_project = AssignedProjects.objects.get(uuid=uuid)

        tasks = Task.objects.filter(active_status=True,assigned_project=assigned_project)

        return tasks

    def perform_create(self, serializer):
        
        uuid = self.kwargs.get('uuid')

        assigned_project = AssignedProjects.objects.get(uuid=uuid)

        data_copy = serializer.validated_data.copy()

        data_copy['assigned_project'] = assigned_project

        serializer.save(assigned_project=assigned_project)

class TaskRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView) :

    authentication_classes = [JWTAuthentication]

    def get_permissions(self):

        if self.request.method == 'PATCH' or self.request.method == 'DELETE' :

            permissions = [IsAdmin]

        else :

            permissions = [IsAuthenticated]

        return [permission() for permission in permissions]

    lookup_field = 'uuid'

    queryset = Task.objects.filter(active_status=True).select_related('assigned_project','assigned_to')

    serializer_class = TaskSerializer
    
    def perform_destroy(self, instance):  # this fuction is used to make any changes from ourself 
                                              #to the delete operation. Here we are doing only soft delete
        instance.active_status = False
    
        instance.save()

class GenerateTaskWithAIView(APIView) :

    authentication_classes = [JWTAuthentication]

    permission_classes = [IsAuthenticated]

    def post(self,request,*args,**kwargs) :

        uuid = kwargs.get('uuid')

        assigned_project = AssignedProjects.objects.get(uuid=uuid)

        response,developers = generate_tasks(assigned_project)

        tasks = [Task(

            assigned_project = assigned_project,
            assigned_to_id = task.developer_id,
            title = task.title,
            description = task.description,
            priority = task.priority
        )  
        for task in response.tasks if task.developer_id in developers]

        with transaction.atomic() :

            Task.objects.bulk_create(tasks)

        return Response(status=200)