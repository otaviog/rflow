import rflow


class CreateMessage(rflow.Interface):
    def evaluate(self, msg):
        return msg


class Print(rflow.Interface):
    def evaluate(self, msg):
        print(msg)


@rflow.graph()
def hello(g):
    g.create = CreateMessage()
    g.create.args.msg = "Hello"

    g.print = Print()
    g.print.args.msg = g.create


if __name__ == '__main__':
    rflow.command.main()
