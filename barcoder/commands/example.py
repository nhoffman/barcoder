"""An example subcommand
"""

import logging
import sys
import argparse
import csv


log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-o', '--outfile', help="Output file",
                        default=sys.stdout, type=argparse.FileType('w'))


def action(args):
    args.outfile.write('hithere\n')
