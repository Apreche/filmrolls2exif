import datetime
import fractions
import io
import math
import piexif
import piexif.helper
import pytz

from PIL import Image
from dateutil import parser as date_parser

def dd_to_dms(value):
    value = abs(value)
    decimals, number = math.modf(value)
    degrees = int(number)
    minutes = int(decimals * 60)
    seconds = (value - degrees - minutes / 60) * 3600.00

    degrees = (degrees, 1)
    minutes = (minutes, 1)
    seconds = (int(seconds * 10000), 10000)
    return (degrees, minutes, seconds)

def convert_gps(latitude, longitude):
    latitude = float(latitude)
    longitude = float(longitude)
    latituderef = 'N' if latitude >= 0 else 'S'
    longituderef = 'E' if longitude >=0 else 'W'
    dmslat = dd_to_dms(latitude)
    dmslong = dd_to_dms(longitude)
    return (latituderef, dmslat, longituderef, dmslong)

def convert_float_to_rational(float_str):
    rational = fractions.Fraction(float_str)
    return (rational.numerator, rational.denominator)

def convert_date(date_string):
    dt = date_parser.parse(date_string)
    nytz = pytz.timezone('America/New_York')
    local_dt = dt.replace(tzinfo=pytz.utc).astimezone(nytz)
    local_dt = nytz.normalize(local_dt)
    return local_dt.strftime("%Y:%m:%d %H:%M:%S")

def get_thumbnail(filename):
    # Create Thumbnail
    thumb_io = io.BytesIO()
    thumb = Image.open(filename)
    thumb.thumbnail((50, 50), Image.ANTIALIAS)
    thumb.save(thumb_io, "jpeg")
    return thumb_io.getvalue()

def apply_metadata(filename, roll, frame):
    data = piexif.load(filename)

    zeroth_ifd = {
        piexif.ImageIFD.Model: roll['camera'],
        piexif.ImageIFD.Software: "piexif",
    }

    exif_ifd = {
        piexif.ExifIFD.ISOSpeedRatings: int(roll['speed']),
        piexif.ExifIFD.LensModel: frame['lens'],
        piexif.ExifIFD.FNumber: convert_float_to_rational(frame['aperture']),
        piexif.ExifIFD.DateTimeOriginal: convert_date(frame['date']),
    }

    if frame['note']:
        comment = piexif.helper.UserComment.dump(frame['note'])
        exif_ifd.update({
            piexif.ExifIFD.UserComment: comment,
        })

    if frame['shutterSpeed'] != 'Av':
        exif_ifd.update({
            piexif.ExifIFD.ExposureTime: convert_float_to_rational(frame['shutterSpeed']),
        })

    gps = convert_gps(frame['latitude'], frame['longitude'])

    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: gps[0],
        piexif.GPSIFD.GPSLatitude: gps[1],
        piexif.GPSIFD.GPSLongitudeRef: gps[2],
        piexif.GPSIFD.GPSLongitude: gps[3],
    }

    first_ifd = {
        piexif.ImageIFD.Software: "piexif",
    }


    thumbnail = get_thumbnail(filename)

    exif_dict = {
        '0th': zeroth_ifd,
        'Exif': exif_ifd,
        'GPS': gps_ifd,
        '1st': first_ifd,
        # 'thumbnail': thumbnail,
    }

    exif_bytes = piexif.dump(exif_dict)
    original = Image.open(filename)
    original.save(filename, exif=exif_bytes)
