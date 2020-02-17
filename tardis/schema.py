import graphene
from tardis.tardis_portal.graphql.schema import tardisQuery, tardisMutation


class Query(tardisQuery, graphene.ObjectType):
    pass

class Mutation(tardisMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
