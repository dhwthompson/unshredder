from __future__ import print_function

import sys
from functools import partial

from PIL import Image

print_stderr = partial(print, file=sys.stderr)


COLUMN_WIDTH = 32

if len(sys.argv) != 2:
    print_stderr('Usage: %s inputfile' % sys.argv[0])
    sys.exit(1)

input_image = Image.open(sys.argv[1])

image_width = input_image.size[0]
if image_width % COLUMN_WIDTH:
    print_stderr('Image width (%d) does not divide into %d-pixel columns' %
                 (image_width, COLUMN_WIDTH))
    sys.exit(1)

column_count = image_width // COLUMN_WIDTH
print_stderr('Image has %d columns' % column_count)

column_boxen = [(i * COLUMN_WIDTH, 0,
                 (i + 1) * COLUMN_WIDTH - 1, input_image.size[1])
                for i in xrange(column_count)]

columns = map(input_image.crop, column_boxen)
