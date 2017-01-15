'''Author: Chandra Krintz, UCSB, ckrintz@cs.ucsb.edu, AppScale BSD license

   USAGE: python box.py BOX_SECRET BOX_CLIENT BOX_APPNAME PREFIX PREFIX_BOXID BOX_FILEID
   python box.py "..." "..." "..." "Windmill Canyon 1" "5802215677" "95599079123"

   The program performs the Oauth2 handshake to have the user retrieve the code.
   It stores the access and refresh token in a file using json for future use.
   It will not re-perform the handshake if such a file exists.
   It will refresh the tokens if the access expires using its refresh token.

   The program retrieves box file BOX_FILEID as a thumbnail file 
   from box.com through the app using oauth2 tokens, and stores it in thumbnail.png 
   in the current working directory.

   required: exifread, boxsdk
'''

import random,argparse,json,os,sys,time,exifread,cv2
from datetime import datetime, timedelta
from contextlib import contextmanager #for timeblock
from boxsdk import Client, OAuth2
from boxsdk.exception import BoxOAuthException
import oauth2_cli_util

DEBUG = False
######################## timer utility ############################
@contextmanager
def timeblock(label): 
    start = time.time() #time.process_time() available in python 3
    try:
        yield
    finally:
        end = time.time()
        print ('{0} : {1:.10f} secs'.format(label, end - start))

############## main #################
def main():
    global DEBUG
    parser = argparse.ArgumentParser(description='Download a file as a thumbnail from box with metadata')
    parser.add_argument('sec',action='store',help='Box Secret')
    parser.add_argument('cli',action='store',help='Box Client')
    parser.add_argument('app',action='store',help='Box App Name')

    parser.add_argument('prefix',action='store',help='Prefix string')
    parser.add_argument('prefix_id',action='store',help='Prefix ID in Box')
    parser.add_argument('fid',action='store',help='File ID in Box')
    args = parser.parse_args()

    prefix_list=[(args.prefix,args.prefix_id)]
    client=args.cli
    secret=args.sec
    fid=args.fid
    app = args.app

    #setup OAuth2
    #make sure that this is one of the redirect URIs in the oauth setup on box app
    redir_uri='http://localhost'
    oauth2_cli_util.setupStorage(app,client,redir_uri)
    tok,ref = oauth2_cli_util.getTokens()
    if DEBUG:
        print 'Initial Access Token is: {0}'.format(tok)
    if tok is None:
        print 'box:main, tok is None, calling setup'
        ucsbauth = oauth2_cli_util.setupOAuth2(
            auth='https://app.box.com/api/oauth2/authorize',
            token='https://app.box.com/api/oauth2/token',
            redir=redir_uri,
            client=client,
            secret=secret,
            app=app,
        )
        if ucsbauth is None:
            print 'Error: unable to authenticate and authorize'
            sys.exit(1)
        tok,ref = oauth2_cli_util.getTokens()
        if tok is None:
            print 'Unknown Error'
            sys.exit(1)

    #for testing - this will cause refresh of the token if needed
    #print oauth2_cli_util.query('https://api.box.com/2.0/users/me')

    res = oauth2_cli_util.get_thumbnail(fid)
    print 'Return Message: {0}'.format(res)


if __name__ == "__main__":
        main()
