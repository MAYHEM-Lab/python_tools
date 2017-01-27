'''Author: Chandra Krintz, UCSB, ckrintz@cs.ucsb.edu, AppScale BSD license

   USAGE: python downloadDir.py BOX_SECRET BOX_CLIENT BOX_APPNAME BOX_FOLDERID local_dirname
   python box.py sec cli app 11396690300 ./mydir

   The program retrieves box files recursively under BOX_FOLDERID and stores them 
   in local_dirname (which must exist)

   required: boxsdk
'''

import argparse,json,os,sys,time
from contextlib import contextmanager #for timeblock
from boxsdk import Client, OAuth2
from boxsdk.exception import BoxOAuthException
import oauth2_cli

DEBUG = False

############## main #################
def main():
    global DEBUG
    parser = argparse.ArgumentParser(description='Download a files from box folder into local dir')
    parser.add_argument('sec',action='store',help='Box Secret')
    parser.add_argument('cli',action='store',help='Box Client')
    parser.add_argument('app',action='store',help='Box App Name')

    parser.add_argument('did',action='store',help='Directory ID in Box')
    parser.add_argument('localdir',action='store',help='Local directory in which to store files')
    args = parser.parse_args()

    client=args.cli
    secret=args.sec
    ldir=args.localdir
    did=args.did
    app = args.app

    #acquire OAuth2 tokens and store them if generated, refresh if expired
    #make sure that this is one of the redirect URIs in the oauth setup on box app
    redir_uri='http://localhost'
    token_uri='https://app.box.com/api/oauth2/token'
    oauth2_cli.initialize(client,secret,redir_uri,token_uri)

    res = oauth2_cli.download(did,ldir)
    print 'Return Message: {0}'.format(res)


if __name__ == "__main__":
        main()
