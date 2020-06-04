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
    bc_width = 2 * inch
    bc_height = 0.5 * inch
    barcode = Image(0, 0, bc_width, bc_height, img)
    label_drawing.add(barcode)

    label_drawing.add(String(bc_width, 7,
                             text=f'{counter} v{VERSION}',
                             fontName="Helvetica", fontSize=8, textAnchor="start"))

    label_drawing.add(String(bc_width, 16,
                             text=batch,
                             fontName="Helvetica", fontSize=8, textAnchor="start"))

    label_drawing.add(String(bc_width, 26,
                             text='specimen',
                             fontName="Helvetica", fontSize=8, textAnchor="start"))

    label_drawing.add(String(5, bc_height + 5,
                             'DOB (MM/DD/YYYY): ____________________',
                             fontName="Helvetica", fontSize=8, textAnchor="start"))

    label_drawing.add(String(5, bc_height + 18,
                             'Name: ________________________________',
                             fontName="Helvetica", fontSize=8, textAnchor="start"))

    return label_drawing


def lablabel(layout, code, img, counter, batch=None):
    label_drawing = Drawing(layout.label_width, layout.label_height)
    # text positioning relative to top of label
    lmar = 5

    # x, y, width, height, path
    bc_width = 2 * inch
    bc_height = 0.5 * inch
    barcode = Image(0, 30, bc_width, bc_height, img)
    label_drawing.add(barcode)

    label_drawing.add(String(bc_width, 55,
                             text=f'{counter} v{VERSION}',
                             fontName="Helvetica", fontSize=8, textAnchor="start"))

    label_drawing.add(String(bc_width, 45,
                             text=batch,
                             fontName="Helvetica", fontSize=8, textAnchor="start"))

    ypos = 25
    label_drawing.add(String(lmar, ypos,
                             text='Place on lab requisition',
                             fontName="Helvetica-Bold",
                             fontSize=10, textAnchor="start"))

    ypos = 15
    label_drawing.add(String(lmar, ypos,
                             'Lab: if order contains QRCODE scan there;',
                             fontName="Helvetica",
                             fontSize=8, textAnchor="start"))

    ypos = 5
    label_drawing.add(String(lmar, ypos,
                             'if not, add QRCOD and scan result at prompt.',
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


def fill_sheet(canvas, layout, page_number, fake_code=None, batch=None):

    with tempfile.TemporaryDirectory() as d:
        ypos = layout.margin_bottom
        for label_number in range(layout.num_y):
            code = fake_code or get_code()
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
            label2 = lablabel(layout, code, code128_path, counter, batch)
            renderPDF.draw(label2, canvas,
                           layout.margin_left + layout.label_width + layout.hspace,
                           ypos)

            # third column
            label3 = qrlabel(layout, code, qr_path, counter, batch)
            renderPDF.draw(label3, canvas,
                           layout.margin_left + 2 * (layout.label_width + layout.hspace),
                           ypos)

            ypos += layout.label_height + layout.vspace



def build_parser(parser):

    parser.add_argument('-o', '--outfile',
                        default='securelink-3x10-{batch}-{fileno:03d}-n{npages}.pdf',
                        help='File name template [%(default)s]')
    parser.add_argument('-d', '--dirname', default='.',
                        help='directory for output [%(default)s]')
    parser.add_argument('-n', '--npages', default=1, type=int)
    parser.add_argument('-N', '--nfiles', default=1, type=int)
    parser.add_argument('-b', '--batch', help='batch identifier (placed on lab label)')
    parser.add_argument('--vline', help='draw vertical line',
                        action='store_true', default=False)
    parser.add_argument('--fake-code', help='fill sheet with this fake code')


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

        canvas = Canvas(str(outfile), pagesize=layout.pagesize)
        for page_number in range(args.npages):
            fill_sheet(canvas, layout=layout, page_number=page_number,
                       fake_code=args.fake_code, batch=args.batch)
            draw_grid(canvas, layout=layout, include_vline=args.vline)
            # starts a new page
            canvas.showPage()

        canvas.save()

