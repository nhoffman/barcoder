"""Three-column QR code layout
"""

# https://gist.github.com/lkrone/04ca0e3ae3a78f434e5ac84cfd9ca6b1
# https://programtalk.com/vs2/python/8113/ReportLab/tests/test_graphics_images.py/

import logging
import tempfile
import os
from os import path
import datetime
import argparse
import sys
from collections import namedtuple
from pathlib import Path
import csv

from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Drawing, String, Image
from reportlab.graphics import renderPDF
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch

from barcoder.utils import (get_chunks, get_code, get_qr, get_code128, hline, vline)

log = logging.getLogger(__name__)

URL = 'https://securelink.labmed.uw.edu'

VERSION = 4

Layout = namedtuple('Layout', ['pagesize', 'label_height', 'label_width',
                               'num_x', 'num_y',
                               'margin_left', 'margin_bottom',
                               'vspace', 'hspace'])

layout1 = Layout(pagesize=letter, label_height=1 * inch, label_width=2.5 * inch,
                 num_x=3, num_y=8,
                 margin_left=(5 / 16) * inch, margin_bottom=(5 / 8) * inch,
                 vspace=0.25 * inch, hspace=(3 / 16) * inch)

layout2 = Layout(pagesize=letter, label_height=1 * inch, label_width=(2 + 5 / 8) * inch,
                 num_x=3, num_y=10,
                 margin_left=(3 / 16) * inch, margin_bottom=0.5 * inch,
                 vspace=0, hspace=(1 / 8) * inch)


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


def specimenlabel(layout, code, img, counter, batch=None):
    label_drawing = Drawing(layout.label_width, layout.label_height)

    # x, y, width, height, path
    bc_width = 2.2 * inch
    bc_height = 0.5 * inch
    barcode = Image(0, 0, bc_width, bc_height, img)
    label_drawing.add(barcode)

    label_drawing.add(String(layout.label_width - 5, 16,
                             text=f'{counter}',
                             fontName="Helvetica", fontSize=6, textAnchor="end"))

    label_drawing.add(String(layout.label_width - 5, 7,
                             text='specimen',
                             fontName="Helvetica", fontSize=6, textAnchor="end"))

    label_drawing.add(String(5, bc_height + 5,
                             'DOB (MM/DD/YYYY): ____________________',
                             fontName="Helvetica", fontSize=8, textAnchor="start"))

    label_drawing.add(String(5, bc_height + 18,
                             'Name: ________________________________',
                             fontName="Helvetica", fontSize=8, textAnchor="start"))

    return label_drawing


def lablabel(layout, code, counter, batch=None):
    label_drawing = Drawing(layout.label_width, layout.label_height)
    # text positioning relative to top of label
    lmar = 5

    # x, y, width, height, path
    bc_width = 2 * inch
    bc_height = 0.5 * inch

    label_drawing.add(String(bc_width, 55,
                             text=f'{counter} v{VERSION}',
                             fontName="Helvetica", fontSize=8, textAnchor="start"))

    label_drawing.add(String(bc_width, 45,
                             text=batch,
                             fontName="Helvetica", fontSize=8, textAnchor="start"))

    ypos = 25
    label_drawing.add(String(lmar, ypos,
                             text='This label may be discarded',
                             fontName="Helvetica-Bold",
                             fontSize=10, textAnchor="start"))

    ypos = 15
    label_drawing.add(String(lmar, ypos,
                             '<-- place on specimen',
                             fontName="Helvetica",
                             fontSize=8, textAnchor="start"))

    ypos = 5
    label_drawing.add(String(lmar, ypos,
                             '     give to individual being tested -->',
                             fontName="Helvetica",
                             fontSize=8, textAnchor="start"))

    return label_drawing


