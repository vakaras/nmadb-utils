#!/usr/bin/python


from django.core.urlresolvers import reverse


class Action(object):
    """ NMADB action.
    """

    actions = []

    def __init__(self, short_description, url_name):
        self.short_description = short_description
        self.url_name = url_name

    @property
    def url(self):
        """ Returns url to action.
        """
        return reverse(self.url_name)


def register(short_description, url_name):
    """ Creates action and adds to list.
    """
    Action.actions.append(Action(short_description, url_name))
