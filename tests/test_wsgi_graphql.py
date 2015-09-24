import pytest
import json
from webtest import TestApp as Client
from wsgi_graphql import wsgi_graphql, wsgi_graphql_dynamic

from graphql.core.type import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLArgument,
    GraphQLNonNull,
    GraphQLSchema,
    GraphQLString,
)


def raises(*_):
    raise Exception("Throws!")


def resolver(root, args, *_):
    return 'Hello ' + (args['who'] or 'World')


TestSchema = GraphQLSchema(
    query=GraphQLObjectType(
        'Root',
        fields=lambda: {
            'test': GraphQLField(
                GraphQLString,
                args={
                    'who': GraphQLArgument(
                        type=GraphQLString
                    )
                },
                resolver=resolver
            ),
            'thrower': GraphQLField(
                GraphQLNonNull(GraphQLString),
                resolver=raises
            )
        }
    )
)


def test_GET_functionality_allows_GET_with_query_param():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)
    response = c.get('/', {'query': '{test}'})
    assert response.json == {
        'data': {
            'test': 'Hello World'
        }
    }


def test_GET_functionality_allows_GET_with_variable_values():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)
    response = c.get('/', {
        'query': 'query helloWho($who: String){ test(who: $who) }',
        'variables': json.dumps({'who': 'Dolly'})
    })

    assert response.json == {
        'data': {
            'test': 'Hello Dolly'
        }
    }


def test_GET_functionality_allows_GET_with_operation_name():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)
    response = c.get('/', {
        'query': '''
          query helloYou { test(who: "You"), ...shared }
          query helloWorld { test(who: "World"), ...shared }
          query helloDolly { test(who: "Dolly"), ...shared }
          fragment shared on Root {
            shared: test(who: "Everyone")
          }''',
        'operationName': 'helloWorld'
    })

    assert response.json == {
        'data': {
            'test': 'Hello World',
            'shared': 'Hello Everyone'
        }
    }


def test_POST_functionality_allows_POST_with_JSON_encoding():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)

    response = c.post_json('/', {'query': '{test}'})

    assert response.json == {
        'data': {
            'test': 'Hello World'
        }
    }


def test_POST_functionality_allows_POST_with_url_encoding():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)

    response = c.post('/', {'query': '{test}'})

    assert response.json == {
        'data': {
            'test': 'Hello World'
        }
    }


def test_POST_functionality_supports_POST_JSON_query_with_string_variables():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)

    response = c.post('/', {
        'query': 'query helloWho($who: String){ test(who: $who) }',
        'variables': json.dumps({'who': 'Dolly'})
    })

    assert response.json == {
        'data': {
            'test': 'Hello Dolly'
        }
    }


def test_POST_functionality_supports_POST_JSON_query_with_JSON_variables():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)

    response = c.post_json('/', {
        'query': 'query helloWho($who: String){ test(who: $who) }',
        'variables': json.dumps({'who': 'Dolly'})
    })

    assert response.json == {
        'data': {
            'test': 'Hello Dolly'
        }
    }


def test_POST_functionality_POST_url_encoded_query_with_string_variables():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)

    response = c.post('/', {
        'query': 'query helloWho($who: String){ test(who: $who) }',
        'variables': json.dumps({'who': 'Dolly'})
    })

    assert response.json == {
        'data': {
            'test': 'Hello Dolly'
        }
    }


def test_POST_functionality_POST_JSON_query_GET_variable_values():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)

    response = c.post_json("/?variables=%s" % json.dumps({'who': 'Dolly'}), {
        'query': 'query helloWho($who: String){ test(who: $who) }'
    })

    assert response.json == {
        'data': {
            'test': 'Hello Dolly'
        }
    }


def test_POST_functionality_url_encoded_query_with_GET_variable_values():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)

    response = c.post("/?variables=%s" % json.dumps({'who': 'Dolly'}), {
        'query': 'query helloWho($who: String){ test(who: $who) }'
    })

    assert response.json == {
        'data': {
            'test': 'Hello Dolly'
        }
    }


def test_POST_functionaly_POST_raw_text_query_with_GET_variable_values():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)

    response = c.post("/?variables=%s" % json.dumps({'who': 'Dolly'}),
                      'query helloWho($who: String){ test(who: $who) }',
                      content_type='application/graphql')

    assert response.json == {
        'data': {
            'test': 'Hello Dolly'
        }
    }


def test_POST_functionality_allows_POST_with_operation_name():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)

    response = c.post('/', {
        'query': '''
              query helloYou { test(who: "You"), ...shared }
              query helloWorld { test(who: "World"), ...shared }
              query helloDolly { test(who: "Dolly"), ...shared }
              fragment shared on Root {
                shared: test(who: "Everyone")
              }
            ''',
        'operationName': 'helloWorld'
    })

    assert response.json == {
        'data': {
            'test': 'Hello World',
            'shared': 'Hello Everyone'
        }
    }


