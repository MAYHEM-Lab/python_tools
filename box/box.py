'''Author: Chandra Krintz, UCSB, ckrintz@cs.ucsb.edu, AppScale BSD license

   USAGE: python box.py BOX_SECRET BOX_CLIENT BOX_APPNAME BOX_FILEID
   python box.py "..." "..." "..." "95599079123"

   The program performs the Oauth2 handshake to have the user retrieve the code.
   It stores the access and refresh token in a file using json for future use.
   It will not re-perform the handshake if such a file exists.
   It will refresh the tokens if the access expires using its refresh token.

   The program retrieves box file BOX_FILEID as a thumbnail file 
   from box.com through the app using oauth2 tokens, and stores it in thumbnail.png 
   in the current working directory.

   required: boxsdk
'''

import argparse,json,os,sys,time
from contextlib import contextmanager #for timeblock
from boxsdk import Client, OAuth2
from boxsdk.exception import BoxOAuthException
import oauth2_cli
import oauth2_cli_util

DEBUG = False

############## main #################
def main():
    global DEBUG
    parser = argparse.ArgumentParser(description='Download a file as a thumbnail from box')
    parser.add_argument('sec',action='store',help='Box Secret')
    parser.add_argument('cli',action='store',help='Box Client')
    parser.add_argument('app',action='store',help='Box App Name')

    parser.add_argument('fid',action='store',help='File ID in Box')
    args = parser.parse_args()

    client=args.cli
    secret=args.sec
    fid=args.fid
    app = args.app

    #acquire OAuth2 tokens and store them if generated, refresh if expired
    #make sure that this is one of the redirect URIs in the oauth setup on box app
    redir_uri='http://localhost'
    token_uri='https://app.box.com/api/oauth2/token'
    auth_uri='https://app.box.com/api/oauth2/authorize',
    oauth2_cli.initialize(client,secret,redir_uri,token_uri)
    res = oauth2_cli.get_thumbnail(fid) #uses requests not auth client

    sys.exit(1)

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

    res = oauth2_cli_util.get_thumbnail(fid) #uses requests not auth client
    print 'Return Message: {0}'.format(res)


if __name__ == "__main__":
        main()
