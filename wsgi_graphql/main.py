import json

from webob.dec import wsgify
from webob.response import Response
from webob.exc import HTTPException, HTTPBadRequest, HTTPMethodNotAllowed

from graphql.core import graphql
from graphql.core.error import format_error


def wsgi_graphql_dynamic(get_options):
    @wsgify
    def handle(request):
        schema, root_value, pretty = get_options(request)

        if request.method != 'GET' and request.method != 'POST':
            raise HTTPMethodNotAllowed(headers={'Allow': 'GET, POST'})

        try:
            data = parse_body(request)
        except Error, e:
            return error_response(e, pretty)

        try:
            query, variables, operation_name = get_graphql_params(
                request, data)
        except Error, e:
            return error_response(e, pretty)
        result = graphql(schema, query, root_value, variables, operation_name)

        if result.data is not None:
            status = 200
        else:
            status = 400

        d = {'data': result.data}
        if result.errors is not None:
            d['errors'] = result.errors

        return Response(status=status,
                        content_type='application/json',
                        body=json_dump(d, pretty))
    return handle


def wsgi_graphql(schema, root_value=None, pretty=None):
    def get_options(request):
        return schema, root_value, pretty

    return wsgi_graphql_dynamic(get_options)


def json_dump(d, pretty):
    if not pretty:
        return json.dumps(d, separators=(',', ':'))
    return json.dumps(d, sort_keys=True,
                      indent=2, separators=(',', ': '))


def parse_body(request):
    if request.content_type is None:
        return {}

    if request.content_type == 'application/graphql':
        return {'query': request.text}
    elif request.content_type == 'application/json':
        try:
            return request.json
        except ValueError:
            raise Error('POST body sent invalid JSON.')
    elif request.content_type == 'application/x-www-form-urlencoded':
        return request.POST

    return {}


def get_graphql_params(request, data):
    query = request.GET.get('query') or data.get('query')

    if query is None:
        raise Error('Must provide query string.')

    variables = request.GET.get('variables') or data.get('variables')

    if variables is not None:
        try:
            variables = json.loads(variables)
        except ValueError:
            raise Error('Variables are invalid JSON.')

    operation_name = (request.GET.get('operationName') or
                      data.get('operationName'))

    return query, variables, operation_name


def error_response(e, pretty):
    d = {
        'errors': [{'message': e.message}]
    }
    return Response(status=400,
                    content_type='application/json',
                    body=json_dump(d, pretty))


class Error(Exception):
    pass
