from django.contrib import admin
from django.shortcuts import render
from django import forms
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.contrib.contenttypes.models import ContentType

from pysheets.sheet import Sheet
from pysheets.spreadsheet import SpreadSheet
from pysheets.writers import SheetWriter, SpreadSheetWriter

from django_db_utils.forms import SpreadSheetField

from nmadb_utils import models


def get_field_value(obj, parts):
    """ Returns the value of the object field.

    If it is callable, then returns its result.
    """
    value = obj
    try:
        for part in parts:
            value = getattr(value, part)
        if hasattr(value, '__call__'):
            value = value()
    except Exception as e:
        value = _(u'Error: {0}').format(e)
    return value


class DownloadSelectedMixin(object):
    """ Download selected mixin for ModelAdmin.
    """

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
                info[caption] = unicode(get_field_value(obj, field))
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


class AllObjectsActionMixin(object):
    """ Perform action on all objects without selecting them.

    .. todo::
        Make to work.
    """

    def response_action(self, request, queryset):
        """ Overriding to allow calling without selecting any objects.

        Based on `answer on StackOverflow
        <http://stackoverflow.com/questions/4500924/django-admin-action-without-selecting-objects>`_.
        """
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        data = request.POST.copy()
        print 'Veikia 1'
        if (data['action'] in self.actions_without_selection):
            print 'Veikia 2'
            if len(selected) == 0:
                print 'Veikia 3'
                ct = ContentType.objects.get_for_model(queryset.model)
                klass = ct.model_class()
                queryset = klass.objects.all()
                return getattr(self, data['action'])(request, queryset)
            else:
                print 'Veikia 4'
                msg = _(u'For this action no items must be selected. '
                        u'No items have been changed.')
                self.message_user(request, msg)
                return None
        else:
            print 'Veikia 5'
            return super(AllObjectsActionMixin, self).response_action(
                    request, queryset)


class FillMisingMixin(object):
    """ Fill missing data in sheet from database mixin for ModelAdmin.
    """

    def generate_spreadsheet(self, klass, sheet_mapping, data):
        """ Generates spreadsheet.
        """

        mapping = []
        mapping_dict = {}
        captions = []
        related = set()
        for caption, parts in sheet_mapping:
            captions.append(caption)
            mapping.append((caption, parts))
            mapping_dict[caption] = parts
            if len(parts) > 1:
                related.add(u'__'.join(parts[:-1]))

        spreadsheet = SpreadSheet()
        make_provided = lambda x: x + u' (provided)'
        for sheet in data:
            keys = set(sheet.captions) & set(captions)
            provided_captions = [
                    make_provided(caption) for caption in sheet.captions]
            new_sheet = spreadsheet.create_sheet(
                    sheet.name,
                    captions=provided_captions + captions)
            fill_columns = len(captions)
            for row in sheet:
                query = dict(
                        (u'__'.join(mapping_dict[key]), row[key])
                        for key in keys
                        )
                try:
                    obj = klass.objects.get(**query)
                except Exception as e:
                    new_sheet.append_iterable(
                            list(row) +
                            [_(u'Error: {0}').format(e)] * fill_columns)
                else:
                    info = dict(
                            (make_provided(key), row[key])
                            for key in row.keys())
                    for caption, field in mapping:
                        info[caption] = unicode(
                                get_field_value(obj, field))
                    new_sheet.append_dict(info)
        return spreadsheet

    class FillMissingForm(forms.Form):
        """ Simple select field.
        """
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        selection = forms.ModelChoiceField(models.DownloadSelection.objects)
        spreadsheet = SpreadSheetField(sheet_name=_(u'Data'))

    def fill_missing(self, request, queryset):
        """ Allows to download sheet filled with missing data from
        database.

        Settings are stored in database.
        """
        form = None
        if 'apply' in request.POST:
            form = self.FillMissingForm(request.POST, request.FILES)

            if form.is_valid():
                selection = form.cleaned_data['selection']
                mapping = []
                for row in selection.query.splitlines():
                    parts = row.split(u':')
                    field = parts[-1].strip()
                    caption = u':'.join(parts[:-1])
                    mapping.append((caption, field.split(u'__')))

                data = form.cleaned_data['spreadsheet']
                ct = ContentType.objects.get_for_model(queryset.model)
                klass = ct.model_class()
                spreadsheet = self.generate_spreadsheet(
                        klass,
                        mapping,
                        data,
                        )
                writer = SpreadSheetWriter.plugins[u'ODS']
                response = HttpResponse(mimetype=writer.mime_type)
                response['Content-Disposition'] = (
                        _(u'attachment; filename=data.{0}').format(
                            writer.file_extensions[0]))
                spreadsheet.write(response, writer=writer())
                return response

        if not form:
            form = self.FillMissingForm(
                    initial={'_selected_action': request.POST.getlist(
                        admin.ACTION_CHECKBOX_NAME)})

        return render(
                request,
                'admin/fill_missing.html',
                {'form': form,})
    fill_missing.short_description = _(u'Fill missing')


class ModelAdmin(
        FillMisingMixin,
        DownloadSelectedMixin,
        admin.ModelAdmin,
        ):
    """ Base model admin for NMADB.
    """

    actions = [
            'download_custom_selected',
            'download_selected_as_csv',
            'download_selected_as_ods',
            'download_selected_as_UTF16Tab_csv',
            'fill_missing',
            ]


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
