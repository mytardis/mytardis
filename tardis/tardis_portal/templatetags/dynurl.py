from django.template import Library, Node, Variable
from django.urls import reverse

register = Library()


class DynUrlNode(Node):
    def __init__(self, *args):
        self.name_var = Variable(args[0])
        self.args = [Variable(a) for a in args[1].split(",")]

    def render(self, context):
        name = self.name_var.resolve(context)
        args = [a.resolve(context) for a in self.args]
        return reverse(name, args=args)


@register.tag
def dynurl(parser, token):
    args = token.split_contents()
    return DynUrlNode(*args[1:])
