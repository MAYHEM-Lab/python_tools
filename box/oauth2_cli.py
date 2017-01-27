'''Author: Chandra Krintz, UCSB, ckrintz@cs.ucsb.edu, AppScale BSD license
   USAGE: import oauth2_cli
'''

import json, traceback, requests, sys, argparse, os, exifread
from datetime import datetime, timedelta
#from urllib import urlencode
from contextlib import contextmanager #for timeblock
from boxsdk import OAuth2
from boxsdk import Client
from boxsdk.network.default_network import DefaultNetwork
import boxsdk.exception 
import boxsdk.exception 
import piexif
from pprint import pformat
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

DEBUG = True
TEST_REFRESH = False #set this to True to test that refresh works
#this is set in intialize_storage which must be run before all else, app entry is /
clientID = 'YYY'
secret = 'ZZZ'
redir_uri = None
token_uri = None
boxClient = None

#You will also need a box login and password, and have added an app in box
#to obtain the client/secret above and to set/get the redirect url

########## Logging Network Class ###################
class LoggingNetwork(DefaultNetwork):
    #from http://opensource.box.com/box-python-sdk/tutorials/intro.html
    def request(self, method, url, access_token, **kwargs):
        """ Base class override. Pretty-prints outgoing requests and incoming responses. """
        print '\x1b[36m{} {} {}\x1b[0m'.format(method, url, pformat(kwargs))
        response = super(LoggingNetwork, self).request(
            method, url, access_token, **kwargs
        )
        if response.ok:
            print '\x1b[32m{}\x1b[0m'.format(response.content)
        else:
            print '\x1b[31m{}\n{}\n{}\x1b[0m'.format(
                response.status_code,
                response.headers,
                pformat(response.content),
            )
        return response


######################## timer utility ############################
@contextmanager
def timeblock(label): 
    start = time.time() #time.process_time() available in python 3
    try:
        yield
    finally:
        end = time.time()
        print ('{0} : {1:.10f} secs'.format(label, end - start))

################ pretty print POST (debugging)  ##################
def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\n{}\n\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))

########## oauthFromSecret() ###################
def oauthFromSecret(cli,sec):
    if DEBUG: 
        print 'in oauthFromSecret()'
    #create oauth from client, secret
    print 'creating oauth object from client and secret'
    oauth = OAuth2(
        client_id=cli,
        client_secret=sec,
        store_tokens=writeTokens,
    )
    auth_url, csrf_token = oauth.get_authorization_url(redir_uri)
    print 'Cut/Paste this URI into the URL box in \
        \na browser window and press enter:\n\n{0}\n'.format(auth_url)
    print 'You should login and authorize use of your account by this app'
    print 'You will then ultimately be redirected to a URL and a page \
        that says "Connection Refused"'
    auth_code = raw_input('Type in the code that appears after \
        "code="\nin the URL box in your browser window, and press enter: ')
    #csrf_returned = raw_input('Type in the csrf in the URI: ')
    #assert csrf_returned == csrf_token
    access_token, refresh_token = oauth.authenticate(auth_code)
    return oauth

########## oauthFromTokens() ###################
def oauthFromTokens(acc,ref,cli,sec):
    #get oauth object from tokens
    oauth = None
    if DEBUG: 
        print 'in oauth2_cli:oauthFromTokens()'
    try:
        oauth = OAuth2(
            client_id=cli,
            client_secret=sec,
            access_token=acc,
            refresh_token=ref,
            store_tokens=writeTokens,
        )
    except Exception as e:  
	print 'Exception in auth(...): {0}'.format(e)
        oauth = None

    if oauth is None:
	print 'oauth is None, calling create from secret'
        return oauthFromSecret(cli,sec)

    return oauth

########## auth() ###################
def auth(cli,sec):
    if DEBUG: 
        print 'in auth()'
    access_token,refresh_token = readTokens() 
    oauth = None
    if access_token is None:
	oauth = oauthFromSecret(cli,sec)
    else: 
	oauth = oauthFromTokens(access_token,refresh_token,cli,sec)
    return oauth

