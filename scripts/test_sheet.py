#!/usr/bin/env python3

from barcoder.commands.sheet import get_pdf
from barcoder import layouts

# mock up some codes
codes = ({
    'barcode': 'D-' + str(i).zfill(10),
    'label1': f'label1-{i}',
    'label2': f'label2-{i}',
    'label3': f'label3-{i}',
    'label4': f'label4-{i}',
} for i in range(1, 97))

bytes = get_pdf(codes, layout=layouts.onecol, grid=True)
with open('sheet.pdf', 'wb') as f:
    f.write(bytes)

print('sheet.pdf')
