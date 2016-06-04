from __future__ import print_function
from builtins import str
import zerorpc
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
endpoint = sys.argv[1]

remote = zerorpc.Client()
remote.debug = True
remote.connect(endpoint)
print('Client Initialised', endpoint) 

assert remote.echo(42) == 42
assert remote.echo(42.42) == 42.42
assert remote.echo(b'random bytes') == b'random bytes'
assert remote.echo(u'unicode string') == u'unicode string'
assert remote.echo('default string') == 'default string'

remote.quit()

print("All tests passed.")
