"""Replacement ``{% block %}`` tag for rendering debug information

Additions to Django's stock ``{% block %}`` tag are marked with the "unwind
addition" comment.

"""


from django.template.base import Library
from django.template.loader_tags import BLOCK_CONTEXT_KEY, BlockNode, do_block
from django.utils.safestring import mark_safe

register = Library()


UNWIND_FORMATS = {
    None: {
        'block': u'{result}',
        'super': u'{result}'},
    'comments': {
        'block': (u'<!-- {{% block {name} [{tmplsrc}] %}} -->\n'
                  u'{result}\n'
                  u'<!-- {{% endblock {name} [{tmplsrc}] %}} -->\n'),
        'block-in-element': (u'{{% block {name} [{tmplsrc}] %}}'
                             u'{result}'
                             u'{{% endblock %}}'),
        'super': (u'<!-- {{{{ block.super {name} [{tmplsrc}] }}}} -->\n'
                  u'{result}\n'
                  u'<!-- {{{{ /block.super {name} [{tmplsrc}] }}}} -->\n')},
    'elements': {
        'block': (u'<django:block name="{name}" template="{tmplsrc}">\n'
                  u'    {result}\n'
                  u'</django:block>\n'),
        'block-in-element': (u'{{% block {name} [{tmplsrc}] %}}'
                             u'{result}'
                             u'{{% endblock %}}'),
        'super': (u'<django:block-super name="{name}" template="{tmplsrc}">\n'
                  u'    {result}\n'
                  u'</django:block-super>\n')}}


MODE = 'html-comment'


def get_unwind_formats(context):
    """Returns True if template unwinding is enabled"""
    try:
        mode = context['request'].GET.get('unwind-template-as')
    except KeyError:
        mode = None
    return UNWIND_FORMATS[mode]


class UnwindBlockNode(BlockNode):
    def __init__(self, name, nodelist, parent=None, tmplsrc=None):
        self.name, self.nodelist, self.parent = name, nodelist, parent
        self.tmplsrc = tmplsrc  # unwind addition

    def __repr__(self):
        return "<Block Node: %s. Contents: %r>" % (self.name, self.nodelist)

    def render(self, context):
        block_context = context.render_context.get(BLOCK_CONTEXT_KEY)
        context.push()
        if block_context is None:
            context['block'] = self
            result = self.nodelist.render(context)
            tmplsrc = self.tmplsrc  # unwind addition
        else:
            push = block = block_context.pop(self.name)
            if block is None:
                block = self
            # Create new block so we can store context without thread-safety
            # issues.
            block = UnwindBlockNode(block.name, block.nodelist,
                                    tmplsrc=block.tmplsrc  # unwind addition
            )
            block.context = context
            context['block'] = block
            result = block.nodelist.render(context)
            if push is not None:
                block_context.push(self.name, push)
            path = self.get_path(context)  # unwind addition
            tmplsrc = block.tmplsrc  # unwind addition
        context.pop()

        formats = get_unwind_formats(context)
        if u'<' in result or u'\n' in result:
            format_ = 'block'
        else:
            format_ = 'block-in-element'
        return formats[format_].format(name=u'/'.join(path),
                                       result=result,
                                       tmplsrc=tmplsrc)

    def get_path(self, context):
        """Returns the 'block path' (unwind addition)"""
        path = []
        for ctx in context.dicts:
            if 'block' in ctx:
                block_name = ctx['block'].name
                if not path or block_name != path[-1]:
                    path.append(block_name)
        return path

    def super(self):
        """Renders debug information around the {{ block.super }} call

        If template unwind debugging is enabled, HTML comments are rendered
        before and after the actual output from calling the inherited block.

        """
        # pylint: disable=E1101
        #         Instance of <class> has no <member>

        result = super(UnwindBlockNode, self).super()
        if result == '':
            return ''
        formats = get_unwind_formats(self.context)  # unwind addition
        return mark_safe(formats['super'].format(
            name=u'/'.join(self.get_path(self.context)),
            result=result,
            tmplsrc=self.tmplsrc))


@register.tag('block')
def unwind_do_block(parser, token):
    """Replace the {% block %} tag with a debug-enhanced version"""
    original_node = do_block(parser, token)
    return UnwindBlockNode(original_node.name,
                           original_node.nodelist,
                           parent=original_node.parent,
                           tmplsrc=token.source[0].loadname)
