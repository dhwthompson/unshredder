"""Taken (almost) directly from http://instagram-engineering.tumblr.com/post/12651721845/instagram-engineering-challenge-the-unshredder"""

import sys

from PIL import Image
from random import shuffle

SHREDS = 20
image = Image.open(sys.argv[1])
shredded = Image.new("RGBA", image.size)
width, height = image.size
shred_width = width/SHREDS
sequence = range(0, SHREDS)
shuffle(sequence)

for i, shred_index in enumerate(sequence):
    shred_x1, shred_y1 = shred_width * shred_index, 0
    shred_x2, shred_y2 = shred_x1 + shred_width, height
    region =image.crop((shred_x1, shred_y1, shred_x2, shred_y2))
    shredded.paste(region, (shred_width * i, 0))

shredded.save(sys.argv[2])