def test_POST_functionality_allows_POST_with_GET_operation_name():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)

    response = c.post('/?operationName=helloWorld', {
        'query': '''
              query helloYou { test(who: "You"), ...shared }
              query helloWorld { test(who: "World"), ...shared }
              query helloDolly { test(who: "Dolly"), ...shared }
              fragment shared on Root {
                shared: test(who: "Everyone")
              }
            '''
    })

    assert response.json == {
        'data': {
            'test': 'Hello World',
            'shared': 'Hello Everyone'
        }
    }


def test_POST_functionality_allows_other_UTF_charsets():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)

    response = c.post('/',
                      u'{ test(who: "World") }'.encode('utf_16_le'),
                      content_type='application/graphql; charset=utf-16')

    assert response.json == {
        'data': {
            'test': 'Hello World'
        }
    }


# Don't test  "allows gzipped POST bodies" and "allows deflated POST bodies"
# as this seems to be outside of
# the domain of WSGI and up to the web server itself.

# "allows for pre-parsed POST bodies" requires some kind of convention
# for pre-parsing that doesn't exist to my knowledge in WSGI or WebOb,
# though with WebOb it can be done with a Request subclass.

def test_pretty_printing_supports_pretty_printing():
    wsgi = wsgi_graphql(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.get('/', {'query': '{test}'})
    assert response.body == '''\
{
  "data": {
    "test": "Hello World"
  }
}'''


def test_pretty_printing_configured_by_request():
    def options_from_request(request):
        return TestSchema, None, request.GET.get('pretty') == '1'

    wsgi = wsgi_graphql_dynamic(options_from_request)

    c = Client(wsgi)

    response = c.get('/', {
        'query': '{test}',
        'pretty': '0'
    })

    assert response.body == '{"data":{"test":"Hello World"}}'

    response = c.get('/', {
        'query': '{test}',
        'pretty': '1'
    })

    assert response.body == '''\
{
  "data": {
    "test": "Hello World"
  }
}'''


# FIXME:
# see https://github.com/dittos/graphqllib/issues/52
@pytest.mark.xfail
def test_error_handling_functionality_handles_field_errors_caught_by_graphql():
    wsgi = wsgi_graphql(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.get('/', {'query': '{thrower}'})

    assert response.status == 200
    assert response.json == {
        'data': None,
        'errors': [{
            'message': 'Throws!',
            'locations': [{'line': 1, 'column': 2}]
        }]
    }


# FIXME:
# see https://github.com/dittos/graphqllib/issues/53
@pytest.mark.xfail
def test_error_handling_handles_syntax_errors_caught_by_graphql():
    wsgi = wsgi_graphql(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.get('/', {'query': 'syntaxerror'}, status=400)

    assert response.json == {
        'data': None,
        'errors': [{
            'message': ('Syntax Error GraphQL request (1:1) '
                        'Unexpected Name "syntaxerror"\n\n1: syntaxerror\n'
                        '  ^\n'),
            'locations': [{'line': 1, 'column': 1}]
        }]
    }


def test_error_handling_handles_errors_caused_by_a_lack_of_query():
    wsgi = wsgi_graphql(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.get('/', status=400)

    assert response.json == {
        'errors': [{'message': 'Must provide query string.'}]
    }


def test_error_handling_handles_invalid_JSON_bodies():
    wsgi = wsgi_graphql(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.post('/',
                      '{"query":',
                      content_type='application/json',
                      status=400)

    assert response.json == {
        'errors': [{'message': 'POST body sent invalid JSON.'}]
    }


# actually text/plain post is not handled as a real query string
# so this error results.
def test_error_handling_handles_plain_POST_text():
    wsgi = wsgi_graphql(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.post('/?variables=%s' % json.dumps({'who': 'Dolly'}),
                      'query helloWho($who: String){ test(who: $who) }',
                      content_type='text/plain',
                      status=400)
    assert response.json == {
        'errors': [{'message': 'Must provide query string.'}]
    }


# need to do the test with foobar instead of ascii as in the original
# test as ascii *is* a recognized encoding.
def test_error_handling_handles_unsupported_charset():
    wsgi = wsgi_graphql(TestSchema, pretty=True)

    c = Client(wsgi)

    response = c.post('/',
                      '{ test(who: "World") }',
                      content_type='application/graphql; charset=foobar',
                      status=415)
    assert response.json == {
        'errors': [{'message': 'Unsupported charset "FOOBAR".'}]
    }
