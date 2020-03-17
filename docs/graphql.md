# GraphQL

[GraphQL](https://graphql.org/) gives clients the power to ask for exactly what they need and nothing more.

Entities in GraphQL are not identified by URLs. Instead, a GraphQL server operates on a single endpoint and all requests should be directed at this endpoint.

##### Query

A standard GraphQL POST request should use the `application/json` content type and include a JSON-encoded body.

```
{
  "query": "...",
  "operationName": "...",
  "variables": { "myVariable": "someValue", ... }
}
```

Parameters `operationName` and `variables` are optional.

If the `application/graphql` Content-Type header is present, POST body contents will be GraphQL query string.

```
query {
  users {
    firstname
    lastname
  }
}
```

##### Response

The response should be returned in the body in JSON format and might result in some `data` and some `errors`.

```
{
  "errors": [
    {
      "message": "Can't find users table."
    }
  ],
  "data": {
    "users": null
  }
}
```

If there were no errors returned, the `errors` field should not be present on the response.

```
{
  "data": {
    "users": [
      {
        "firstname": "John",
        "lastname": "Doe"
      },
      {
        "firstname": "Alicia",
        "lastname": "Smith"
      }
    ]
  }
}
```

## Endpoint

Endpoint in browser (using GraphiQL library to be disabled in production using GRAPHIQL variable in settings, default is True)

[https://test-store.erc.monash.edu/graphql/](https://test-store.erc.monash.edu/graphql/)

Browser will use your session for authentication, so it will be easy to quickly try API without complications with request headers. It also provides you with documentation on available operations (queries and mutations) and neat autocomplete function.

To simulate real API call with headers you can use [Postman](https://www.postman.com/) software.

## Authentication

All non-auth requests to GraphQL will be protected with [JSON Web Tokens](https://jwt.io/) (JWT) token, valid by default for 3 days . You are able to refresh token at any time within 7 days since first invocation. Values are configurable via settings.

We can use username and password combination to obtain JWT token to sign future requests:

```
mutation {
  userSignIn(input: {
    username: "John.Doe@monash.edu",
    password: "PeekABoo"
  }) {
    token
    user {
      firstName
      lastName
      email
    }
  }
}
```

and response:

```
{
  "data": {
    "userSignIn": {
      "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IkRtaX...",
      "user": {
        "firstName": "John",
        "lastName": "Doe",
        "email": "John.Doe@monash.edu"
      }
    }
  }
}
```

### User

Let's see *who am I* using `User` query without authentication:

```
{
  user {
    username
  }
}
```

will return

```
{
  "data": {
    "user": null
  }
}
```

And if we send same request with header `Authorization: JWT <token>`

```
{
  "data": {
    "user": {
      "username": "John.Doe@monash.edu"
    }
  }
}
```

## Join data in one query

Get all instruments, including facility data.

```
{
  instruments {
    edges {
      node {
        id
        pk
        name
        facility {
          id
          pk
          name
        }
      }
    }
  }
}
```

## Filtering

```
{
  facilities(name_Contains:"AR") {
    edges {
      node {
        id
        pk
        name
      }
    }
  }
}
```

## Sorting

```
{
  facilities(orderBy:"-name") {
    edges {
      node {
        name
      }
    }
  }
}
```

## Pagination

Following example will fetch first 20 records, asking for total number of records and `endCursor` anchor for subsequent call.

```
{
  instruments(first:20) {
    totalCount
    pageInfo {
      endCursor
    }
    edges {
      node {
        name
      }
    }
  }
}
```

Next page (use `endCursor` from prior request as `after` parameter):

```
{
  instruments(first:20, after:"YXJyYXljb25uZWN0aW9uOjE5") {
    pageInfo {
      endCursor
    }
    edges {
      node {
        name
      }
    }
  }
}
```

## Create record

Input element `facility` has ID reference to a corresponding facility.

```
mutation {
  createInstrument(input: {
    name: "Test ABC",
    facility: "RmFjaWxpdHlUeXBlOjEyMQ=="
  }) {
    instrument {
      id
    }
  }
}
```

## Update record

```
mutation {
  updateInstrument(input: {
    id: "SW5zdHJ1bWVudFR5cGU6Mzk0",
    name: "Test!"
  }) {
    instrument {
      name
    }
  }
}
```

# Backend

### Requirements

```
graphene-django
graphene-django-plus
django-filter
django-crispy-forms
django-graphql-jwt
django-graphiql
django-cors-headers
```

### Config

```
authentication_backends:
  - graphql_jwt.backends.JSONWebTokenBackend
```

### Settings

`tardis.default_settings.graphql`

### Schema

`tardis.schema` -> `tardis.tardis_portal.graphql.schema`

### Model

```
import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from django.contrib.auth.models import Group as GroupModel

from .utils import ExtendedConnection


class GroupType(ModelType):
    class Meta:
        model = GroupModel
        permissions = ['auth.view_group']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class GroupTypeFilter(FilterSet):
    class Meta:
        model = GroupModel
        fields = {
            'name': ['exact', 'contains']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('name', 'name')
        )
    )


class CreateGroup(ModelCreateMutation):
    class Meta:
        model = GroupModel
        permissions = ['auth.add_group']


class UpdateGroup(ModelUpdateMutation):
    class Meta:
        model = GroupModel
        permissions = ['auth.change_group']
```

Model integration in to schema:

```
from .group import (
    GroupType, GroupTypeFilter,
    CreateGroup, UpdateGroup
)


class tardisQuery(graphene.ObjectType):

    groups = DjangoFilterConnectionField(
        GroupType,
        filterset_class=GroupTypeFilter
    )

    def resolve_groups(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            if user.is_superuser:
                return GroupModel.objects.all()
            return GroupModel.objects.filter(user=user)
        return None


class tardisMutation(graphene.ObjectType):

    create_group = CreateGroup.Field()
    update_group = UpdateGroup.Field()
```
