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


ALPHANUM_CHARS = [c for c in string.ascii_uppercase + string.digits
                  if c not in {'I', '1', 'O', '0'}]
NUM_CHARS = [c for c in string.digits if c not in {'1', '0'}]


def get_chunks(text, n):
    for i in range(0, len(text), n):
        yield text[i:i + n]


def get_code(length, alphanum_chars=ALPHANUM_CHARS, num_chars=NUM_CHARS):
    """Return a string of the specified length composed of N - 1 random
    characters followed by the uppercased first character of the md5
    checksum. The first position is always numeric.

    """

    text = secrets.choice(num_chars)
    text += ''.join(secrets.choice(alphanum_chars) for i in range(length - 2))
    check_char = hashlib.md5(text.encode('utf-8')).hexdigest()[0].upper()
    return text + check_char


def generate_codes(length, already_seen=None, stop_if_seen=False):
    already_seen = already_seen or set()

    while True:
        code = get_code(length)
        if code in already_seen:
            msg = f'code {code} has already been seen'
            log.warning(msg)
            if stop_if_seen:
                raise ValueError(msg)
        else:
            already_seen.add(code)
            yield code


def generate_fake_codes(length, chars=None):

    allchars = [c for c in string.ascii_uppercase + string.digits
                if c not in {'I', '1', 'O', '0'}]
    basechars = chars or allchars

    for char in basechars:
        basestr = char * (length - 2)
        for penultimate in allchars:
            allbutlast = basestr + penultimate
            code = allbutlast + hashlib.md5(allbutlast.encode('utf-8')).hexdigest()[0].upper()
            yield code


def get_qr(text, **kwargs):
    """Return bytes representing a QR code image. kwargs can be used to
    provide parameters to qrcode.QRCode() constructor.

    """
    qr = qrcode.QRCode(**kwargs)
    qr.add_data(text)
    qr.make(fit=True)

    bc = qr.make_image(fill_color="black", back_color="white")
    with io.BytesIO() as f:
        bc.save(f)
        f.seek(0)
        return f.read()


def get_code128(text, add_semicolon=False):
    ean = barcode.get(
        'code128',
        ';' + text if add_semicolon else text,
        writer=ImageWriter())

    # print(ean.default_writer_options)
    options = {
        'module_height': 5,
        'text_distance': 1,
    }

    with io.BytesIO() as f:
        ean.write(f, options=options, text='-'.join(get_chunks(text, 4)))
        f.seek(0)
        return f.read()


def get_pool_label(text):

    options = {
        'module_height': 5,
        'text_distance': 1,
    }

    ean = barcode.get('code128', text.replace('-', ''), writer=ImageWriter())
    with io.BytesIO() as f:
        ean.write(f, options=options, text=text)
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
