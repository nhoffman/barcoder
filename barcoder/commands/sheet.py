"""Print barcodes read from a csv file in a single column
"""

import logging
import tempfile
from os import path
import io
from pathlib import Path
from itertools import zip_longest
import csv
import argparse
import sys

from reportlab.graphics.shapes import Drawing, String, Image
from reportlab.graphics import renderPDF
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch

from barcoder import __version__, layouts
from barcoder.utils import get_pool_label, draw_grid

log = logging.getLogger(__name__)


def grouper(iterable, size, padvalue=None):
    "grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')"
    return zip_longest(*[iter(iterable)] * size, fillvalue=padvalue)


def specimenlabel(layout, img, barcode,
                  label1=None, label2=None, label3=None, label4=None, **ignored):

    label_drawing = Drawing(layout.label_width, layout.label_height)

    # adjust the width based on number of characters in
    # the barcode to preserve appropriate horizontal spacing
    code = barcode.replace('-', '')
    mils = 15 * 0.001
    alpha = len([c for c in code if c.isalpha()])
    num = len(code) - alpha
    # see https://www.traceability.com/calculators/7-code-128-barcode-length-calculator
    bc_width = (11 * alpha + 5.5 * num + 35) * mils * inch
    bc_height = 0.4 * inch
    lmar = 5

    # lay out grid of labels
    topy = bc_height + 15
    boty = bc_height + 4

    positions = [
        (lmar, topy),
        (lmar, boty),
        (lmar + layout.label_width / 2, topy),
        (lmar + layout.label_width / 2, boty),
    ]

    for label, (x, y) in zip([label1, label2, label3, label4], positions):
        if label:
            label_drawing.add(String(x=x, y=y, text=label, fontName="Helvetica", fontSize=8))

    barcode = Image(x=0, y=0, width=bc_width, height=bc_height, path=img)
    label_drawing.add(barcode)
    return label_drawing


def fill_sheet(canvas, codes, layout):
    """Fill the provided canvas with an array of labels. 'codes' is a
    sequence of dicts with required key 'barcode' and optional keys
    'label1' (...?). The sequence should be padded with falsy values
    (eg, None, {}, '', etc) to fill the sheet given the total number
    of rows and columns.

    """

    # reverse the order of codes
    codes = reversed(list(codes))

    with tempfile.TemporaryDirectory() as d:
        # start at the bottom of the page
        ypos = layout.margin_bottom
        for label_number in range(layout.num_y):
            for i in reversed(range(layout.num_x)):
                code = next(codes)
                if not code:
                    continue

                barcode = code['barcode']
                label1 = code.get('label1')

                # generate barcode images
                code128_path = path.join(d, barcode) + '.png'
                with open(code128_path, 'wb') as f:
                    f.write(get_pool_label(barcode))

                label = specimenlabel(layout=layout, img=code128_path, **code)

                renderPDF.draw(
                    drawing=label,
                    canvas=canvas,
                    x=layout.margin_left + i * (layout.label_width + layout.hspace),
                    y=ypos)

            ypos += layout.label_height + layout.vspace


def get_pdf(codes, layout, grid=False):
    """Return bytes encoding a pdf file including the barcodes in sequence
    'codes'; see fill_sheet() for details.

    This function provides a programmatic interface to generate labels
    outside of the context of the CLI. For example:

    from barcoder.commands.sheet import get_pdf
    from barcoder import layouts

    # mock up some codes
    codes = ({
        'barcode': 'D' + str(i).zfill(10),
        'label1': 'platelabel',
    } for i in range(1, 97))

    bytes = get_pdf(codes, layout=layouts.threecol)
    with open('sheet.pdf', 'wb') as f:
        f.write(bytes)
    """

    chunks = grouper(codes, layout.num_x * layout.num_y)
    with io.BytesIO() as f:
        canvas = Canvas(f, pagesize=layout.pagesize)
        for page_number, chunk in enumerate(chunks, 1):

            fill_sheet(canvas, chunk, layout=layout)

            if grid:
                draw_grid(canvas, layout=layout, include_vline=True)

            # add page number (bottom left)
            canvas.drawString(10, 20, str(page_number))

            # add package version
            canvas.drawString(30, 20, f'barcoder version {__version__}')

            # starts a new page
            canvas.showPage()

        canvas.save()
        f.seek(0)
        return f.read()


def build_parser(parser):
    parser.add_argument('-i', '--infile', type=argparse.FileType('r'),
                        help="""Input file in csv format with required
                        field "barcode" and optional fields "label1", ...""")
    parser.add_argument('-o', '--outfile', default='platelabels.pdf',
                        help='File name template [%(default)s]')
    parser.add_argument('-g', '--grid', help='draw grid',
                        action='store_true', default=False)


def action(args):
    outfile = Path(args.outfile)
    print(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)

    if args.infile:
        reader = csv.DictReader(args.infile)
        if 'barcode' not in reader.fieldnames:
            sys.exit('"barcode" is a required field in the input file')
        codes = list(reader)
    else:
        # for mocking up labels during development
        codes = ({
            'barcode': 'D-' + str(i).zfill(10),
            'label1': f'label1-{i}',
            'label2': f'label2-{i}',
            'label3': f'label3-{i}',
            'label4': f'label4-{i}',
        } for i in range(1, 97))

    with open(str(outfile), 'wb') as fobj:
        fobj.write(get_pdf(codes, layout=layouts.onecol, grid=args.grid))
