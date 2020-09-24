"""Labels for pooled specimens
"""

# https://gist.github.com/lkrone/04ca0e3ae3a78f434e5ac84cfd9ca6b1
# https://programtalk.com/vs2/python/8113/ReportLab/tests/test_graphics_images.py/

import logging
import tempfile
import os
from os import path
from datetime import datetime
import argparse
import sys
from collections import namedtuple
from pathlib import Path
from itertools import count

from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Drawing, String, Image
from reportlab.graphics import renderPDF
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch

from barcoder.utils import (get_chunks, get_pool_label, hline, vline)

log = logging.getLogger(__name__)


VERSION = 1

Layout = namedtuple('Layout', ['pagesize', 'label_height', 'label_width',
                               'num_x', 'num_y',
                               'margin_left', 'margin_bottom',
                               'vspace', 'hspace'])

avery94203 = Layout(pagesize=letter, label_height=0.5 * inch, label_width=1.75 * inch,
                    num_x=4, num_y=20,
                    margin_left=(5 / 16) * inch, margin_bottom=(17 / 32) * inch,
                    vspace=0 * inch, hspace=(5 / 16) * inch)


def generate_codes(timestamp, page):
    # V333327469
    # PYYDDDPNNC
    # PYYMMDDPNNC
    counter = count()
    while True:
        c = next(counter)
        check_digit = 0
        yield f'P{timestamp}-{page:02}-{c:02}-{check_digit}'


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


def specimenlabel(layout, code, img):
    label_drawing = Drawing(layout.label_width, layout.label_height)

    bc_width = 1.75 * inch
    bc_height = 0.4 * inch
    barcode = Image(x=0, y=0, width=bc_width, height=bc_height, path=img)
    label_drawing.add(barcode)

    # label_drawing.add(String(layout.label_width - 5, 16,
    #                          text=f'{counter}',
    #                          fontName="Helvetica", fontSize=6, textAnchor="end"))

    # label_drawing.add(String(layout.label_width - 5, 7,
    #                          text='specimen',
    #                          fontName="Helvetica", fontSize=6, textAnchor="end"))

    # label_drawing.add(String(5, bc_height + 5,
    #                          'DOB (MM/DD/YYYY): ____________________',
    #                          fontName="Helvetica", fontSize=8, textAnchor="start"))

    # label_drawing.add(String(5, bc_height + 18,
    #                          'Name: ________________________________',
    #                          fontName="Helvetica", fontSize=8, textAnchor="start"))

    return label_drawing


def fill_sheet(canvas, layout, timestamp, page_number, fake_code=None):

    codes = generate_codes(timestamp=timestamp, page=page_number)
    with tempfile.TemporaryDirectory() as d:
        ypos = layout.margin_bottom
        for label_number in range(layout.num_y):
            for i in range(layout.num_x):
                code = fake_code or next(codes)

                # generate barcode images
                code128_path = path.join(d, code) + '-code128.png'
                with open(code128_path, 'wb') as f:
                    f.write(get_pool_label(code))

                label = specimenlabel(layout, code, code128_path)
                renderPDF.draw(
                    label,
                    canvas,
                    layout.margin_left + i * (layout.label_width + layout.hspace),
                    ypos)

            ypos += layout.label_height + layout.vspace


def build_parser(parser):

    parser.add_argument('-o', '--outfile',
                        default='pool-labels-{timestamp}-f{fileno:03d}-n{npages}.pdf',
                        help='File name template [%(default)s]')
    parser.add_argument('-d', '--dirname', default='.',
                        help='directory for output [%(default)s]')
    parser.add_argument('-t', '--timestamp', default=datetime.now().strftime('%y%m%d'),
                        help='[default %(default)s]')
    parser.add_argument('-n', '--npages', default=1, type=int,
                        help='number of pages, max 99 [default %(default)s]')
    parser.add_argument('-N', '--nfiles', default=1, type=int, help='[default %(default)s]')
    parser.add_argument('--grid', help='draw grid',
                        action='store_true', default=False)
    parser.add_argument('--fake-code', help='fill sheet with this fake code')


def action(args):
    layout = avery94203

    if args.npages > 99:
        sys.exit('The maximum number of pages is 99')

    outdir = Path(args.dirname)
    outdir.mkdir(parents=True, exist_ok=True)

    for fileno in range(1, args.nfiles + 1):
        outfile = outdir / args.outfile.format(
            timestamp=args.timestamp,
            fileno=fileno,
            npages=args.npages
        )

        print(outfile)

        canvas = Canvas(str(outfile), pagesize=layout.pagesize)
        for page_number in range(args.npages):
            fill_sheet(canvas, layout=layout, page_number=page_number + 1,
                       timestamp=args.timestamp, fake_code=args.fake_code)
            if args.grid:
                draw_grid(canvas, layout=layout, include_vline=True)
            # starts a new page
            canvas.showPage()

        canvas.save()

