from webtest import TestApp as Client
from wsgi_graphql import wsgi_graphql

from graphql.core.type import (
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLField,
    GraphQLArgument,
    GraphQLList,
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


def test_basic():
    wsgi = wsgi_graphql(TestSchema)

    c = Client(wsgi)
    response = c.get('/?query={test}')
    assert response.json == {
        'data': {
            'test': 'Hello World'
        }
    }
