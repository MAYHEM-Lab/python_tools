'''Author: Chandra Krintz, UCSB, ckrintz@cs.ucsb.edu, AppScale BSD license

   USAGE: python myexif.py file.jpg

   The program extracts and prints out the exif data.
'''

import argparse,os,sys,time,exifread
from datetime import datetime, timedelta
from contextlib import contextmanager #for timeblock
from PIL import Image, ExifTags
import pyexifinfo as pyexif


tag_name_to_id = dict([ (v, k) for k, v in ExifTags.TAGS.items() ])
tag_name_to_id[270] = 'ImageDescription'
tag_name_to_id[306] = 'DateTime'
tag_name_to_id[256] = 'ImageWidth'
tag_name_to_id[257] = 'ImageLength'
tag_name_to_id[258] = 'BitsPerSample'
tag_name_to_id[40962] = 'PixelXDimension'
tag_name_to_id[40963] = 'PixelYDimension'
tag_name_to_id[305] = 'Software'
tag_name_to_id[37510] = 'UserComment'
tag_name_to_id[40091] = 'XPTitle'
tag_name_to_id[40092] = 'XPComment'
tag_name_to_id[40093] = 'XPAuthor'
tag_name_to_id[40094] = 'XPKeywords'
tag_name_to_id[40095] = 'XPSubject'
tag_name_to_id[40961] = 'ColorSpace' # Bit depth
tag_name_to_id[315] = 'Artist'
tag_name_to_id[33432] = 'Copyright'

DEBUG = False

def convert_exif_to_dict(exifin):
    '''
    This helper function converts the dictionary keys from
    IDs to strings so your code is easier to read.
    '''
    data = {}
    if exifin is None:
        return data
    for k,v in exifin.items():
        if k in tag_name_to_id:
            data[tag_name_to_id[k]] = v
    else:
            data[k] = v
    # These fields are in UCS2/UTF-16, convert to something usable within python
    for k in ['XPTitle', 'XPComment', 'XPAuthor', 'XPKeywords', 'XPSubject']:
        if k in data:
            data[k] = data[k].decode('utf-16').rstrip('\x00')
    return data



############## main #################
def main():
    global DEBUG
    parser = argparse.ArgumentParser(description='Download a file as a thumbnail from box')
    parser.add_argument('fname',action='store',help='JPG file name')
    args = parser.parse_args()

    fname=args.fname

    f = open(fname, 'rb')
    tags = exifread.process_file(f)

    print 'EXIFREAD'
    print tags
    #for tag in tags:
        #print '{0}:{1}'.format(tag,tags[tag])
    
    print 'PIL'
    img = Image.open(fname)
    #print img.__dict__
    #tags = img._getexif()
    #print tags
    #for tag in tags:
        #print '{0}:{1}'.format(tag,tags[tag])

    img.verify()
    print img.format
    if img.format in ['JPEG', 'JPG', 'TIFF']:
        ex = img._getexif()
        print 'ex: {0}'.format(ex)
        exif1 = convert_exif_to_dict(ex)
        #if exif is not None:
            #print exif['DateTime']
        print exif1
    print img.info


    exif_json = pyexif.get_json(fname)
    print exif_json

if __name__ == "__main__":
        main()
