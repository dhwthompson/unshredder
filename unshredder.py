from __future__ import print_function

import sys
import logging
from itertools import izip, permutations, product

from PIL import Image

LOGGER = logging.getLogger(__name__)
COLUMN_WIDTH = 32
GOOD_MATCH_THRESHOLD = 0.5


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
    
    left_slice, right_slice = (s.getdata() for s in [left_slice, right_slice])
    
    differences = []
    # Find the adjoining pixel of closest value and use that
    for i, left_pixel in enumerate(left_slice):
        # Pixel data objects don't support slicing, so have to do it this way
        pixel_range = range(max(0, i - 1), min(len(right_slice), i + 2))
        differences.append(min(pixel_difference(left_pixel, right_slice[r])
                               for r in pixel_range))
    
    return sum(differences)


if __name__ == '__main__':
    
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    
    if len(sys.argv) != 3:
        print('Usage: %s infile outfile' % sys.argv[0], file=sys.stderr)
        sys.exit(1)
    
    input_image = Image.open(sys.argv[1])
    try:
        columns = get_columns(input_image)
    except RuntimeError as e:
        print(e.args[0], file=sys.stderr)
        sys.exit(1)
    
    diffs = {}
    for (a, col_a), (b, col_b) in product(enumerate(columns), enumerate(columns)):
        if a == b:
            continue
        diffs[a, b] = column_difference(col_a, col_b)
    
    LOGGER.info('Min: %d' % min(diffs.values()))
    median = sorted(diffs.values())[len(diffs) // 2]
    LOGGER.info('Median: %d' % median)
    LOGGER.info('Max: %d' % max(diffs.values()))
    
    good_matches = set([pair for pair, value in diffs.items()
                       if float(value) / median < GOOD_MATCH_THRESHOLD])
    
    chains = []
    while good_matches:
        new_item = good_matches.pop()
        before = [x for x in chains if x[-1] == new_item[0]]
        after = [x for x in chains if x[0] == new_item[-1]]
        if len(before) > 2 or len(after) > 2:
            raise RuntimeError('Too many obvious matches')
        if before:
            chains.remove(before[0])
            new_item = before[0][:-1] + new_item
        if after:
            chains.remove(after[0])
            new_item = new_item + after[0][1:]
        chains.append(new_item)
    
    # Fill in any columns that aren't covered
    chained_columns = set(sum(chains, ()))
    chains = chains + [(i,) for i in range(len(columns))
                       if i not in chained_columns]
    LOGGER.debug(chains)
    best = None
    for i, permutation in enumerate(permutations(chains)):
        if not i % 1000:
            LOGGER.debug(i)
        cost = 0
        for (a, b) in izip(permutation, permutation[1:]):
            cost += diffs[a[-1], b[0]]
        if best is None or best[1] > cost:
            best = permutation, cost
    
    LOGGER.debug(best[0])
    ordering = sum(best[0], ())
    
    image_out = Image.new(input_image.mode, input_image.size)
    
    for i, column in enumerate(columns[x] for x in ordering):
        image_out.paste(column, (COLUMN_WIDTH * i, 0))
    
    image_out.save(open(sys.argv[2], mode='w'))
