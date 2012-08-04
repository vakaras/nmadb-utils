from django.db import models
from django.utils.translation import ugettext_lazy as _


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
            verbose_name=_(u'title'),
            )

    model = models.CharField(
            max_length=80,
            blank=True,
            verbose_name=_(u'model'),
            )

    writer = models.CharField(
            max_length=5,
            choices=AVAILABLE_WRITERS,
            verbose_name=_(u'writer'),
            )

    query = models.TextField(
            verbose_name=_(u'query'),
            help_text=_(
                u'Each column have to be on separate row, in form: '
                u'column caption: field name'),
            )

    class Meta(object):
        ordering = [u'title',]
        verbose_name = _(u'download selection')
        verbose_name_plural = _(u'download selections')

    def __unicode__(self):
        return unicode(self.title)
