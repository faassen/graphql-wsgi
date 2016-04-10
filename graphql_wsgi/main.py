import json

import six
from webob.dec import wsgify
from webob.response import Response


from graphql.core import graphql
from graphql.core.error import format_error


def graphql_wsgi_dynamic(get_options):
    @wsgify
    def handle(request):
        schema, root_value, pretty = get_options(request)

        if request.method != 'GET' and request.method != 'POST':
            return error_response(
                Error(
                    'GraphQL only supports GET and POST requests.',
                    status=405,
                    headers={'Allow': 'GET, POST'}
                ),
                pretty)

        try:
            data = parse_body(request)
        except Error as e:
            return error_response(e, pretty)

        try:
            query, variables, operation_name = get_graphql_params(
                request, data)
        except Error as e:
            return error_response(e, pretty)
        result = graphql(schema, query, root_value, variables, operation_name)

        if result.invalid:
            status = 400
        else:
            status = 200

        d = {'data': result.data}
        if result.errors:
            d['errors'] = [format_error(error)
                           for error in result.errors]

        return Response(status=status,
                        content_type='application/json',
                        body=json_dump(d, pretty))
    return handle


def graphql_wsgi(schema, root_value=None, pretty=None):
    def get_options(request):
        return schema, root_value, pretty

    return graphql_wsgi_dynamic(get_options)


def json_dump(d, pretty):
    if not pretty:
        return json.dumps(d, separators=(',', ':'))
    return json.dumps(d, sort_keys=True,
                      indent=2, separators=(',', ': '))


def parse_body(request):
    if request.content_type is None:
        return {}

    if request.content_type == 'application/graphql':
        try:
            return {'query': request.text}
        except LookupError:
            raise Error('Unsupported charset "%s".' % request.charset.upper(),
                        status=415)
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

    if variables is not None and isinstance(variables, six.string_types):
        try:
            variables = json.loads(variables)
        except ValueError:
            raise Error('Variables are invalid JSON.')

    operation_name = (request.GET.get('operationName') or
                      data.get('operationName'))

    return query, variables, operation_name


def error_response(e, pretty):
    d = {
        'errors': [{'message': e.args[0]}]
    }
    response = Response(status=e.status,
                        content_type='application/json',
                        body=json_dump(d, pretty))
    if e.headers:
        response.headers.update(e.headers)
    return response


class Error(Exception):
    def __init__(self, message, status=400, headers=None):
        super(Error, self).__init__(message)
        self.status = status
        self.headers = headers
