import graphene
from graphene import relay
from graphene_django_plus.types import ModelType
from graphql import GraphQLError

import graphql_jwt
from graphql_jwt.shortcuts import get_token

from django.contrib.auth.models import User as UserModel
from tastypie.models import ApiKey as ApiKeyModel

from .utils import ExtendedConnection


class UserType(ModelType):
    class Meta:
        model = UserModel
        fields = ('id', 'username', 'first_name', 'last_name', 'email')
        interfaces = [relay.Node]
        connection_class = ExtendedConnection


class UserSignIn(graphql_jwt.relay.JSONWebTokenMutation):
    user = graphene.Field(UserType)

    @classmethod
    def resolve(cls, self, info, **kwargs):
        return cls(user=info.context.user)


class ApiSignInInput(graphene.InputObjectType):
    key = graphene.String(required=True)


class ApiSignIn(graphene.Mutation):
    class Arguments:
        input = ApiSignInInput(required=True)

    token = graphene.String()
    user = graphene.Field(UserType)

    def mutate(self, info, input=None):
        key = ApiKeyModel.objects.filter(key=input.key)
        if len(key) == 1:
            user = key[0].user
            return ApiSignIn(token=get_token(user), user=user)
        raise GraphQLError('Access denied.')
