""" Module that provides some functionality for sending mass mail.
"""


from django.core import mail
from django.utils.encoding import smart_str


def send_mass_mail(
        email_addresses, title, text,
        attachment1=None, attachment1_label=None,
        attachment2=None, attachment2_label=None,
        attachment3=None, attachment3_label=None,
        **backend_args):
    """ Sends emails using custom connection.

    .. todo::
        Add support for HTML emails (maybe with images). Urls:

        +   http://djangosnippets.org/snippets/2215/
        +   https://docs.djangoproject.com/en/dev/topics/email/
        +   http://djangosnippets.org/snippets/1710/

    """

    attachment1_data = attachment1.read() if attachment1 else None
    attachment2_data = attachment2.read() if attachment2 else None
    attachment3_data = attachment3.read() if attachment3 else None

    emails = []
    for email_address in email_addresses:
        email = mail.EmailMessage(title)
        email.body = text
        email.from_email = backend_args['username']
        email.to = [email_address]
        if attachment1:
            email.attach(
                    smart_str(attachment1_label or _(u'attachment 1')),
                    attachment1_data)
        if attachment2:
            email.attach(
                    smart_str(attachment2_label or _(u'attachment 2')),
                    attachment2_data)
        if attachment3:
            email.attach(
                    smart_str(attachment3_label or _(u'attachment 3')),
                    attachment3_data)
        emails.append(email)

    for i in range(0, len(emails), 7):
        connection = mail.get_connection(use_tls=True, **backend_args)
        connection.send_messages(emails[i:i + 7])
