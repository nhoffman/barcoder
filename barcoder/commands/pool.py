"""Labels for pooled specimens using 4x20 label stock (Avery 94203)
"""

# https://gist.github.com/lkrone/04ca0e3ae3a78f434e5ac84cfd9ca6b1
# https://programtalk.com/vs2/python/8113/ReportLab/tests/test_graphics_images.py/

import logging
import tempfile
from os import path
from datetime import datetime
import sys
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Image
from reportlab.graphics import renderPDF
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch

from barcoder import layouts, __version__
from barcoder.utils import get_pool_label, draw_grid

log = logging.getLogger(__name__)


VERSION = 2


def generate_codes(timestamp, batch, hexlen=4):
    for i in range(int('0x' + 'f' * hexlen, base=16)):
        h = hex(i)[2:].upper().zfill(hexlen)
        yield f'P{timestamp}-{batch}-{h}'


def specimenlabel(layout, code, img):
    label_drawing = Drawing(layout.label_width, layout.label_height)

    bc_width = 1.75 * inch
    bc_height = 0.4 * inch
    barcode = Image(x=0, y=0, width=bc_width, height=bc_height, path=img)
    label_drawing.add(barcode)
    return label_drawing


def fill_sheet(canvas, codes, layout, timestamp, page_number, fake_code=None):

    # consume enough codes to fill the page and reverse the order
    revcodes = iter(reversed([next(codes) for i in range(layout.num_x * layout.num_y)]))

    with tempfile.TemporaryDirectory() as d:
        # start at the bottom of the page
        ypos = layout.margin_bottom
        for label_number in range(layout.num_y):
            for i in reversed(range(layout.num_x)):
                code = fake_code or next(revcodes)

                # generate barcode images
                code128_path = path.join(d, code) + '-code128.png'
                with open(code128_path, 'wb') as f:
                    f.write(get_pool_label(code))

                label = specimenlabel(layout, code, code128_path)
                renderPDF.draw(
                    drawing=label,
                    canvas=canvas,
                    x=layout.margin_left + i * (layout.label_width + layout.hspace),
                    y=ypos)

            ypos += layout.label_height + layout.vspace


def build_parser(parser):

    parser.add_argument('-o', '--outfile',
                        default='pool-labels-{timestamp}-{fileno:03d}-n{npages}.pdf',
                        help='File name template [%(default)s]')
    parser.add_argument('-d', '--dirname', default='.',
                        help='directory for output [%(default)s]')
    parser.add_argument('-t', '--timestamp', default=datetime.now().strftime('%y%j')[1:],
                        help='[default %(default)s]')
    parser.add_argument('-p', '--npages', default=25, type=int,
                        help='number of pages, max 99 [default %(default)s]')
    parser.add_argument('-f', '--nfiles', default=99, type=int, help='[default %(default)s]')
    parser.add_argument('--grid', help='draw grid',
                        action='store_true', default=False)
    parser.add_argument('--fake-code', help='fill sheet with this fake code')


def action(args):
    layout = layouts.pool

    if args.npages > 99:
        sys.exit('The maximum number of pages is 99')

    if args.nfiles > 99:
        sys.exit('The maximum number of files is 99')

    outdir = Path(args.dirname)
    outdir.mkdir(parents=True, exist_ok=True)

    for fileno in range(1, args.nfiles + 1):
        codes = generate_codes(args.timestamp, f'{fileno:02}')

        outfile = outdir / args.outfile.format(
            timestamp=args.timestamp,
            fileno=fileno,
            npages=args.npages
        )

        print(outfile)

        canvas = Canvas(str(outfile), pagesize=layout.pagesize)
        for page_number in range(args.npages):
            fill_sheet(canvas, codes, layout=layout, page_number=page_number + 1,
                       timestamp=args.timestamp, fake_code=args.fake_code)
            if args.grid:
                draw_grid(canvas, layout=layout, include_vline=True)

            # add page number (bottom left)
            canvas.drawString(10, 20, str(page_number + 1))

            # add package version
            canvas.drawString(30, 20, f'barcoder version {__version__}')

            # starts a new page
            canvas.showPage()

        canvas.save()
