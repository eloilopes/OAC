import requests
import base64
import json
import datetime
from datetime import datetime, timedelta, timezone
import time
import io
import json
import logging
from fdk import response




def handler(ctx, data: io.BytesIO=None):
    logging.getLogger().info("function start")
    url = "<YOUR IDCS URL>"
    oacinstace = '<OAC INSTANCE>'
    appID =""
    appRole=""
    consumer_key = '<CONSUMER KEY>'
    consumer_secret = '<CONSUMER SECRET>'
    consumer_key_secret = consumer_key+":"+consumer_secret
    consumer_key_secret_enc = base64.b64encode(consumer_key_secret.encode()).decode()
    now = datetime.now(timezone.utc)
    dtime = now.strftime("%Y-%m-%d %H:%M:%S")
    current_date = datetime.strptime(dtime, '%Y-%m-%d %H:%M:%S')
    try:
        data='grant_type=client_credentials&scope=urn%3Aopc%3Aidm%3A__myscopes__'
        headers = {
          'Authorization': 'Basic ' + str(consumer_key_secret_enc),
          'Content-Type': 'application/x-www-form-urlencoded'
        }
        # get access token
        response = requests.request("POST", url+"/oauth2/v1/token", headers=headers, data=data)
        #print (response.text)
        access_token = response.json()['access_token']
    except Exception as ex:
        print('ERROR: get access token', ex, flush=True)
        raise
    try:
      #search for internal user ID
      data={}
      headers = {
        'Authorization': 'Bearer ' + str(access_token),
        'Content-Type': 'application/json'
      }
      response = requests.get(url+"/admin/v1/Users?count=3000&startIndex=0", headers=headers, data=data)
    except Exception as ex:
        print('ERROR: search for internal user ID', ex, flush=True)
        raise
 #get last user added in idcs
    try:
      users = []
      lag=timedelta(minutes=5)
      lastdate = current_date-lag
        #searching
      for key in response.json()['Resources']:
          createddate=datetime.strptime(str(key['meta']['created'])[0:19], '%Y-%m-%dT%H:%M:%S')
          if createddate>=lastdate:
              users = {"id": key['id'], "created": str(lastdate), "User Name": key['displayName']}
              print("Last user added : " + users['User Name'])
    except Exception as ex:
        print('ERROR: search for the new user', ex, flush=True)
        raise

      #get all OAC IDs on OCI
    if len(users) > 0:
      try:
        data = "{\r\n  \"schemas\": [ \"urn:ietf:params:scim:api:messages:2.0:SearchRequest\"],\r\n  \"attributes\": [\"displayName\", \"active\"],\r\n  \"filter\": \"displayName co \\\"ANALYTICSINST\\\"\",\r\n  \"sortBy\": \"displayName\",\r\n  \"startIndex\": 1,\r\n  \"count\": 10\r\n}"
        response = requests.request("POST", url+"/admin/v1/Apps/.search", headers=headers, data=data)
        for key in response.json()['Resources']:
            appID = str(key['id'])
            print ("App ID "+ appID + " OAC Instance " + str(key['displayName']) )
            roleResponse = requests.get(url+"/admin/v1/AppRoles?filter=app.value eq "+ '"'+appID +'"', headers=headers)
            for keyRole in roleResponse.json()['Resources']:
                if str(keyRole['displayName']) == ('ServiceAdministrator'):
                    appRole = str(keyRole['id'])
                    print("Role "+ keyRole['displayName'] +" assigned to user "+ users['User Name'])
                    payload = "{\r\n    \"grantee\": {\r\n        \"type\": \"User\",\r\n         \"value\": \""+users['id']+"\"\r\n    },\r\n    \"app\": {\r\n        \"value\": \""+appID+"\"\r\n    },\r\n    \"entitlement\" : {\r\n        \"attributeName\": \"appRoles\",\r\n        \"attributeValue\": \""+appRole+"\"\r\n    },\r\n    \"grantMechanism\" : \"ADMINISTRATOR_TO_USER\",\r\n    \"schemas\": [\r\n    \"urn:ietf:params:scim:schemas:oracle:idcs:Grant\"\r\n  ]\r\n}"
                    #Assign role
                    requests.post(url+"/admin/v1/Grants", headers=headers, data=payload)
      except Exception as ex:
          print('ERROR: adding new role', ex, flush=True)
          raise
    else:
        print("No new users")
    #logging.getLogger().info("function end")
    #return requests.Response()