#############################
def setupClient():
    #this assumes that initialize has been called
    if clientID == 'YYY':
        print 'initialize must be called before setupClient'
        sys.exit(1)
	
    oauth = auth(clientID,secret)
    if oauth is None:
	print 'unable to create oauth2 object'
        sys.exit(1)
    if DEBUG:
        #client = Client(oauth,LoggingNetwork())
        client = Client(oauth)
    else: 
        client = Client(oauth)
    if client is None:
	print 'unable to create Box Client object'
        sys.exit(1)

    #use this to access box
    return client

################ initialize ##################
def initialize(client,sec,redir,token):
    global redir_uri,clientID,secret,token_uri,boxClient
    if DEBUG:
        print 'in oauth2_cli:initialize() {0},{1}'.format(client,redir)
    clientID = client
    secret = sec
    redir_uri=redir
    token_uri=token
    boxClient =  setupClient();

    if TEST_REFRESH:
        worked = refresh_creds() 
        if not worked: 
            if os.path.isfile('tokens'):
                os.path.remove('tokens')
            boxClient =  setupClient();
            worked = refresh_creds() 
            if not worked: 
                print 'Error, refresh failed the second time.  Unable to continue'
                sys.exit(1)

################ readTokens ##################
def readTokens():
    if not os.path.isfile('tokens'):
        return None,None
    with open('tokens', 'rb') as f:
        acc = f.readline().rstrip('\n')
        ref = f.readline().rstrip('\n')
    return acc,ref

################ writeTokens ##################
def writeTokens(acc,ref):
    with open('tokens', 'wb') as f:
        f.write(acc+'\n')
        f.write(ref+'\n')
    
#############################
def download(fid,ldir,flat=True):    
    '''Download files from box directory recursively into ldir '''
    if not flat:
        print 'unsupported feature, only flattening into ldir is currently supported'''
        return 'Error - Flat only available'
    try:
        folder = boxClient.folder( folder_id=fid, ).get()
    except: #try again
        folder = boxClient.folder( folder_id=fid, ).get()

    if DEBUG:
        print 'in oauth2_cli.download() {0} {1}'.format(fid,folder.name)
    MAX = 100
    offset = 0
    items = folder.get_items(limit=MAX,offset=offset)
    while len(items) is not 0:
        for f in items:
	    if type(f).__name__=='Folder':
                download(f.id,ldir)
	    if type(f).__name__=='File':
                fname = '{0}/{1}'.format(ldir,f.name)
		get_thumbnail(f.id,fname)

		#instead of saving off the thumbnail, do the actual file
                #boxfile = get_file_using_boxclient(f.id)
                #fileAsString = boxfile.content()
		#process_jpeg(fileAsString) #rename using exif info (not working)
                
        offset += MAX
        items = folder.get_items(limit=MAX,offset=offset)
    return

#############################
def process_jpeg(fin):    
    ''' this doesn't work for the images without jpeg exif info '''
    fjpeg = StringIO(fin)
    tags = exifread.process_file(fjpeg)
    print tags
    stop_tag = 'Image DateTime'
    dt_tag = vars(tags[stop_tag])['printable']
    photo_id = 0
    #dt_tag: 2014:08:01 19:06:50
    d = (dt_tag.split()[0]).replace(':','-')
    t = dt_tag.split()[1]
    newfname = 'Main_{1}_{2}_{3}.JPG'.format(prefix,d,t,photo_id)

#############################
def get_folder_using_boxclient(fid):    
    try:
        folder = boxClient.folder( folder_id=fid, ).get()
    except: #try again
        folder = boxClient.folder( folder_id=fid, ).get()
    return folder

