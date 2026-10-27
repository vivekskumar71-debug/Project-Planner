import string

import random

from django.core.mail import EmailMultiAlternatives

from django.template.loader import render_to_string

from django.conf import settings

def  generate_password() :

    password = ''.join(random.choices(string.ascii_letters+string.digits,k=8))

    return password

def send_email(recipient,subject,context,template) :

    email = EmailMultiAlternatives(from_email=settings.EMAIL_HOST_USER,subject=subject,to=[recipient])

    content = render_to_string(template,context)

    email.attach_alternative(content,mimetype='text/html')

    email.send()
