# GraphQL

[GraphQL](https://graphql.org/) gives clients the power to ask for exactly what they need and nothing more.

Entities in GraphQL are not identified by URLs. Instead, a GraphQL server operates on a single endpoint and all requests should be directed at this endpoint.

##### Query

A standard GraphQL POST request should use the `application/json` content type and include a JSON-encoded body.

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

And if we send same request with header `Authorization: Bearer <token>`

```
{
  "data": {
    "user": {
      "username": "John.Doe@monash.edu"
    }
  }
}
```