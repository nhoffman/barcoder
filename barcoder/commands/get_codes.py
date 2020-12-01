"""Get a bunch of codes
"""

import logging
import sys
import argparse
import csv

from barcoder.utils import generate_codes

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-n', '--number', type=int, default=1)
    parser.add_argument('-l', '--length', type=int, default=16)
    parser.add_argument('-s', '--stop-if-seen', action='store_true', default=False)
    parser.add_argument('-o', '--outfile', help="Output file",
                        default=sys.stdout, type=argparse.FileType('w'))


def action(args):

    codes = generate_codes(args.length, stop_if_seen=args.stop_if_seen)

    for i in range(args.number):
        args.outfile.write(next(codes) + '\n')
