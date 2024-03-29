#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 Doug Hellmann.  All rights reserved.
#
"""Integration of Sphinx with BitBucket.
"""

from docutils import nodes, utils
from docutils.parsers.rst.roles import set_classes

def make_link_node(rawtext, app, type, slug, options):
    """Create a link to a BitBucket resource.

    :param rawtext: Text being replaced with link node.
    :param app: Sphinx application context
    :param type: Link type (issue, changeset, etc.)
    :param slug: ID of the thing to link to
    :param options: Options dictionary passed to role func.
    """
    # 
    try:
        base = app.config.bitbucket_project_url
        if not base:
            raise AttributeError
    except AttributeError as err:
        raise ValueError('bitbucket_project_url configuration value is not set (%s)' % str(err))
    #
    slash = '/' if base[-1] != '/' else ''
    ref = base + slash + type + '/' + slug + '/'
    set_classes(options)
    node = nodes.reference(rawtext, type + ' ' + utils.unescape(slug), refuri=ref,
                           **options)
    return node
    

def bbissue_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """Link to a BitBucket issue.

    Returns 2 part tuple containing list of nodes to insert into the
    document and a list of system messages.  Both are allowed to be
    empty.

    :param name: The role name used in the document.
    :param rawtext: The entire markup snippet, with role.
    :param text: The text marked with the role.
    :param lineno: The line number where rawtext appears in the input.
    :param inliner: The inliner instance that called us.
    :param options: Directive options for customization.
    :param content: The directive content for customization.
    """
    try:
        issue_num = int(text)
        if issue_num <= 0:
            raise ValueError
    except ValueError:
        msg = inliner.reporter.error(
            'BitBucket issue number must be a number greater than or equal to 1; '
            '"%s" is invalid.' % text, line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]
    app = inliner.document.settings.env.app
    #app.info('issue %r' % text)
    node = make_link_node(rawtext, app, 'issue', str(issue_num), options)
    return [node], []

def bbchangeset_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """Link to a BitBucket changeset.

    Returns 2 part tuple containing list of nodes to insert into the
    document and a list of system messages.  Both are allowed to be
    empty.

    :param name: The role name used in the document.
    :param rawtext: The entire markup snippet, with role.
    :param text: The text marked with the role.
    :param lineno: The line number where rawtext appears in the input.
    :param inliner: The inliner instance that called us.
    :param options: Directive options for customization.
    :param content: The directive content for customization.
    """
    app = inliner.document.settings.env.app
    #app.info('changeset %r' % text)
    node = make_link_node(rawtext, app, 'changeset', text, options)
    return [node], []

def bbuser_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """Link to a BitBucket user.

    Returns 2 part tuple containing list of nodes to insert into the
    document and a list of system messages.  Both are allowed to be
    empty.

    :param name: The role name used in the document.
    :param rawtext: The entire markup snippet, with role.
    :param text: The text marked with the role.
    :param lineno: The line number where rawtext appears in the input.
    :param inliner: The inliner instance that called us.
    :param options: Directive options for customization.
    :param content: The directive content for customization.
    """
    app = inliner.document.settings.env.app
    #app.info('user link %r' % text)
    ref = 'https://bitbucket.org/' + text
    node = nodes.reference(rawtext, text, refuri=ref, **options)
    return [node], []


def setup(app):
    """Install the plugin.
    
    :param app: Sphinx application context.
    """
    app.info('Initializing BitBucket plugin')
    app.add_role('bbissue', bbissue_role)
    app.add_role('bbchangeset', bbchangeset_role)
    app.add_role('bbuser', bbuser_role)
    app.add_config_value('bitbucket_project_url', None, 'env')
    return

