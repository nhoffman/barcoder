import logging
import string
import secrets
import hashlib
import io

from reportlab.lib.pagesizes import letter

from barcode.writer import ImageWriter
import barcode
import qrcode

log = logging.getLogger(__name__)


def get_chunks(text, n):
    for i in range(0, len(text), n):
        yield text[i:i + n]


def get_code(length=16):
    """Return a string of the specified length composed of N - 1 random
    characters followed by the uppercased first character of the md5 checksum.

    """

    chars = [c for c in string.ascii_uppercase + string.digits
             if c not in {'I', '1', 'O', '0'}]

    text = ''.join(secrets.choice(chars) for i in range(length - 1))
    check_char = hashlib.md5(text.encode('utf-8')).hexdigest()[0].upper()

    return text + check_char


def get_qr(text):
    qr = qrcode.QRCode()
    qr.add_data(text)
    qr.make(fit=True)

    bc = qr.make_image(fill_color="black", back_color="white")
    with io.BytesIO() as f:
        bc.save(f)
        f.seek(0)
        return f.read()


def get_code128(text):

    # Sunquest expects a semicolon before the payload
    ean = barcode.get('code128', ';' + text, writer=ImageWriter())
    # print(ean.default_writer_options)
    options = {
        'module_height': 5,
        'text_distance': 1,
    }

    with io.BytesIO() as f:
        ean.write(f, options=options, text='-'.join(get_chunks(text, 4)))
        f.seek(0)
        return f.read()


def hline(p, y, pagesize=letter):
    """
    Draw a horizontal line at y given p = canvas.beginPath()
    """
    p.moveTo(0, y)
    p.lineTo(pagesize[0], y)


def vline(p, x, pagesize=letter):
    """
    Draw a vertical line at x given p = canvas.beginPath()
    """
    p.moveTo(x, 0)
    p.lineTo(x, pagesize[1])
