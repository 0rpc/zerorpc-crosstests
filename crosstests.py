#!/usr/bin/env python

import os
import sys
import yaml
import argparse
import subprocess
import itertools
import random
import select
import fcntl
import time
import io 
import errno


class TestDef(object):

    def __init__(self, name, version, spec):
        self.name = name
        self.version = version
        self.spec = spec

    @property
    def display_name(self):
        return self.name + '-' + self.version

    def env_dir(self, home_dir):
        env_dir = 'testenvs/' + self.name
        if self.version != 'default':
            env_dir = env_dir + '_' + self.version
        return self._resolve_path(home_dir, env_dir)

    def zerorpc_src(self, home_dir):
        return os.path.abspath(self._resolve_path(home_dir, self.spec['zerorpc_src']))

    def setup_executable(self, home_dir):
        return self._resolve_path(home_dir, os.path.join(self.name, 'setup'))

    def _resolve_path(self, home_dir, path):
        if not path.startswith('/'):
            path = os.path.join(home_dir, path)
        return path
    
    def execv(self, home_dir, executable, args):
        env_dir = self.env_dir(home_dir)
        cmd = './' + executable
        print('-- cd', env_dir)
        os.chdir(env_dir)
        print('--', cmd, ''.join(args))
        os.execv(cmd, [cmd] + args)


def action_setup(home_dir, matrix, args):
    print('-- setup tests environments')
            
    home = os.getcwd()
    for test in selected_tests(matrix, args.test):

        env_dir = test.env_dir(home_dir)
        print('-- cd', env_dir)

        try:
            os.makedirs(env_dir)
        except FileExistsError:
            pass
        os.chdir(env_dir)

        zerorpc_src = test.zerorpc_src(home_dir)
        setup_executable = test.setup_executable(home_dir)
        cmd = [setup_executable, zerorpc_src, test.version]
        print('   .../{0}/setup {1} {2}'.format(test.name, zerorpc_src, test.version))
        subprocess.check_call(cmd)

def action_run(home_dir, matrix, args):
    test = next(selected_tests(matrix, [args.test]))
    test.execv(home_dir, args.executable, [args.endpoint])


class TestPairProcess(object):

    def __init__(self, process, stdout, stderr):
        self.process = process
        self.stdout = stdout
        self.stderr = stderr

    @property
    def running(self):
        return self.process.returncode is None

    def kill_and_reap(self):
        self.process.kill()
        self.process.wait()


class TestPair(object):

    TIMEOUT_S = 5.0
    TERMINATE_TIMEOUT_S = 2.0

    def __init__(self, client_test, server_test):
        self.client = client_test
        self.server = server_test
        self.client_status = None
        self.server_status = None
        self.client_output = ([], [])
        self.server_output = ([], [])

    def is_success(self):
        return self.client_status == 0 and self.server_status == 0

    def run_test(self, home_dir):
        print('## START {0}/client <-> {1}/server'.format(
            self.client.display_name, self.server.display_name))
        endpoint = None
        server = None
        client = None

        try:
            endpoint = self.random_ipc_endpoint()
            server = self.spawn_test_process(home_dir, self.server,
                    './server', [endpoint])
            client = self.spawn_test_process(home_dir, self.client,
                    './client', [endpoint])

            outputs = {
                    server.stdout: ('-- server', self.server_output[0]),
                    server.stderr: ('!! server', self.server_output[1]),
                    client.stdout: ('-- client', self.client_output[0]),
                    client.stderr: ('!! client', self.client_output[1]),
                    }

            print('-- Waiting up to {0}s for test run'.format(self.TIMEOUT_S))
            start = time.time()
            deadline = start + self.TIMEOUT_S
            completed = self.collect_output(start, deadline, server, client,
                    outputs, wait_for_all=False)

            if completed:
                waiting = True

                if server.process.returncode is None:
                    print('-- waiting {0}s after server {1}'.format(
                        self.TERMINATE_TIMEOUT_S, server.process.pid))
                elif server.process.returncode != 0:
                    waiting = False

                if waiting:
                    if client.process.returncode is None:
                        print('-- waiting {0}s after client {1}'.format(
                            self.TERMINATE_TIMEOUT_S, client.process.pid))
                    elif client.process.returncode != 0:
                        waiting = False

                if waiting:
                    deadline = time.time() + self.TERMINATE_TIMEOUT_S
                    completed = self.collect_output(start, deadline, server,
                            client, outputs, wait_for_all=True)
                    if not completed:
                        print('!! process took too long to terminate!')
            else:
                print('!! test took too long!')

        except Exception as e:
            print('!!', e)
        finally:
            if client and client.running:
                print('-- killing client', client.process.pid)
                client.kill_and_reap()
            if server and server.running:
                print('-- killing server', server.process.pid)
                server.kill_and_reap()
            self.unlink(endpoint)

        self.server_status = server and server.process.returncode
        self.client_status = client and client.process.returncode

        print('-- client->{0}, server->{0}'.format(self.client_status, self.server_status))

        status = self.is_success() and 'SUCCESS' or 'FAILED'
        print('-- {0} {1}/client <-> {2}/server'.format(
            status, self.client.display_name, self.server.display_name))

    def spawn_test_process(self, home_dir, test, executable, args):
        env_dir = test.env_dir(home_dir)
        print('-- cd', env_dir)
        os.chdir(env_dir)
        cmd = [executable] + args
        print('--', ' '.join(cmd), '&')
        (stdout_master, stdout_slave) = os.openpty()
        (stderr_master, stderr_slave) = os.openpty()
        self.set_fd_nonblocking(stdout_master)
        self.set_fd_nonblocking(stderr_master)
        stdout_master = io.BufferedReader(io.FileIO(stdout_master))
        stderr_master = io.BufferedReader(io.FileIO(stderr_master))
        process = subprocess.Popen(cmd, stdout=stdout_slave, stderr=stderr_slave)
        os.close(stdout_slave)
        os.close(stderr_slave)
        print('-- pid', process.pid)
        return TestPairProcess(process, stdout_master, stderr_master)

    @staticmethod
    def collect_output(start, deadline, server, client, outputs, wait_for_all):
        while True:
            client.process.poll()
            server.process.poll()
            interesting_outputs = []
            if server.process.returncode is None:
                interesting_outputs.extend([server.stdout, server.stderr])
            if client.process.returncode is None:
                interesting_outputs.extend([client.stdout, client.stderr])
            if len(interesting_outputs) < (wait_for_all and 2 or 4):
                return True
            time_remaining = deadline - time.time()
            if time_remaining <= 0:
                return False
            (active_outputs, _, _) = select.select(interesting_outputs, [], [],
                    time_remaining)
            for output in active_outputs:
                try:
                    lines = output.readlines()
                except OSError as e:
                    if e.errno == errno.EIO:
                        continue
                    raise
                outputs[output][1].extend(lines)
                prefix = outputs[output][0]
                elapsed = time.time() - start
                for line in lines:
                    print('{0} [{1:.3f}s] {2}'.format(prefix, elapsed,
                        str(line.rstrip(), 'utf-8')))
        return True

    @staticmethod
    def random_ipc_endpoint():
        tmpfile = '/tmp/zerorpc_test_socket_{0}.sock'.format(
                str(random.random())[2:])
        return 'ipc://{0}'.format(tmpfile)

    @staticmethod
    def unlink(path):
        try:
            os.unlink(path)
        except Exception:
            pass

    @staticmethod
    def set_fd_nonblocking(fd):
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)


