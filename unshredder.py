from __future__ import print_function

import sys
import logging
from itertools import product

from PIL import Image

LOGGER = logging.getLogger(__name__)
COLUMN_WIDTH = 32


def get_columns(input_image):
    image_width = input_image.size[0]
    if image_width % COLUMN_WIDTH:
        error = 'Image width (%d) does not divide into %d-pixel columns' % \
                (image_width, COLUMN_WIDTH)
        raise RuntimeError(error)
    
    column_count = image_width // COLUMN_WIDTH
    LOGGER.info('Image has %d columns' % column_count)
    
    column_boxen = [(i * COLUMN_WIDTH, 0,
                     (i + 1) * COLUMN_WIDTH, input_image.size[1])
                    for i in xrange(column_count)]
    
    return map(input_image.crop, column_boxen)


def pixel_difference(a, b):
    # Ignore the alpha component for now
    return sum(abs(x[0] - x[1]) for x in zip(a[0:3], b[0:3]))


def column_difference(left, right):
    
    left_slice = left.crop((left.size[0] - 1, 0, left.size[0], left.size[1]))
    right_slice = right.crop((0, 0, 1, right.size[1]))
    
    return sum(pixel_difference(a, b) for a, b in
               zip(left_slice.getdata(), right_slice.getdata()))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: %s inputfile' % sys.argv[0], file=sys.stderr)
        sys.exit(1)
    
    input_image = Image.open(sys.argv[1])
    try:
        columns = get_columns(input_image)
    except RuntimeError as e:
        print(e.args[0], file=sys.stderr)
        sys.exit(1)
    
    diffs = {}
    for (a, col_a), (b, col_b) in product(enumerate(columns), enumerate(columns)):
        diffs[a, b] = column_difference(col_a, col_b)
    
    print(diffs)
    print('Min: %d' % min(diffs.values()))
    median = sorted(diffs.values())[len(diffs) // 2]
    print('Median: %d' % median)
    print('Max: %d' % max(diffs.values()))
    
    print(list(pair for pair, value in diffs.items()
               if float(value) / median < 0.4))
