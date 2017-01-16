'''Author: Chandra Krintz, UCSB, ckrintz@cs.ucsb.edu, AppScale BSD license

   USAGE: python downloadDir.py BOX_SECRET BOX_CLIENT BOX_APPNAME BOX_DIRID
   python box.py "..." "..." "..." "11396690300"

   The program performs the Oauth2 handshake to have the user retrieve the code.
   It stores the access and refresh token in a file using json for future use.
   It will not re-perform the handshake if such a file exists.
   It will refresh the tokens if the access expires using its refresh token.

   The program retrieves box folder BOX_DIRID and downloads the hierarchy
   from box.com through the app using oauth2 tokens, and stores it in thumbnail.png 
   into the current working directory (recursively -- so everything below BOX_DIRID

   required: boxsdk
'''

import argparse,json,os,sys,time,exifread,cv2
from datetime import datetime, timedelta
from boxsdk import Client, OAuth2
from boxsdk.exception import BoxOAuthException
import oauth2_cli_util
from oauth2client.client import flow_from_clientsecrets


DEBUG = False

############## main #################
def main():
    global DEBUG
    parser = argparse.ArgumentParser(description='Download a directory structure from box with metadata')
    parser.add_argument('sec',action='store',help='Box Secret')
    parser.add_argument('cli',action='store',help='Box Client')
    parser.add_argument('app',action='store',help='Box App Name')

    parser.add_argument('fid',action='store',help='Folder ID in Box')
    args = parser.parse_args()

    client=args.cli
    secret=args.sec
    fid=args.fid
    app = args.app

    #acquire OAuth2 tokens and store them if generated, refresh if expired; get box handle
    #make sure that this is one of the redirect URIs in the oauth setup on box app
    redir_uri='http://localhost'
    auth_uri='https://app.box.com/api/oauth2/authorize',
    token_uri='https://app.box.com/api/oauth2/token',
    #oauth2_cli_util.setupStorage(client,secret,redir_uri,token_uri)
    #boxclient = oauth2_cli_util.setupClient()
    oauth2_cli_util.initialize(client,secret,redir_uri,token_uri) #stores box Client object

    #print 'testing access via tokens'
    #oauth2_cli_util.get_thumbnail('95623144310')
    print 'testing access via box client'
    oauth2_cli_util.get_file_using_boxclient('95623144310')

    sys.exit(1)
    

    ucsbauth = None
    auth_uri='https://app.box.com/api/oauth2/authorize',
    token_uri='https://app.box.com/api/oauth2/token',
    oauth2_cli_util.setupStorage(app,client,redir_uri)
    #creds = oauth2_cli_util.getTokens()
    tok,ref = creds['access_token'],creds['refresh_token']
    if DEBUG:
        print 'Initial Access Token is: {0}'.format(tok)
    if tok is None:
        print 'box:main, tok is None, calling setup'
        ucsbauth = oauth2_cli_util.setupOAuth2(
            auth=auth_uri,
            token=token_uri,
            redir=redir_uri,
            client=client,
            secret=secret,
            app=app,
        )
        if ucsbauth is None:
            print 'Error: unable to authenticate and authorize'
            sys.exit(1)
        #tok,ref = oauth2_cli_util.getTokens()
        if tok is None:
            print 'Unknown Error'
            sys.exit(1)

    #this will cause refresh of the token if needed
    print '**************** Testing Tokens *********************'
    print oauth2_cli_util.query('https://api.box.com/2.0/users/me')
    print '**************** Testing Tokens Completed *********************\n'
  
    #create an oauth2 flow from client secrets
    #fname = oauth2_cli_util.getJSONSecrets(redir_uri,auth_uri)
    #ucsbauth = flow_from_clientsecrets(fname, scope='', redirect_uri=redir_uri)
    #os.remove(fname)
    ucsbauth = oauth2_cli_util.auth()

    if ucsbauth is not None:
        print ucsbauth.__dict__
        client = Client(ucsbauth)
        f = oauth2_cli_util.get_folder_using_boxclient(client,fid)
    else:
	print 'ERROR: Flow creation failed!'


if __name__ == "__main__":
        main()
