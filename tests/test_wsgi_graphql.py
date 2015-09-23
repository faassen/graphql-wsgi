import json
from webtest import TestApp as Client
from wsgi_graphql import wsgi_graphql

from graphql.core.type import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLArgument,
    GraphQLNonNull,
    GraphQLSchema,
    GraphQLString,
)


def raises(*_):
    raise Exception("Raises!")


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
                resolver=lambda root, args, *_: 'Hello ' + (args['who'] or 'World')
            ),
            'thrower': GraphQLField(
                GraphQLNonNull(GraphQLString),
                resolver=raises
            )
        }
    )
)


def test_allows_GET_with_query_param():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)
    response = c.get('/', {'query': '{test}'})
    assert response.json == {
        'data': {
            'test': 'Hello World'
        }
    }


def test_allows_GET_with_variable_values():
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
