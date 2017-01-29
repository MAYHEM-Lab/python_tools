'''Author: Chandra Krintz, UCSB, ckrintz@cs.ucsb.edu, AppScale BSD license
   required: python2.7
   USAGE: python create_zooniverse_manifest.py filelist.txt 
   filelist.txt must contain the filename (one per line)
'''

import argparse,json,os,sys,time,exifread
from contextlib import contextmanager #for timeblock

DEBUG = False

############## main #################
def main():
    global DEBUG
    parser = argparse.ArgumentParser(description='Parse a filelist.txt file produced by parse_file_list.py without the csv option and create a zooniverse manifest (csv) from it.')
    #required args
    parser.add_argument('fname',action='store',help='input filename')
    parser.add_argument('fname_out',action='store',help='output filename')
    #optional args
    #parser.add_argument('--printcsv',action='store_true',default=False,help='Generate a CSV file of the map')
    args = parser.parse_args()

    '''subject_id,image_name_1,origin,link,attribution,license,#secret_description
       1,Figueroa_2013-12-01_08:02:00_681.jpg,Sedwick Figueroa Camera Trap,http://169.231.235.52/static/sedgwick/2013/12/Figueroa_2013-12-01_08:02:00_681.jpg,UCSB Sedgwick Reserve,BSD,Figueroa Camera Trap
    '''
    fname=args.fname
    fname_out=args.fname_out
    count = 1
    with open(fname_out, 'wb') as fout:
        fout.write('subject_id,image_name_1,origin,link,attribution,license,#secret_description\n')

        with open(fname, 'rb') as fin:
	    for fi in fin:
                newfname = fi.strip()
                if newfname.endswith('.JPG'):
                    newfname = newfname.replace('.JPG','.jpg')
 		fout.write('{0},{1},Sedgwick Main Road Camera Trap,http://169.231.235.52/static/sr/zooniverse/{1},UCSB Sedgwick Reserve,BSD,Main Road Camera Trap\n'.format(count,newfname))
                count += 1

if __name__ == "__main__":
        main()
