
class Widget:

    def __init__(self, options=dict()):
        self.options = options

    def run(self):
        raise NotImplementedError

    def __str__(self):
        return self.xml()

    def xml(self):
        return self.run()
