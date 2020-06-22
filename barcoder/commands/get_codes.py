"""Get a bunch of codes
"""

import logging
import sys
import argparse
import csv

from barcoder.utils import get_code

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-n', '--number', type=int, default=1)
    parser.add_argument('-l', '--length', type=int, default=16)
    parser.add_argument('-o', '--outfile', help="Output file",
                        default=sys.stdout, type=argparse.FileType('w'))


def action(args):
    for i in range(args.number):
        args.outfile.write(get_code(length=args.length) + '\n')
