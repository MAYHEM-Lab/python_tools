'''Author: Chandra Krintz, UCSB, ckrintz@cs.ucsb.edu, AppScale BSD license
   library used for oauth2 handshake using Google's Oauth2 lib
   https://developers.google.com/api-client-library/python/start/get_started 
   required: google-api-python-clien

   USAGE: import oauth2_cli_util
'''

import json, traceback, requests, sys, argparse, csv
from datetime import datetime, timedelta
from urllib import urlencode
import logging
#Google APIs OAuth2 library: pip install --upgrade google-api-python-client
from oauth2client import client as oclient
from oauth2client.file import Storage as ostorage

DEBUG = True
CLI_session = {}
#this is set in intialize_storage which must be run before all else, app entry is /
app_name = 'XXX'
service = 'YYY'
storage = None
redir_uri = None

#You will also need a box login and password, and have added an app in box
#to obtain the client/secret above and to set/get the redirect url

################ initialize_storage ##################
def initialize_storage():
  '''
  Utility to grab the credentials from storage if any
  -- from https://developers.google.com/api-client-library/python/guide/aaa_oauth
  '''
  global storage
  print 'oauth2_cli_util:in initialize_storage {0}, {1}'.format(app_name,service)
  if storage is None:
      fname = '{0}_{1}'.format(app_name,service)
      storage = ostorage(fname)
  credentials = storage.get()
  if credentials is not None:
      CLI_session['credentials'] = oclient.OAuth2Credentials.to_json(credentials)
      if DEBUG:
          creds = json.loads(CLI_session['credentials'])
      return True
  return False
    

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

################ refresh_creds ##################
def refresh_creds():

    '''
    Utility to refresh OAuth2 access_token.
    '''
    global storage
    print 'oauth2_cli_util:in refresh_creds'
    print 'Token has expired... refreshing'
    print redir_uri

    creds = json.loads(CLI_session['credentials']) 
    payload = {'grant_type':'refresh_token', 
        'refresh_token':creds['refresh_token'],
        'client_id':creds['client_id'], 
        'client_secret':creds['client_secret'], 
    }
    headers={
      'Content-Type':'application/x-www-form-urlencoded',
    }

    if DEBUG:
        print '\nrefresh payload: {0}\n\ttoken_uri {1}\n\t{2}'.format(payload,creds['token_uri'],headers)
    req = requests.Request('POST',creds['token_uri'],data=payload,headers=headers)
    prepared = req.prepare()
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

    ''' 
    Create a new creds object and save it off on disk for fast access.
    Note that the object saved on disk is clear text and contains the secret.
    '''
    refr = creds['refresh_token']
    if res['refresh_token'] is not None:
        print 'got a valid refresh token'
        refr = res['refresh_token'] #get the new refresh token if any
    if DEBUG:
        print 'refresh token: {0}'.format(refr)

    credentials = oclient.OAuth2Credentials(access_token=res['access_token'],
        client_id=creds['client_id'],
        client_secret=creds['client_secret'],
        refresh_token=refr,
        token_expiry=datetime.now()+timedelta(seconds=res['expires_in']),
        token_uri=creds['token_uri'],user_agent=creds['user_agent'])
    fname = None
    if storage is None:
        fname = '{0}_{1}'.format(app_name,service)
        storage = ostorage(fname)
    storage.put(credentials)
    CLI_session['credentials'] = oclient.OAuth2Credentials.to_json(credentials)
    if DEBUG:
        print 'Stored creds at={0} and in file if not None {1}'.format(res['access_token'],fname)
    return True

################ setupStorage ##################
def setupStorage(app,client,redir):
    global storage,redir_uri,app_name,service
    print 'oauth2_cli_util:in setupStorage {0},{1},{2}'.format(app,client,redir)
    app_name = app
    service = client
    fname = '{0}_{1}'.format(app_name,service)
    print 'setting up redir: {0}'.format(redir)
    redir_uri=redir
    storage = ostorage(fname)

################ getTokens ##################
def getTokens():
    
    '''
    This function returns the access token or None
    '''
    print 'oauth2_cli_util:in getTotkens'
    if 'credentials' not in CLI_session:
        #check first to see if we have valid credentials 
	#stored away from a previous run
        if storage is None:
            return None,None
        if not initialize_storage():
            return None,None
    creds = json.loads(CLI_session['credentials']) #json
    return creds['access_token'],creds['refresh_token']
    
