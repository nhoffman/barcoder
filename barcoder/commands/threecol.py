"""Three-column QR code layout
"""

# https://gist.github.com/lkrone/04ca0e3ae3a78f434e5ac84cfd9ca6b1
# https://programtalk.com/vs2/python/8113/ReportLab/tests/test_graphics_images.py/

import logging
import tempfile
from os import path
import datetime
import argparse
import sys
from collections import namedtuple

from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Drawing, String, Image
from reportlab.graphics import renderPDF
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch

from barcoder.utils import (get_chunks, get_code, get_qr, get_code128, hline, vline)

log = logging.getLogger(__name__)

URL = 'https://securelink.labmed.uw.edu'

VERSION = 1

Layout = namedtuple('Layout', ['pagesize', 'label_height', 'label_width',
                               'num_x', 'num_y',
                               'margin_left', 'margin_bottom',
                               'vspace', 'hspace'])

layout1 = Layout(pagesize=letter, label_height=1 * inch, label_width=2.5 * inch,
                 num_x=3, num_y=8,
                 margin_left=(5 / 16) * inch, margin_bottom=(5 / 8) * inch,
                 vspace=0.25 * inch, hspace=(3 / 16) * inch)


def draw_grid(canvas, layout, include_vline=False):

    p = canvas.beginPath()

    if include_vline:
        vpos = layout.margin_left
        for i in range(layout.num_x):
            vline(p, vpos)
            vpos += layout.label_width
            vline(p, vpos)
            vpos += layout.hspace

        hpos = layout.margin_bottom
        for i in range(layout.num_y):
            hline(p, hpos)
            hpos += layout.label_height
            hline(p, hpos)
            hpos += layout.vspace

    p.close()
    canvas.drawPath(p)


def write_labels(outfile, npages=1, include_vline=False, fake_code=None, batch=None):

    canvas = Canvas(outfile, pagesize=PAGESIZE)
    for page_number in range(npages):
        # fill_sheet(canvas, page_number=page_number, fake_code=fake_code, batch=batch)
        draw_grid(canvas, include_vline=include_vline)

        # starts a new page
        canvas.showPage()

    canvas.save()


def build_parser(parser):
    parser.add_argument('-o', '--outfile',
                        help='Output file name (default '
                        'is "securelink-labels-{date}-n{npages}")')
    parser.add_argument('-n', '--npages', default=1, type=int)
    parser.add_argument('-b', '--batch', help='batch identifier (placed on lab label)')
    parser.add_argument('--vline', help='draw vertical line',
                        action='store_true', default=False)
    parser.add_argument('--fake-code', help='fill sheet with this fake code')


def action(args):
    if args.outfile:
        outfile = args.outfile
    else:
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        outfile = f'securelink-labels-{date}-n{args.npages}.pdf'

    print(f'writing {outfile}')

    layout = layout1

    canvas = Canvas(outfile, pagesize=layout.pagesize)
    for page_number in range(args.npages):
        draw_grid(canvas, layout=layout, include_vline=args.vline)

    canvas.save()

