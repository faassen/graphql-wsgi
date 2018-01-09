import pytest
import json
from webtest import TestApp as Client
from graphql_wsgi import graphql_wsgi, graphql_wsgi_dynamic

from graphql.type import (
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
    return 'Hello ' + args.get('who', 'World')


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
    wsgi = graphql_wsgi(TestSchema)

    c = Client(wsgi)
    response = c.get('/', {'query': '{test}'})

    assert response.json == {
        'data': {
            'test': 'Hello World'
        }
    }


def test_GET_functionality_allows_GET_with_variable_values():
    wsgi = graphql_wsgi(TestSchema)

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
    wsgi = graphql_wsgi(TestSchema)

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
    wsgi = graphql_wsgi(TestSchema)

    c = Client(wsgi)

    response = c.post_json('/', {'query': '{test}'})

    assert response.json == {
        'data': {
            'test': 'Hello World'
        }
    }


def test_POST_functionality_allows_POST_with_url_encoding():
    wsgi = graphql_wsgi(TestSchema)

    c = Client(wsgi)

    response = c.post('/', {'query': b'{test}'})

    assert response.json == {
        'data': {
            'test': 'Hello World'
        }
    }


def test_POST_functionality_supports_POST_JSON_query_with_string_variables():
    wsgi = graphql_wsgi(TestSchema)

    c = Client(wsgi)

    response = c.post('/', {
        'query': b'query helloWho($who: String){ test(who: $who) }',
        'variables': json.dumps({'who': 'Dolly'})
    })

    assert response.json == {
        'data': {
            'test': 'Hello Dolly'
        }
    }


def test_POST_functionality_supports_POST_JSON_query_with_JSON_variables():
    wsgi = graphql_wsgi(TestSchema)

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
    wsgi = graphql_wsgi(TestSchema)

    c = Client(wsgi)

    response = c.post('/', {
        'query': b'query helloWho($who: String){ test(who: $who) }',
        'variables': json.dumps({'who': 'Dolly'})
    })

    assert response.json == {
        'data': {
            'test': 'Hello Dolly'
        }
    }


def test_POST_functionality_POST_JSON_query_GET_variable_values():
    wsgi = graphql_wsgi(TestSchema)

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
    wsgi = graphql_wsgi(TestSchema)

    c = Client(wsgi)

    response = c.post("/?variables=%s" % json.dumps({'who': 'Dolly'}), {
        'query': b'query helloWho($who: String){ test(who: $who) }'
    })

    assert response.json == {
        'data': {
            'test': 'Hello Dolly'
        }
    }


def test_POST_functionaly_POST_raw_text_query_with_GET_variable_values():
    wsgi = graphql_wsgi(TestSchema)

    c = Client(wsgi)

    response = c.post("/?variables=%s" % json.dumps({'who': 'Dolly'}),
                      b'query helloWho($who: String){ test(who: $who) }',
                      content_type='application/graphql')

    assert response.json == {
        'data': {
            'test': 'Hello Dolly'
        }
    }


def test_POST_functionality_allows_POST_with_operation_name():
    wsgi = graphql_wsgi(TestSchema)

    c = Client(wsgi)

    response = c.post('/', {
        'query': b'''
              query helloYou { test(who: "You"), ...shared }
              query helloWorld { test(who: "World"), ...shared }
              query helloDolly { test(who: "Dolly"), ...shared }
              fragment shared on Root {
                shared: test(who: "Everyone")
              }
            ''',
        'operationName': b'helloWorld'
    })

    assert response.json == {
        'data': {
            'test': 'Hello World',
            'shared': 'Hello Everyone'
        }
    }


def test_POST_functionality_allows_POST_with_GET_operation_name():
    wsgi = graphql_wsgi(TestSchema)

    c = Client(wsgi)

    response = c.post('/?operationName=helloWorld', {
        'query': b'''
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
    wsgi = graphql_wsgi(TestSchema)

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
    wsgi = graphql_wsgi(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.get('/', {'query': '{test}'})
    assert response.body == b'''\
{
  "data": {
    "test": "Hello World"
  }
}'''


def test_pretty_printing_configured_by_request():
    def options_from_request(request):
        return TestSchema, None, request.GET.get('pretty') == '1'

    wsgi = graphql_wsgi_dynamic(options_from_request)

    c = Client(wsgi)

    response = c.get('/', {
        'query': '{test}',
        'pretty': '0'
    })

    assert response.body == b'{"data":{"test":"Hello World"}}'

    response = c.get('/', {
        'query': '{test}',
        'pretty': '1'
    })

    assert response.body == b'''\
{
  "data": {
    "test": "Hello World"
  }
}'''


def test_error_handling_functionality_handles_field_errors_caught_by_graphql():
    wsgi = graphql_wsgi(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.get('/', {'query': b'{thrower}'})

    assert response.json == {
        'data': None,
        'errors': [{
            'message': 'Throws!',
            'locations': [{'line': 1, 'column': 2}]
        }]
    }


def test_error_handling_handles_syntax_errors_caught_by_graphql():
    wsgi = graphql_wsgi(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.get('/', {'query': 'syntaxerror'}, status=400)

    assert response.json == {
        'data': None,
        'errors': [{
            'message': ('Syntax Error GraphQL request (1:1) '
                        'Unexpected Name "syntaxerror"\n\n1: syntaxerror\n'
                        '   ^\n'),
            'locations': [{'line': 1, 'column': 1}]
        }]
    }


def test_error_handling_handles_errors_caused_by_a_lack_of_query():
    wsgi = graphql_wsgi(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.get('/', status=400)

    assert response.json == {
        'errors': [{'message': 'Must provide query string.'}]
    }


def test_error_handling_handles_invalid_JSON_bodies():
    wsgi = graphql_wsgi(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.post('/',
                      b'{"query":',
                      content_type='application/json',
                      status=400)

    assert response.json == {
        'errors': [{'message': 'POST body sent invalid JSON.'}]
    }


# actually text/plain post is not handled as a real query string
# so this error results.
def test_error_handling_handles_plain_POST_text():
    wsgi = graphql_wsgi(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.post('/?variables=%s' % json.dumps({'who': 'Dolly'}),
                      b'query helloWho($who: String){ test(who: $who) }',
                      content_type='text/plain',
                      status=400)
    assert response.json == {
        'errors': [{'message': 'Must provide query string.'}]
    }


# need to do the test with foobar instead of ascii as in the original
# test as ascii *is* a recognized encoding.
def test_error_handling_handles_unsupported_charset():
    wsgi = graphql_wsgi(TestSchema, pretty=True)

    c = Client(wsgi)

    response = c.post('/',
                      b'{ test(who: "World") }',
                      content_type='application/graphql; charset=foobar',
                      status=415)
    assert response.json == {
        'errors': [{'message': 'Unsupported charset "FOOBAR".'}]
    }


def test_error_handling_handles_unsupported_utf_charset():
    wsgi = graphql_wsgi(TestSchema, pretty=True)

    c = Client(wsgi)

    response = c.post('/',
                      b'{ test(who: "World") }',
                      content_type='application/graphql; charset=utf-53',
                      status=415)
    assert response.json == {
        'errors': [{'message': 'Unsupported charset "UTF-53".'}]
    }


# I have no idea how to handle Content-Encoding with WSGI
@pytest.mark.xfail
def test_error_handling_handles_unknown_encoding():
    wsgi = graphql_wsgi(TestSchema, pretty=True)

    c = Client(wsgi)

    response = c.post('/',
                      b'!@#$%^*(&^$%#@',
                      headers={'Content-Encoding': 'garbage'},
                      status=415)
    assert response.json == {
        'errors': [{'message': 'Unsupported content encoding "garbage".'}]
    }


def test_error_handling_handles_poorly_formed_variables():
    wsgi = graphql_wsgi(TestSchema, pretty=True)

    c = Client(wsgi)

    response = c.get('/', {
        'variables': b'who:You',
        'query': b'query helloWho($who: String){ test(who: $who) }'
    }, status=400)

    assert response.json == {
        'errors': [{'message': 'Variables are invalid JSON.'}]
    }


def test_error_handling_handles_unsupported_http_methods():
    wsgi = graphql_wsgi(TestSchema, pretty=True)

    c = Client(wsgi)
    response = c.put('/?query={test}', status=405)

    assert response.json == {
        'errors': [{'message': 'GraphQL only supports GET and POST requests.'}]
    }


def test_error_handling_unknown_field():
    wsgi = graphql_wsgi(TestSchema, pretty=True)

    c = Client(wsgi)
    # I think this should actually be a 200 status
    response = c.get('/?query={unknown}', status=400)
    # locations formatting appears to be different here...
    assert response.json == {
        'data': None,
        'errors': [
            {
                "locations": [
                    {'line': 1,
                     'column': 2}
                ],
                "message": u'Cannot query field "unknown" on type "Root".'
            }
        ]
    }


# this didn't appear to be covered in the test suite of express-graphql
def test_POST_functionality_variables_in_json_POST_body_not_encoded():
    wsgi = graphql_wsgi(TestSchema)

    c = Client(wsgi)

    response = c.post_json('/', {
        'query': 'query helloWho($who: String){ test(who: $who) }',
        'variables': {'who': 'Dolly'}
    })

    assert response.json == {
        'data': {
            'test': 'Hello Dolly'
        }
    }
