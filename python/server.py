
from __future__ import print_function
import logging
import sys
import zerorpc


logging.basicConfig(level=logging.DEBUG)
endpoint = sys.argv[1]

class TestServer(zerorpc.Server):

    def echo(self, v):
        print("echo {0} <{1}>".format(type(v), v))
        return v

    def quit(self):
        print("exiting...")
        self.stop()

server = TestServer()
server.bind(endpoint)
print('Server started', endpoint)
server.run()