def qrlabel(layout, code, img, counter, batch=None):
    label_drawing = Drawing(layout.label_width, layout.label_height)

    # x, y, width, height, path
    bc_edge = 0.75 * inch
    barcode = Image(0, 0, bc_edge, bc_edge, img)
    label_drawing.add(barcode)

    label_drawing.add(String(2, layout.label_height - 14,
                             text=URL,
                             fontName="Helvetica-Bold", fontSize=11, textAnchor="start"))

    label_drawing.add(String(bc_edge + 2, layout.label_height - 30,
                             text='Visit URL or scan QR code',
                             fontName="Helvetica", fontSize=10, textAnchor="start"))

    label_drawing.add(String(bc_edge + 2, layout.label_height - 42,
                             text='Your retrieval code:',
                             fontName="Helvetica", fontSize=10, textAnchor="start"))

    label_drawing.add(String(bc_edge + 2, layout.label_height - 54,
                             '-'.join(get_chunks(code, 4)),
                             fontName="Helvetica-Bold",
                             fontSize=10, textAnchor="start"))

    label_drawing.add(String(bc_edge + 2, layout.label_height - 64,
                             f'Testing by Univ. of Washington  {counter}',
                             fontName="Helvetica-Oblique",
                             fontSize=7, textAnchor="start"))

    return label_drawing


def fill_sheet(canvas, layout, page_number, code_length, fake_code=None, batch=None):

    if fake_code:
        if len(fake_code) != code_length:
            raise ValueError(f'fake code {fake_code} must be the specified length ({code_length})')

    codes = []

    with tempfile.TemporaryDirectory() as d:
        ypos = layout.margin_bottom
        for label_number in reversed(range(layout.num_y)):
            code = fake_code or get_code(code_length)
            codes.append(code)
            counter = f'({page_number + 1}-{label_number + 1})'

            # generate barcode images
            code128_path = path.join(d, code) + '-code128.png'
            with open(code128_path, 'wb') as f:
                f.write(get_code128(code))

            qr_path = path.join(d, code) + '-qr.png'
            with open(qr_path, 'wb') as f:
                f.write(get_qr(f'{URL}?code={code}', border=4))

            # first column
            label1 = specimenlabel(layout, code, code128_path, counter, batch)
            renderPDF.draw(label1, canvas, layout.margin_left, ypos)

            # second column
            label2 = lablabel(layout, code, counter, batch)
            renderPDF.draw(label2, canvas,
                           layout.margin_left + layout.label_width + layout.hspace,
                           ypos)

            # third column
            label3 = qrlabel(layout, code, qr_path, counter, batch)
            renderPDF.draw(label3, canvas,
                           layout.margin_left + 2 * (layout.label_width + layout.hspace),
                           ypos)

            ypos += layout.label_height + layout.vspace

    return codes


def build_parser(parser):

    parser.add_argument('-o', '--outfile',
                        default='securelink-3x10-{batch}-{fileno:03d}-n{npages}.pdf',
                        help='File name template [%(default)s]')
    parser.add_argument('-d', '--dirname', default='.',
                        help='directory for output [%(default)s]')
    parser.add_argument('-n', '--npages', default=1, type=int, help='[default %(default)s]')
    parser.add_argument('-N', '--nfiles', default=1, type=int, help='[default %(default)s]')
    parser.add_argument('-b', '--batch', default='',
                        help='batch identifier (placed on lab label)')
    parser.add_argument('--grid', help='draw grid',
                        action='store_true', default=False)
    parser.add_argument('--vline', help='include vertical line in grid',
                        action='store_true', default=False)
    parser.add_argument('--fake-code', help='fill sheet with this fake code')
    parser.add_argument('-l', '--code-length', metavar='N', type=int, default=16,
                        help='Total length of code in characters [%(default)s]')


def action(args):
    layout = layout2

    outdir = Path(args.dirname)
    outdir.mkdir(parents=True, exist_ok=True)

    for fileno in range(1, args.nfiles + 1):
        outfile = outdir / args.outfile.format(
            batch=args.batch or '',
            fileno=fileno,
            npages=args.npages
        )
        print(outfile)

        logfilename = str(outfile).replace('.pdf', '.csv')
        with open(logfilename, 'w') as f:
            writer = csv.writer(f)

            canvas = Canvas(str(outfile), pagesize=layout.pagesize)
            for page_number in range(args.npages):

                codes = fill_sheet(
                    canvas,
                    layout=layout,
                    page_number=page_number,
                    code_length=args.code_length,
                    fake_code=args.fake_code,
                    batch=args.batch)

                if args.grid:
                    draw_grid(canvas, layout=layout, include_vline=args.vline)
                # starts a new page
                canvas.showPage()

                for code in codes:
                    writer.writerow([outfile, page_number + 1, code])

            canvas.save()

