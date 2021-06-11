from datetime import timedelta

GRAPHQL = False

# GraphiQL is very useful during development,
# but it's standard practice to disable that view in production
# as it may allow an external developer too much insight into the API.
GRAPHIQL = False

# It means that you need to refresh every 5 mins and
# even you keep on refreshing token every 5 mins,
# you will still be logout in 7 days after
# the first token has been issued.
GRAPHQL_JWT = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': timedelta(days=3),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
}

GRAPHENE = {
    'SCHEMA': 'tardis.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}
