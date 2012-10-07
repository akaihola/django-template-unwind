============================================================
 django-template-unwind – debug complex template structures
============================================================

This app injects information about template blocks into rendered templates.
It is most useful for debugging the template structure
of a complex Django project.

This should never be used in production,
and will also break correct rendering of pages in development.
Only use the tool for enhancing the page markup
while examining the HTML source code.

In rendered template, all invocations of
``{% block %}``, ``{% endblock %}`` and ``{{ block.super }}``
are annotated with the name of the block and the current template.

The template name also includes the template inheritance path
through the hierarchy created with ``{% extends %}``.

Quickstart
==========

Install the django-template-unwind Python package::

    pip install -e git+git://github.com/akaihola/django-template-unwind.git#egg=template_unwind

Add django-template-unwind to ``INSTALLED_APPS`` in your project settings::

    INSTALLED_APPS = (
        # ...
        # 'template_unwind',
        # ...
    )

Open a page while adding one of the following GET parameters to the url::

    http://localhost:8000/page-url/?unwind-template-as=comments
    http://localhost:8000/page-url/?unwind-template-as=elements

When using the ``comments`` format,
you'll see HTML comments in the source code of the rendered page::

    <!-- {% block myblock [mypage.html] %} -->
    <!-- {% endblock myblock [mypage.html] %} -->
    <!-- {{ block.super myblock [mypage.html] }} -->
    <!-- {% /block.super myblock [mypage.html] %} -->

For the ``elements`` format, custom HTML tags are used instead.
This works well with browsers' developer tools
which show the DOM in a properly indented and foldable view::

    <django:block name="myblock" template="mypage.html">
    </django:block>
    <django:block-super name="myblock" template="mypage.html">
    </django:block-super>

In both formats, a special syntax is used
for one-line blocks which don't contain HTML tags::

    <body class="{% block myblock [mypage.html] %}myclass{% endblock %}">

This avoids breaking the rendering too much.
