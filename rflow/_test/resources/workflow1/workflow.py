"""Very simple workflow for testing.
"""
import rflow

# pylint: disable=missing-docstring,no-self-use,invalid-name


class Add(rflow.Interface):
    """Add Interface doc.
    """

    def evaluate(self, a, b):
        return a + b


class Sub(rflow.Interface):
    """Sub Interface doc.
    """

    def evaluate(self, resource, a, b):
        return resource.pickle_dump(a - b)


@rflow.graph()
def workflow1(g):
    g.add = Add()
    g.add.args.a = 1
    g.add.args.b = 2

    g.sub = Sub(rflow.FSResource('sub.pkl'))
    g.sub.args.a = 8
    g.sub.args.b = g.add


if __name__ == '__main__':
    rflow.command.main()
