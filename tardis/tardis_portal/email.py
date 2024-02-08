from os import path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

email_template_dir = "tardis_portal/email/"


def email_user(subject, template_filename, context, user):

    to_email = [user.email]

    from_email = settings.EMAIL_HOST_USER

    msg = EmailMultiAlternatives(
        subject, build_template_text(template_filename, context), from_email, to_email
    )

    msg.attach_alternative(build_template_html(template_filename, context), "text/html")

    msg.send()


def build_template_text(template_filename, context):
    template_filename_text = template_filename + ".txt"
    plaintext = get_template(path.join(email_template_dir, template_filename_text))
    text_content = plaintext.render(context)
    return text_content


def build_template_html(template_filename, context):
    template_filename_html = template_filename + ".html"
    htmly = get_template(path.join(email_template_dir, template_filename_html))
    html_content = htmly.render(context)
    return html_content
