import string

import random

from django.core.mail import EmailMultiAlternatives

from django.template.loader import render_to_string

from django.conf import settings

from datetime import timedelta
from typing import List, Literal

from decouple import config
from django.db import transaction
from django.utils.html import strip_tags
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from project.models import Task

def  generate_password() :

    password = ''.join(random.choices(string.ascii_letters+string.digits,k=8))

    return password

def send_email(recipient,subject,context,template) :

    email = EmailMultiAlternatives(from_email=settings.EMAIL_HOST_USER,subject=subject,to=[recipient])

    content = render_to_string(template,context)

    email.attach_alternative(content,mimetype='text/html')

    email.send()



client = genai.Client(api_key=config('GEMINI_API_KEY'))

class GeneratedTask(BaseModel):
    title: str = Field(description="Short task title")
    description: str = Field(description="What needs to be done, with clear deliverables")
    developer_id: int = Field(description="ID of the developer this task is assigned to")
    priority: Literal['Low', 'Medium', 'High']


class TaskPlan(BaseModel):
    tasks: List[GeneratedTask]


def generate_tasks(assigned_project):

    project = assigned_project.project
    developers = list(assigned_project.developers.all())

    if not developers:
        raise ValueError('No developers are assigned to this project.')

    developer_lines = '\n'.join(
        f'- id: {dev.id}, name: {dev.first_name or dev.username}, tech: {dev.tech}'
        for dev in developers
    )

    allowed_ids = ', '.join(str(dev.id) for dev in developers)

    prompt = f"""
You are an experienced technical project manager planning work for a software team.
Break the project below into concrete, development-ready tasks and assign each
task to exactly one of the listed developers.

PROJECT NAME:
{project.name}

PROJECT DESCRIPTION:
{strip_tags(project.description)}

DEVELOPERS:
{developer_lines}

Rules:
1. Create between 5 and 20 tasks that together cover the whole project.
2. developer_id MUST be one of these IDs only: {allowed_ids}.
   Never use any other number, never invent or guess an ID, and never leave it empty.
   If a task does not fit any listed developer, do not create that task.
3. Assign each task based on the developer's tech:
   - Frontend Developer: UI pages, components, client-side API integration
   - Backend Developer: APIs, database, business logic, auth, deployment
   - Fullstack Developer: can take frontend or backend tasks
   - UI/UX Designer: wireframes, mockups, design system, user flows
   - Software Tester: test plans, test cases, QA, bug verification
4. Never give a task to a developer whose tech does not fit it. If no one on the
   team has the tech for some work, do not create tasks for that work.
5. Spread the work fairly among developers who share the same tech.
6. Order tasks logically (design and setup first, testing and deployment last).
7. priority must be exactly one of: Low, Medium, High.
8. Keep titles short and descriptions specific.
9. Return only the requested structured output.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TaskPlan,
        ),
    )

    return response.parsed, [dev.id for dev in developers]


