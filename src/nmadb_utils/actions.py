#!/usr/bin/python


from django.core.urlresolvers import reverse


class Action(object):
    """ NMADB action.
    """

    actions = []

    def __init__(self, gid, short_description, url_name):
        self.gid = gid
        self.short_description = short_description
        self.url_name = url_name

    @property
    def url(self):
        """ Returns url to action.
        """
        return reverse(self.url_name)


class DuplicateGid(Exception):
    """ Duplicated gid exception.
    """


def register(gid, short_description, url_name):
    """ Creates action and adds to list.
    """
    for action in Action.actions:
        if gid == action.gid:
            raise DuplicateGid(u'gid: {0}'.format(gid))
    Action.actions.append(Action(gid, short_description, url_name))


def unregister(gid):
    """ Deletes action with specified gid.
    """
    for i, action in enumerate(Action.actions):
        if gid == action.gid:
            del Action.actions[i]
            return
