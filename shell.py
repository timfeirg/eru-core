#!/usr/bin/env python
# coding: utf-8
import atexit
import os
import sys

import six

from eru.app import create_app_with_celery


def hook_readline_hist():
    try:
        # Try to set up command history completion/saving/reloading
        import readline
    except ImportError:
        return

    # The place to store your command history between sessions
    histfile = os.environ["HOME"] + "/.eru_history"
    readline.parse_and_bind('tab: complete')
    try:
        readline.read_history_file(histfile)
    except IOError:
        pass  # It doesn't exist yet.

    def savehist():
        try:
            readline.write_history_file(histfile)
        except:
            print 'Unable to save Python command history'
    atexit.register(savehist)


def pre_imports():
    from eru.models.base import Base
    from eru.models.host import Core, Host, _create_cores_on_host
    from eru.models.pod import Pod
    from eru.models.app import App, Version
    from eru.models.appconfig import AppConfig, ResourceConfig
    from eru.models.container import Container
    from eru.models.task import Task
    from eru.models.network import Network, IP
    from eru.models import db
    from eru.clients import rds, get_docker_client
    return locals()

def ipython_shell(user_ns):
    from IPython.terminal.ipapp import TerminalIPythonApp
    from IPython.terminal.interactiveshell import TerminalInteractiveShell

    class ShireIPythonApp(TerminalIPythonApp):
        def init_shell(self):
            self.shell = TerminalInteractiveShell.instance(
                config=self.config,
                display_banner=False,
                profile_dir=self.profile_dir,
                ipython_dir=self.ipython_dir,
                banner1=lambda: 'ERU shell.',
                banner2=''
            )
            self.shell.configurables.append(self)

    app = ShireIPythonApp.instance()
    app.initialize()
    app.shell.user_ns.update(user_ns)

    eru_app, _ = create_app_with_celery()
    with eru_app.app_context():
        sys.exit(app.start())

def get_notebook():
    from notebook.notebookapp import NotebookApp

    def install_kernel_spec(app, display_name, ipython_arguments):
        ksm = app.kernel_spec_manager
        try_spec_names = ['python2', 'python']
        if isinstance(try_spec_names, six.string_types):
            try_spec_names = [try_spec_names]
        ks = None
        for spec_name in try_spec_names:
            try:
                ks = ksm.get_kernel_spec(spec_name)
                break
            except:
                continue
        if not ks:
            raise Exception("No notebook (Python) kernel specs found")
        ks.argv.extend(ipython_arguments)
        ks.display_name = display_name

        current_dir, this_script = os.path.split(os.path.realpath(sys.argv[0]))

        if this_script == 'shell.py' and os.path.isdir(current_dir) and current_dir != os.getcwd():
            pythonpath = ks.env.get('PYTHONPATH', os.environ.get('PYTHONPATH', ''))
            pythonpath_list = pythonpath.split(':')
            if current_dir not in pythonpath_list:
                pythonpath_list.append(current_dir)

            ks.env['PYTHONPATH'] = ':'.join(filter(None, pythonpath_list))

        kernel_dir = os.path.join(ksm.user_kernel_dir, 'eru_kernel')
        if not os.path.exists(kernel_dir):
            os.makedirs(kernel_dir)
        with open(os.path.join(kernel_dir, 'kernel.json'), 'w') as f:
            f.write(ks.to_json())

    def run_notebook():
        app = NotebookApp.instance()

        # Treat IPYTHON_ARGUMENTS from settings
        ipython_arguments = []
        notebook_arguments = ['--no-browser']

        app.initialize(notebook_arguments)

        display_name = 'eru-shell'
        install_kernel_spec(app, display_name, ipython_arguments)

        app.start()

    return run_notebook


def main():
    # hook_readline_hist()
    # ipython_shell(pre_imports())
    get_notebook()()


if __name__ == '__main__':
    main()
