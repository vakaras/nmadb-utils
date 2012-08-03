from django.db import models
from django.utils.translation import ugettext as _


class DownloadSelection(models.Model):
    """ DownloadSelection for download as action in admin.
    """

    AVAILABLE_WRITERS = (
            (u'CSV', _(u'Comma separated values')),
            (u'ODS', _(u'Open document spreadsheet')),
            )

    title = models.CharField(
            max_length=80,
            unique=True,
            )

    model = models.CharField(
            max_length=80,
            blank=True,
            )

    writer = models.CharField(
            max_length=5,
            choices=AVAILABLE_WRITERS,
            )

    query = models.TextField(
            help_text=_(
                u'Each column have to be on separate row, in form: '
                u'column caption: field name')
            )

    class Meta(object):
        ordering = [u'title',]

    def __unicode__(self):
        return unicode(self.title)