def action_test(home_dir, matrix, args):
    report = []
    tests = list(selected_tests(matrix, args.test))
    pairs = [TestPair(client_test, server_test) for client_test, server_test
            in itertools.product(tests, tests)]
    print('-- running {0} test pair(s)'.format(len(pairs)))
    for test_pair in pairs:
        test_pair.run_test(home_dir)

    print('-- summary')
    passed = sum(1 for test_pair in pairs if test_pair.is_success())
    total = len(pairs)
    for test_pair in pairs:
        status = test_pair.is_success() and '-- SUCCESS' or '!! FAILED '
        print('{0}: {1}/client <-> {2}/server'.format(
            status, test_pair.client.display_name, test_pair.server.display_name))
    print('-- {0}/{1} passed'.format(passed, total))
    if passed != total:
        return -1

def build_test_selection_map(matrix, selection_list):
    selection_map = {}
    for selected_test in selection_list:
        (test_name, test_version) = (selected_test.split('-', 1) + [None])[0:2]
        test_spec = matrix.get(test_name)

        if test_spec is None:
            raise Exception('Unknown test: {0} (typo?)'.format(selected_test))
        version_selection = selection_map.setdefault(test_name, set())

        if test_version:
            if test_version not in map(str, test_spec.get('vers', ['default'])):
                raise Exception('Unknown version: {0} (typo?)'.format(selected_test))
            version_selection.add(test_version)
    return selection_map

def selected_tests(matrix, selection_list):
    selection = build_test_selection_map(matrix, selection_list)
    for test_name, test_spec in matrix.items():
        if selection and test_name not in selection:
            continue
        versions = map(str, sorted(set(test_spec.get('vers', ['default']))))
        for version in versions:
            version_selection = selection.get(test_name)
            if version_selection and version not in version_selection:
                continue
            yield TestDef(test_name, version, test_spec)


parser = argparse.ArgumentParser(
        description='Run cross-language zerorpc tests.'
        )

parser.add_argument('--matrix', '-m', type=str, default='testmatrix.yaml',
                    help='The matrix yaml file to use', metavar='testmatrix.yaml')

actions_parser = parser.add_subparsers(help='action to run', dest='action')
actions_parser.required = True

setup_parser = actions_parser.add_parser('setup', help='setup all tests environments')
setup_parser.add_argument('test',
        type=str, metavar='test[-version]',
        help='only setup the given test & version', nargs='*')

run_parser = actions_parser.add_parser('run', help='run a test binary')
run_parser.add_argument('test',
        type=str, metavar='test-version',
        help='Run from the given test & version')
run_parser.add_argument('executable', choices=['server', 'client'],
        type=str, help='The executable to run')
run_parser.add_argument('endpoint',
        type=str, help='Network endpoint given to the executable')

test_parser = actions_parser.add_parser('test', help='run cross-languages tests')
test_parser.add_argument('test',
        type=str, metavar='test[-version]',
        help='only run the given tests & versions', nargs='*')

args = parser.parse_args()


matrix = yaml.load(open(args.matrix))
home_dir = os.path.abspath(os.path.realpath(os.path.dirname(args.matrix)))
print('-- loaded {0} (home: {1})'.format(os.path.basename(args.matrix), home_dir))

if not args.matrix:
    matrix = yaml.load(open(os.path.join(home_dir, 'testmatrix.yaml')))

action_f = getattr(sys.modules[__name__], 'action_' + args.action)
sys.exit(action_f(home_dir, matrix, args))