#############################
def get_file_using_boxclient(fid):    
    global boxClient
    f = None
    try:
        f = boxClient.file( file_id=fid, ).get()
    except boxsdk.exception.BoxOAuthException as boxe: 
        print boxe.__dict__
        if boxe._status == 400 or boxe._status == 401:
            refresh_creds()
	    boxClient =  setupClient();
        try:
            f = boxClient.file( file_id=fid, ).get()
        except Exception as e : #try again
 	    print e
 	    print type(e)
 	    print e.__dict__
	    print f
	    sys.exit(1)
    
    return f


################ get_thumbnail ##################
def get_thumbnail(fileID,fname='thumbnail.png'):
    
    '''
    This function is invoked to access the API at api_url using requests
    It uses stored credentials, or creates them if not stored.
    It does NOT use the Box Client
    get thumbnail:
    curl --header "Authorization: Bearer XXX" https://api.box.com/2.0/files/94082555506/thumbnail.png\?min_height=256\&min_width=256 -o test.png

    if there is no thumbnail, nothing will be downloaded/stored (box generates thumbnails)
    '''
    if DEBUG:
	print 'in oauth2_cli:get_thumbnail() {0} {1}'.format(fileID, fname)
    access_token,refresh_token = readTokens() 
    
    header = {'Authorization': 'Bearer {0}'.format(access_token)}
    api_url = 'https://api.box.com/2.0/files/{0}/thumbnail.png'.format(fileID)
    payload = {'min_height':'256','min_width':'256'}
    r = None
    try:
        r = requests.get(api_url, data=payload, headers=header)
    except requests.exceptions.RequestException as e:  
        print 'API Access failed: {0}'.format(e)
        output = {'name':'api_access_failed'}
        return output

    if r is not None:
	#This is where we insert the code for storing the data that comes back from the request
        if r.status_code == 401 or r.status_code == 400:  #unauthorized - check if refresh is needed, else regenerate from code

            #todo: this returns false up on failure, handle it better
            success = refresh_creds()
            success = None
	    if not success:
                print 'refresh failed'
                sys.exit(1)

            #do it again
            header = {'Authorization': 'Bearer {0}'.format(access_token)}
            r = None
            try:
                r = requests.get(api_url, headers=header)
            except requests.exceptions.RequestException as e:  
                print 'API Access post refresh failed: {0}'.format(e)
                output = {'name':'api_access_post_refresh_failed'}
                return output

        if r is not None:
            if r.status_code == 200:
                output = {'name':'api_access_succeeded200'}
	        with open(fname, 'wb') as f:
                    f.write(r.content)
            else: 
                output = {'name':'api_access_failed4'}
        else: 
            output = {'name':'api_access_failed2'}
      
    else: 
        output = {'name':'api_access_failed3'}

    return output

################ refresh_creds ##################
def refresh_creds():

    '''
    Utility to refresh OAuth2 access_token.
    '''
    if DEBUG: 
	print 'in oauth2_cli:refresh_creds()'
    access_token,refresh_token = readTokens() 

    payload = {'grant_type':'refresh_token', 
        'refresh_token':refresh_token,
        'client_id':clientID, 
        'client_secret':secret, 
    }
    headers={
      'Content-Type':'application/x-www-form-urlencoded'
    }


    if DEBUG:
        print '\nrefresh payload: {0}\n\theader {1}'.format(payload,headers)
    req = requests.Request('POST',token_uri,data=payload,headers=headers)
    prepared = req.prepare()
    if DEBUG:
        pretty_print_POST(prepared)
    s = requests.Session()
    resp = s.send(prepared)
    res = resp.json()
    if DEBUG:
        print 'result: {0}'.format(res)
    if 'error' in res:
        print 'refresh error: {0}'.format(res['error'])
        ''' any error that occurs in the refresh process will result in restarting the protocol.
            Protocol restart (oauth2setup) requires the user/customer to reauthorize our
            use of their account '''
        return False

    writeTokens(res['access_token'],res['refresh_token'])
    return True
