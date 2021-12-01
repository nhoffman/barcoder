from collections import namedtuple

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

Layout = namedtuple('Layout', ['pagesize', 'label_height', 'label_width',
                               'num_x', 'num_y',
                               'margin_left', 'margin_bottom',
                               'vspace', 'hspace'])

# Three column format (1' x 2.5'): https://www.avery.com/blank/labels/94221
threecol = Layout(pagesize=letter, label_height=1 * inch, label_width=(2 + 5 / 8) * inch,
                  num_x=3, num_y=10,
                  margin_left=(3 / 16) * inch, margin_bottom=0.5 * inch,
                  vspace=0, hspace=(1 / 8) * inch)

# Two column format (1 1/3' x 4'): https://www.avery.com/templates/5162
# (layout not defined in this format for two column labels)

# Pool labels using 4 x 20 stock: https://www.avery.com/templates/94203
pool = Layout(pagesize=letter,
              label_height=0.5 * inch,
              label_width=1.75 * inch,
              num_x=4, num_y=20,
              margin_left=(1 / 4) * inch,
              margin_bottom=(17 / 32) * inch,
              vspace=0 * inch,
              hspace=(9 / 32) * inch)

# one column format for plain paper
onecol = Layout(pagesize=letter,
                  label_height=0.8 * inch,
                  label_width=(2 + 5 / 8) * inch,
                  num_x=1, num_y=12,
                  margin_left=1.0 * inch,
                  margin_bottom=1.0 * inch,
                  vspace=0 * inch,
                  hspace=0 * inch)
