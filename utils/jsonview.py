from __future__ import absolute_import, unicode_literals

import logging
import traceback
from functools import wraps
from importlib import import_module

from django import http
from django.conf import settings
from django.core.handlers.base import BaseHandler
from django.core.serializers.json import DjangoJSONEncoder
from django.core.signals import got_request_exception
from django.utils.module_loading import import_string

json = import_module(getattr(settings, 'JSON_MODULE', 'json'))
JSON = getattr(settings, 'JSON_DEFAULT_CONTENT_TYPE', 'application/json')
logger = logging.getLogger('django.request')


class BadRequest(Exception):
    pass


def _dump_json(data):
    options = {}
    options.update(getattr(settings, 'JSON_OPTIONS', {}))

    options.setdefault('cls', DjangoJSONEncoder)
    if isinstance(options['cls'], str):
        options['cls'] = import_string(options['cls'])
    elif options['cls'] is None:
        options.pop('cls')

    return json.dumps(data, **options)


def json_view(*args, **kwargs):
    content_type = kwargs.get('content_type', JSON)

    def decorator(f):
        @wraps(f)
        def _wrapped(request, *a, **kw):
            try:
                status = 200
                headers = {}
                ret = f(request, *a, **kw)

                if isinstance(ret, tuple):
                    if len(ret) == 3:
                        ret, status, headers = ret
                    else:
                        ret, status = ret

                if isinstance(ret, http.HttpResponseNotAllowed):
                    blob = _dump_json({
                        'error': 405,
                        'message': 'HTTP method not allowed.'
                    })
                    return http.HttpResponse(
                        blob, status=405, content_type=JSON)

                if isinstance(ret, http.HttpResponse):
                    return ret

                blob = _dump_json(ret)
                response = http.HttpResponse(blob, status=status,
                                             content_type=content_type)
                for k in headers:
                    response[k] = headers[k]
                return response

            except http.Http404 as e:
                blob = _dump_json({
                    'error': 404,
                    'message': str(e),
                })
                logger.warning('Not found: %s', request.path,
                               extra={
                                   'status_code': 404,
                                   'request': request,
                               })
                return http.HttpResponseNotFound(blob, content_type=JSON)

            except BadRequest as e:
                blob = _dump_json({
                    'error': 400,
                    'message': str(e),
                })
                return http.HttpResponseBadRequest(blob, content_type=JSON)

            except Exception as e:
                exc_data = {
                    'error': 500,
                    'message': 'An error occurred',
                }
                if settings.DEBUG:
                    exc_data['message'] = str(e)
                    exc_data['traceback'] = traceback_prettify(
                        traceback.format_exc())[8:]

                blob = _dump_json(exc_data)

                logger.error(
                    'Internal Server Error: %s', request.path,
                    exc_info=True,
                    extra={
                        'status_code': 500,
                        'request': request
                    }
                )

                got_request_exception.send(
                    sender=BaseHandler,
                    request=request,
                    exception=e,
                    exc_data=exc_data
                )
                return http.HttpResponseServerError(blob, content_type=JSON)

        return _wrapped

    if len(args) == 1 and callable(args[0]):
        return decorator(args[0])
    else:
        return decorator


def traceback_prettify(tb):
    without_quote = tb.replace('"', "")
    without_space = without_quote.replace("    ", "").replace("  ", "")
    lines = without_space.split('\nFile')
    tb_res = []
    for line in lines:
        if len(line.split('\n')) == 2:
            tb_res.append(line.split('\n'))
    return tb_res
