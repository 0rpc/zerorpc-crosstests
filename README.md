# zerorpc cross languages tests

[![Build Status](https://travis-ci.org/0rpc/zerorpc-crosstests.svg?branch=master)](https://travis-ci.org/0rpc/zerorpc-crosstests)

Few tests for testing zerorpc across supported languages.
The goal is to catch very visible protocol errors quickly.

## Quick start

Dependencies:
 - python 2.6, 2.7 and 3.4 (take a look at the ppa deadsnake for ubuntu).
 - nodejs (with the executable called "node", package nodejs-legacy on ubuntu).
 
 `crosstests.py` itself works on Python3.
 
Make sure to have proper path to zerorpc language specific implementation in `testmatrix.yaml`.
 
```shell
pip install -r requirements.txt
./crosstests.py setup
./crosstests.py test
```

Note: no need to re-run `./crosstests.py setup` after modifying a zerorpc language specific implementation,
they are symlinked in the test environements for conveniance.

## Directory structure

A test must implement a server and client compatible with all other test servers and clients.

The directoy structure of a test is:
 - testname/setup
 
Any other files are ignored, for example the `python` test contains:
 - setup
 - client.py
 - server.py
 - requirements.txt
 
`setup` must be an executable (likely a shell script) that will be invoked like so:
```shell
cd testenvs/testname-${VERSION}
[...]/testname/setup ZERORPC_SRC VERSION
```

`setup` can find its original src directory, example:
```shell
SRC_DIR="$(dirname "$(readlink -f "$0")")"
```

`ZERORPC_SRC` is the zerorpc language specific implementation to use for testing, it should be symliked
to save us from running `setup` before every test.

`VERSION` comes from the list of version per test in `testmatrix.yaml`.
A special `VERSION` is `default`, which means use whatever sensible `default`.

For example, `python/setup` uses `VERSION` to choose which `python` interpreter version to use.
If `default` it will use the executable `python` from the current environement else it will use `python-${VERSION}`.

`setup` must generate two executables: `server` and `client`, taking a zerorpc endpoint as unique parameter.
Both `python` and `node` tests are generating small shell scripts stubs for `server` and `client` to run `server/client.{py/js}`
the files from `SRC_DIR` in the right environment.

## Test matrix

The file `testmatrix.yaml` defines for every test directory what `version`
should run and the path to the corresponding zerorpc repository implementation.
