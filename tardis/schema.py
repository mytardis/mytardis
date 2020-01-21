import graphene
import tardis.tardis_portal.graphql.schema


class Query(tardis.tardis_portal.graphql.schema.Query, graphene.ObjectType):
    pass

class Mutation(tardis.tardis_portal.graphql.schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
