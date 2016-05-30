from __future__ import print_function
import zerorpc
import sys

endpoint = sys.argv[1]

remote = zerorpc.Client(endpoint)
print('Client Initialised', endpoint) 

assert remote.echo(42) == 42
assert remote.echo(42.42) == 42.42
assert remote.echo(b'random bytes') == b'random bytes'
assert remote.echo(u'unicode string') == u'unicode string'
assert remote.echo('unicode string') == 'unicode string'

remote.quit()

print("All tests passed.")
