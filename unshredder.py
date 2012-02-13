from __future__ import print_function

import sys
import logging
from itertools import izip, permutations, product
from math import factorial
from pprint import pformat

from PIL import Image

LOGGER = logging.getLogger(__name__)
COLUMN_WIDTH = 32

# The maximum number of columns we can sensibly brute-force
COLUMN_LIMIT = 8


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
    
    from optparse import OptionParser
    
    parser = OptionParser(usage='%prog [options] infile outfile')
    parser.add_option('-v', '--verbose', action='store_true',
                      help='Show verbose logging')
    
    options, args = parser.parse_args()
    
    log_level = logging.DEBUG if options.verbose else logging.INFO
    logging.basicConfig(stream=sys.stderr, level=log_level)
    
    if len(args) != 2:
        parser.error('Two arguments required')
        sys.exit(1)
    
    infile, outfile = args
    
    input_image = Image.open(infile)
    try:
        columns = get_columns(input_image)
    except RuntimeError as e:
        print(infile, file=sys.stderr)
        sys.exit(1)
    
    diffs = {}
    for (a, col_a), (b, col_b) in product(enumerate(columns), enumerate(columns)):
        if a == b:
            continue
        diffs[a, b] = column_difference(col_a, col_b)
    
    LOGGER.debug(pformat(diffs))
    LOGGER.info('Min: %f' % min(diffs.values()))
    median = sorted(diffs.values())[len(diffs) // 2]
    LOGGER.info('Median: %f' % median)
    LOGGER.info('Max: %f' % max(diffs.values()))
    
    matches = diffs.items()
    
    # Sort the matches in ascending cost order
    matches.sort(key=lambda (pair, value): value)
    
    chains = []
    for new_item, value in matches:
        chained_columns = sum(chains, ())
        # The final number of chains we'll have to piece together
        unchained_columns = [(i,) for i in range(len(columns))
                             if i not in chained_columns]
        if len(chains) + len(unchained_columns) <= COLUMN_LIMIT:
            # We have few enough options left that we can brute-force them
            chains += unchained_columns
            LOGGER.debug('Proceeding to brute force')
            break
        
        # If the new pair shares columns with an existing chain, and they're
        # not in a position to join together, discard this match
        if any(new_item[0] in c[:-1] or new_item[1] in c[1:] for c in chains):
            LOGGER.info('Match %s includes already used '
                        'column: skipping' % (new_item,))
            continue
        
        before = [x for x in chains if x[-1] == new_item[0]]
        after = [x for x in chains if x[0] == new_item[-1]]
        # If this weren't the case, the previous loop would have continued
        assert len(before) in (0, 1)
        assert len(after) in (0, 1)
        if before:
            chains.remove(before[0])
            new_item = before[0][:-1] + new_item
        if after:
            chains.remove(after[0])
            new_item = new_item + after[0][1:]
        chains.append(new_item)
    
    LOGGER.debug(chains)
    total_count = factorial(len(chains))
    LOGGER.debug('Number of permutations: %d' % total_count)
    while len(chains) > COLUMN_LIMIT:
        LOGGER.debug('Too many chains to brute force')
        candidate = None  # left, right, cost
        for left, right in product(chains, chains):
            if left == right:
                continue
            cost = diffs[left[-1], right[0]]
            if candidate is None or candidate[2] > cost:
                candidate = (left, right, cost)
        LOGGER.debug('Joining chains %s and %s' % candidate[:2])
        chains.remove(candidate[0])
        chains.remove(candidate[1])
        chains.append(candidate[0] + candidate[1])
        
    best = None
    percentiles = [total_count // 100 * i for i in range(100)]
    for i, permutation in enumerate(permutations(chains)):
        if i in percentiles:
            LOGGER.debug('%d%% complete' % percentiles.index(i))
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
    
    image_out.save(open(outfile, mode='w'))
