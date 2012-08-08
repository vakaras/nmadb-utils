from django import template

from nmadb_utils.actions import Action


class ActionListNode(template.Node):
    """ NMADB action list representation.
    """

    def __init__(self, varname):
        self.varname = varname

    def __repr__(self):
        return "<GetNMADBActionList Node>"

    def render(self, context):
        context[self.varname] = Action.actions
        return ''


class DoGetActionList(object):
    """
    Populates a template variable with the NMADB actions list.

    Usage::

        {% get_nmadb_action_list as [varname] %}

    Examples::

        {% get_nmadb_action_list as actions %}

    """
    def __init__(self, tag_name):
        self.tag_name = tag_name

    def __call__(self, parser, token):
        tokens = token.contents.split()
        if len(tokens) != 3:
            raise template.TemplateSyntaxError(
                    "'{0}' statements require one argument".format(
                        self.tag_name))
        if tokens[1] != 'as':
            raise template.TemplateSyntaxError(
                    "Second argument in '{0}' must be 'as'".format(
                        self.tag_name))
        return ActionListNode(varname=tokens[2])


register = template.Library()
register.tag(
    'get_nmadb_action_list', DoGetActionList('get_nmadb_action_list'))
