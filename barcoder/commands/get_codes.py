"""Get a bunch of codes
"""

import logging
import sys
import argparse
import csv

from barcoder.utils import generate_codes, get_code

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-n', '--number', type=int, default=1)
    parser.add_argument('-l', '--length', type=int, default=16)
    parser.add_argument('-s', '--stop-if-seen', action='store_true', default=False)
    parser.add_argument('--alpha-chars', help='limit to these characters')
    parser.add_argument('-o', '--outfile', help="Output file",
                        default=sys.stdout, type=argparse.FileType('w'))


def action(args):

    if args.alpha_chars:
        codes = (get_code(args.length, alphanum_chars=list(args.alpha_chars.upper()))
                 for i in range(args.number))
    else:
        codes = generate_codes(args.length, stop_if_seen=args.stop_if_seen)

    for i in range(args.number):
        args.outfile.write(next(codes) + '\n')
