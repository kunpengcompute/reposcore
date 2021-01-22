import git


class Progress(git.remote.RemoteProgress):
    def __init__(self, name):
        super(Progress, self).__init__()
        self.name = name

    def update(self, op_code, cur_count, max_count=None, message=''):
        print('Cloning %s, %s' % (self.name, self._cur_line))
