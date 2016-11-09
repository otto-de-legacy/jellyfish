from flask import render_template, request

from app.config import app_name
from app.config import navigation_bar


def ceil(value):
    return 99.99 if value > 99.99 else value


def render(html, title, **kwargs):
    return render_template(html,
                           parameter=request.args,
                           url_query=get_url_query(),
                           navigation_bar=navigation_bar,
                           title=title,
                           app_name=app_name,
                           **kwargs)


def get_url_query():
    if request.query_string:
        return '?' + str(request.query_string.decode())
    else:
        return ''


def request_wants_json():
    for mime in request.accept_mimetypes:
        if 'json' in mime[0]:
            return mime[0]
    return False
