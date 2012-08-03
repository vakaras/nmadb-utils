from django.contrib import admin
from django.shortcuts import render
from django import forms
from django.utils.translation import ugettext as _
from django.http import HttpResponse

from pysheets.sheet import Sheet
from pysheets.spreadsheet import SpreadSheet
from pysheets.writers import SheetWriter, SpreadSheetWriter

from nmadb_utils import models


class DownloadSelectedMixin(object):
    """ Download selected mixin for ModelAdmin.
    """

    download_actions = (
            'download_custom_selected',
            'download_selected_as_csv',
            'download_selected_as_ods',
            'download_selected_as_UTF16Tab_csv',
            )

    def dump_query_to_sheet(self, queryset, sheet_mapping, sheet=None):
        """ Dumps query to sheet.
        """

        mapping = []
        captions = []
        related = set()
        for caption, parts in sheet_mapping:
            captions.append(caption)
            mapping.append((caption, parts))
            if len(parts) > 1:
                related.add(u'__'.join(parts[:-1]))

        if sheet is None:
            sheet = Sheet()
        sheet.add_columns(captions)

        for obj in queryset.select_related(*related):
            info = {}
            for caption, field in mapping:
                value = obj
                try:
                    for part in field:
                        value = getattr(value, part)
                except Exception as e:
                    value = _(u'Error: {0}').format(e)
                if hasattr(value, '__call__'):
                    value = value()
                info[caption] = unicode(value)
            sheet.append_dict(info)

        return sheet

    class DownloadSelectionForm(forms.Form):
        """ Simple select field.
        """
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        selection = forms.ModelChoiceField(models.DownloadSelection.objects)

    def download_custom_selected(self, request, queryset):
        """ Allows to download sheet generated with settings, which
        are stored in database.
        """
        form = None
        if 'apply' in request.POST:
            form = self.DownloadSelectionForm(request.POST)

            if form.is_valid():
                selection = form.cleaned_data['selection']
                mapping = []
                for row in selection.query.splitlines():
                    parts = row.split(u':')
                    field = parts[-1].strip()
                    caption = u':'.join(parts[:-1])
                    mapping.append((caption, field.split(u'__')))
                return self.download_selected(
                        queryset, selection.writer, mapping)

        if not form:
            form = self.DownloadSelectionForm(
                    initial={'_selected_action': request.POST.getlist(
                        admin.ACTION_CHECKBOX_NAME)})

        return render(
                request,
                'admin/download_selected.html',
                {'form': form,})
    download_custom_selected.short_description = _(u'Download selected')

    def download_selected(self, queryset, writer_type, sheet_mapping=None):
        """ Generates sheet from queryset for downloading.

        :param writer_type: Sheet writer short name.
        """

        if sheet_mapping is None:
            if hasattr(self, 'sheet_mapping'):
                sheet_mapping = self.sheet_mapping
            else:
                sheet_mapping = [
                        (
                            column.replace(u'__', u':'),
                            column.split(u'__'))
                        for column in self.list_display[1:]
                        ]
        try:
            writer = SheetWriter.plugins[writer_type]
            data = self.dump_query_to_sheet(queryset, sheet_mapping)
        except KeyError:
            writer = SpreadSheetWriter.plugins[writer_type]
            data = SpreadSheet()
            sheet = data.create_sheet(u'Duomenys')
            self.dump_query_to_sheet(queryset, sheet_mapping, sheet)

        response = HttpResponse(mimetype=writer.mime_type)
        response['Content-Disposition'] = (
                _(u'attachment; filename=data.{0}').format(
                    writer.file_extensions[0]))
        data.write(response, writer=writer())
        return response

    def download_selected_as_csv(self, request, queryset):
        """ Generates CSV from queryset for download.
        """
        return self.download_selected(queryset, u'CSV')
    download_selected_as_csv.short_description = _(u'Download as CSV.')

    def download_selected_as_ods(self, request, queryset):
        """ Generates ODS from queryset for download.
        """
        return self.download_selected(queryset, u'ODS')
    download_selected_as_ods.short_description = _(u'Download as ODS.')

    def download_selected_as_UTF16Tab_csv(self, request, queryset):
        """ Generates CSV from queryset for download.
        """
        writer = SheetWriter.plugins[u'CSV']
        data = utils.dump_query_to_sheet(queryset)

        response = HttpResponse(mimetype=writer.mime_type)
        response['Content-Disposition'] = (
                _('attachment; filename=data.csv'))
        data.write(
                response,
                writer=writer(quotechar='\t', encoding='utf-16'),)
        return response
    download_selected_as_UTF16Tab_csv.short_description = (
            _(u'Download as UTF16 CSV.'))


class ModelAdmin(DownloadSelectedMixin, admin.ModelAdmin):
    """ Base model admin for NMADB.
    """

    actions = list(DownloadSelectedMixin.download_actions)



class DownloadSelectionAdmin(ModelAdmin):
    """ Administration for DownloadSelection.
    """

    list_display = (
            'id',
            'title',
            'model',
            'writer',
            )

    list_filter = (
            'writer',
            )

    search_fields = (
            'id',
            'title',
            'model',
            )


admin.site.register(models.DownloadSelection, DownloadSelectionAdmin)
