import json

import six
from webob.dec import wsgify
from webob.response import Response


from graphql import graphql
from graphql.error import GraphQLError, format_error as format_graphql_error


def graphql_wsgi_dynamic(get_options):
    @wsgify
    def handle(request):
        schema, root_value, pretty, middleware = get_options(request)

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

        context_value = request
        result = graphql(schema, query, root_value,
                context_value,
                variables,
                operation_name,
                middleware=middleware)

        if result.invalid:
            status = 400
        else:
            status = 200

        d = {'data': result.data}
        if result.errors:
            d['errors'] = [format_error(error) for error in result.errors]

        return Response(status=status,
                        content_type='application/json',
                        body=json_dump(d, pretty).encode('utf8'))
    return handle


def format_error(error):
    if isinstance(error, GraphQLError):
        return format_graphql_error(error)

    return {'message': '{}: {}'.format(
        error.__class__.__name__, six.text_type(error))}


def graphql_wsgi(schema, root_value=None, pretty=None, middleware=None):
    def get_options(request):
        return schema, root_value, pretty, middleware

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
    elif request.content_type == 'multipart/form-data':  # support for apollo-upload-client
        return json.loads(request.POST['operations'])

    return {}


def get_graphql_params(request, data):
    query = request.GET.get('query') or data.get('query')

    if query is None:
        raise Error('Must provide query string.')

    variables = request.GET.get('variables') or data.get('variables')

    if variables is not None and isinstance(variables, six.text_type):
        try:
            variables = json.loads(variables)
        except ValueError:
            raise Error('Variables are invalid JSON.')

    operation_name = (request.GET.get('operationName') or
                      data.get('operationName'))

    for key, value in request.POST.items():  # support for apollo-upload-client
        if key.startswith('variables.'):
            variables[key[10:]] = key

    return query, variables, operation_name


def error_response(e, pretty):
    d = {
        'errors': [{'message': six.text_type(e)}]
    }
    response = Response(status=e.status,
                        content_type='application/json',
                        body=json_dump(d, pretty).encode('utf8'))
    if e.headers:
        response.headers.update(e.headers)
    return response


class Error(Exception):
    def __init__(self, message, status=400, headers=None):
        super(Error, self).__init__(message)
        self.status = status
        self.headers = headers
