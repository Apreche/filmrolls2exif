#!/usr/bin/env python

import exif
import ipdb
import os
import re

from xml.etree import ElementTree


ROLL_FIELDS = [
    'title',
    'speed',
    'camera',
    'load',
    'unload',
    'note',
]

FRAME_FIELDS = [
    'lens',
    'aperture',
    'shutterSpeed',
    'compensation',
    'accessory',
    'number',
    'date',
    'latitude',
    'longitude',
    'note',
]

def load_tree(xml_filename="data/export.xml"):
    # Load XML tree, remove pesky namespace
    with open(xml_filename, 'r') as xmlfile:
        xmlstring = xmlfile.read()
    xmlstring = re.sub(' xmlns="[^"]+"', '', xmlstring, count=1)
    return ElementTree.fromstring(xmlstring)

def get_frames(raw_roll):
    # Extract frame data from roll data
    frames = []
    raw_frames = raw_roll.find('frames').findall('frame')
    for raw_frame in raw_frames:
        frame = {}
        for field in FRAME_FIELDS:
            frame[field] = raw_frame.find(field).text
        frames.append(frame)
    return frames

def get_rolls(xmltree):
    # Extract roll data from xml tree
    rolls = []
    raw_rolls = xmltree.find('filmRolls').findall('filmRoll')
    for raw_roll in raw_rolls:
        roll = {}
        for field in ROLL_FIELDS:
            roll[field] = raw_roll.find(field).text
        roll['frames'] = get_frames(raw_roll)
        rolls.append(roll)
    return rolls

def roll_choice(rolls):
    # Make user choose which roll they want to use
    for index, roll in enumerate(rolls):
        print("{}: {} - {}".format(
            index,
            roll['title'],
            len(roll['frames'])
        ))

    index = input()
    return rolls[int(index)]

def update_images(directory, roll):
    # apply metadata from roll to images in directory
    image_files = []
    for (dirpath, dirnames, filenames) in os.walk(directory):
        image_files.extend(filenames)
        image_files = ["{}{}".format(dirpath, filename) for filename in filenames]
        image_files = list(filter(lambda x: x[-4:].lower() == '.jpg', image_files))
    for filename, frame in  list(zip(image_files, roll['frames'])):
        exif.apply_metadata(filename, roll, frame)

def main():
    tree = load_tree()
    rolls = get_rolls(tree)
    roll = roll_choice(rolls)
    directory = input('Path to image directory: ')
    update_images(directory, roll)

if __name__ == "__main__":
    main()
