"""
Assembles subcommands and provides top-level script.
"""

import argparse
from argparse import (RawDescriptionHelpFormatter, OPTIONAL,
                      ZERO_OR_MORE, ONE_OR_MORE, REMAINDER, PARSER)
import logging
import pkgutil
import sys
from importlib import import_module

from barcoder import commands, __doc__ as docstring, __version__


class MyRawDescriptionHelpFormatter(RawDescriptionHelpFormatter):
    """Subclass RawDescriptionHelpFormatter to prevent duplication of
    choice list when nargs is '*' or '+'.

    """

    def _format_args(self, action, default_metavar):
        get_metavar = self._metavar_formatter(action, default_metavar)
        if action.nargs in {None, OPTIONAL, ZERO_OR_MORE, ONE_OR_MORE}:
            result = '%s' % get_metavar(1)
        elif action.nargs == REMAINDER:
            result = '...'
        elif action.nargs == PARSER:
            result = '%s ...' % get_metavar(1)
        else:
            formats = ['%s' for _ in range(action.nargs)]
            result = ' '.join(formats) % get_metavar(action.nargs)
        return result


def parse_arguments(argv):
    """
    Create the argument parser
    """

    parser = argparse.ArgumentParser(
        description=docstring, formatter_class=MyRawDescriptionHelpFormatter)

    parser.add_argument('-V', '--version', action='version',
                        version=__version__,
                        help='Print the version number and exit')
    parser.add_argument('-v', '--verbose',
                        action='count', dest='verbosity', default=1,
                        help='Increase verbosity of screen output (eg, -v is verbose, '
                        '-vv more so)')
    parser.add_argument('-q', '--quiet',
                        action='store_const', dest='verbosity', const=0,
                        help='Suppress output')

    ##########################
    # Setup all sub-commands #
    ##########################

    subparsers = parser.add_subparsers(dest='subparser_name', title='actions')

    # Begin help sub-command
    parser_help = subparsers.add_parser(
        'help', help='Detailed help for actions using `help <action>`')
    parser_help.add_argument('action', nargs=1)
    # End help sub-command

    # Organize submodules by argv
    modules = [name for _, name, _ in pkgutil.iter_modules(commands.__path__)]
    modules = [m for m in modules if not m.startswith('_')]

    # `run` will contain the module corresponding to a single
    # subcommand if provided; otherwise, generate top-level help
    # message from all submodules in `modules`.
    run = list(filter(lambda name: name in argv, modules))
    actions = {}

    for name in run or modules:
        # set up subcommand help text. The first line of the dosctring
        # in the module is displayed as the help text in the
        # script-level help message (`script -h`). The entire
        # docstring is displayed in the help message for the
        # individual subcommand ((`script action -h`))
        # if no individual subcommand is specified (run_action[False]),
        # a full list of docstrings is displayed
        mod = import_module('{}.{}'.format(commands.__name__, name))

        if mod.__doc__.strip():
            helpstr = mod.__doc__.lstrip().split('\n', 1)[0]
        else:
            helpstr = '<add help text in docstring>'

        subparser = subparsers.add_parser(
            name, help=helpstr,
            description=mod.__doc__,
            formatter_class=MyRawDescriptionHelpFormatter)
        mod.build_parser(subparser)
        actions[name] = mod.action

    # Determine we have called ourself (e.g. "help <action>")
    # Set arguments to display help if parameter is set
    #           *or*
    # Set arguments to perform an action with any specified options.
    arguments = parser.parse_args(argv)
    # Determine which action is in play.
    action = arguments.subparser_name

    # Support help <action> by simply having this function call itself and
    # translate the arguments into something that argparse can work with.
    if action is None:
        return parse_arguments(['-h'])
    elif action == 'help':
        return parse_arguments([str(arguments.action[0]), '-h'])
    else:
        return actions[action], arguments


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    action, arguments = parse_arguments(argv)

    loglevel = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }.get(arguments.verbosity, logging.DEBUG)

    if arguments.verbosity > 1:
        logformat = '%(levelname)s %(module)s.%(funcName)s() %(lineno)s %(message)s'
    else:
        logformat = '%(message)s'

    logging.basicConfig(stream=sys.stderr, format=logformat, level=loglevel)

    return action(arguments)
