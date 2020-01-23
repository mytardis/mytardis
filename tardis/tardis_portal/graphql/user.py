import graphene
from graphql import GraphQLError
from graphene_django.types import DjangoObjectType

import graphql_jwt
from graphql_jwt.shortcuts import get_token

from django.contrib.auth.models import User as UserModel
from tastypie.models import ApiKey as ApiKeyModel

from .utils import ExtendedConnection


class UserType(DjangoObjectType):
    class Meta:
        model = UserModel
        fields = ('id', 'username', 'first_name', 'last_name', 'email')
        interfaces = (graphene.Node,)
        connection_class = ExtendedConnection


class UserSignIn(graphql_jwt.relay.JSONWebTokenMutation):
    user = graphene.Field(UserType)

    @classmethod
    def resolve(cls, self, info, **kwargs):
        return cls(user=info.context.user)


class ApiSignIn(graphene.Mutation):
    class Input:
        key = graphene.String(required=True)

    token = graphene.String()
    user = graphene.Field(UserType)

    def mutate(self, info, **kwargs):
        key = ApiKeyModel.objects.filter(key=kwargs.get('key'))
        if len(key) == 1:
            user = key[0].user
            return ApiSignIn(token=get_token(user), user=user)
        raise GraphQLError('Access denied.')