################ get_thumbnail ##################
def get_thumbnail(fileID):
    
    '''
    This function is invoked to access the API at api_url
    It uses stored credentials, or creates them if not stored
    get thumbnail:
    curl --header "Authorization: Bearer XXX" https://api.box.com/2.0/files/94082555506/thumbnail.png\?min_height=256\&min_width=256 -o test.png
    '''
    print 'oauth2_cli_util:get_thumbnail'
    if 'credentials' not in CLI_session:
        #check first to see if we have valid credentials 
	#stored away from a previous run
        if not initialize_storage():
            output = {'name':'oauth2_required'}
            return output
    creds = json.loads(CLI_session['credentials']) #json
    
    header = {'Authorization': 'Bearer {0}'.format(creds['access_token'])}
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
        if r.status_code == 401:  #unauthorized - check if refresh is needed, else regenerate from code

            #todo: this returns false up on failure, handle it better
            success = refresh_creds()
	    if not success:
                print 'refresh failed'
                sys.exit(1)

            #do it again
            creds = json.loads(CLI_session['credentials']) #json
            header = {'Authorization': 'Bearer {0}'.format(creds['access_token'])}
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
	        with open('thumbnail.png', 'wb') as f:
                    f.write(r.content)
            else: 
                output = {'name':'api_access_failed4'}
        else: 
            output = {'name':'api_access_failed2'}
      
    else: 
        output = {'name':'api_access_failed3'}

    return output


################ query ##################
def query(api_url):
    
    '''
    This function is invoked to access the API at api_url
    It uses stored credentials, or creates them if not stored
    '''
    print 'oauth2_cli_util:in query'
    if 'credentials' not in CLI_session:
        #check first to see if we have valid credentials 
	#stored away from a previous run
        if not initialize_storage():
            output = {'name':'oauth2_required'}
            return output
    creds = json.loads(CLI_session['credentials']) #json
    
    header = {'Authorization': 'Bearer {0}'.format(creds['access_token'])}
    '''get thumbnail:
    curl https://api.box.com/2.0/files/FILE_ID/thumbnail.png?min_height=256&min_width=256 \
    -H "Authorization: Bearer ACCESS_TOKEN"
    '''
    
    payload = {'grant_type':'refresh_token', 
        'refresh_token':creds['refresh_token'],
        'client_id':creds['client_id'], 
        'client_secret':creds['client_secret'], 
        #'redirect_uri':redir_uri,
    }
    r = None
    try:
        r = requests.get(api_url, headers=header)
    except requests.exceptions.RequestException as e:  
        print 'API Access failed: {0}'.format(e)
        output = {'name':'api_access_failed'}
        return output

    if r is not None:
	#This is where we insert the code for storing the data that comes back from the request
        if r.status_code == 401:  #unauthorized - check if refresh is needed, else regenerate from code

            #todo: this returns false up on failure, handle it better
            success = refresh_creds()
	    if not success:
                print 'refresh failed'
                sys.exit(1)

            #do it again
            creds = json.loads(CLI_session['credentials']) #json
            header = {'Authorization': 'Bearer {0}'.format(creds['access_token'])}
            r = None
            try:
                r = requests.get(api_url, headers=header)
            except requests.exceptions.RequestException as e:  
                print 'API Access post refresh failed: {0}'.format(e)
                output = {'name':'api_access_post_refresh_failed'}
                return output

        if r is not None:
	    output = r.json()
        else: 
            output = {'name':'api_access_failed2'}
    else: 
        output = {'name':'api_access_failed3'}

    return output


def setupOAuth2(auth,token,redir,client,secret,app,obs_scope=''):
    global app_name,service,storage,redir_uri
    print 'oauth2_cli_util:setupOAuth2'
    try:
        flow = oclient.OAuth2WebServerFlow(
            client_id=client,
            client_secret=secret,
            scope=obs_scope,
            redirect_uri=redir,
            auth_uri=auth,
            token_uri=token,
            include_granted_scopes=True)
    except: 
        print traceback.format_exc()
        return None

    auth_uri = flow.step1_get_authorize_url()
    redir_uri = redir

    print 'Cut/Paste this URI into the URL box in \
        \na browser window and press enter:\n\n{0}\n'.format(auth_uri)
    print 'You should login and authorize use of your account by this app'
    print 'You will then ultimately be redirected to a URL and a page \
        that says "Connection Refused"'
    auth_code = raw_input('Type in the code that appears after \
        "code="\nin the URL box in your browser window, and press enter: ')

    try:
        credentials = flow.step2_exchange(auth_code)
    except oclient.FlowExchangeError, e:
        print 'Authentication failed: {0}'.format(e)
    
    app_name = app
    service = client
    if storage is None:
        fname = '{0}_{1}'.format(app_name,service)
        storage = ostorage(fname)
    storage.put(credentials)
    json_creds = oclient.OAuth2Credentials.to_json(credentials)
    CLI_session['credentials'] = json_creds
    return flow


