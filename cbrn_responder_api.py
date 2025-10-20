#!/usr/bin/python3
import os
import json
import base64
import sys
import requests
from urllib.parse import urlencode

class cbrn_equipment_data_api(object):

  # class members
  # -------------
  URL_ACCESS_TOKEN = 'https://api.cbrnresponder.net/oauth/token'
  URL_EQUIPMENT_DATA_API = 'https://api.cbrnresponder.net/api/v2/gis'

  def __init__(self, body):
    self.body = body

  def upload_kml_cbrn_responder(self, kml_filename: str, 
          equipment_serial_number: str):
    
    # get an updated access token before attempting to upload any KML files 
    # ---------------------------------------------------------------------
    api_token = self.retrieve_access_token()
    if not api_token:
      raise IOError(f'ERROR (fatal): invalid token: {api_token}. Exiting ...')
      sys.exit(1)

    # make sure that the KML file(s) do indeed exist on the file-system
    # -----------------------------------------------------------------
    if not os.path.isfile(kml_filename):
      raise IOError(f'ERROR (fatal): not an exsiting file: {kml_filename}')

    # read contents of KML as base64
    # ------------------------------
    f_kml = open(kml_filename, 'r')
    kml_data = f_kml.read().encode('utf-8')
    kml_data = base64.b64encode(kml_data)
    f_kml.close()

    with open(kml_filename, 'rb') as kml_file:

      # set up headers for request
      # --------------------------
      headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/vnd.google-earth.kml+xml'
      }

      # set up payload body
      # -------------------
      payload = {
        "recordId": "",
        "eventId": "",
        "equipmentSerialNumber": equipment_serial_number,
        "gisFiles": [{
            "fileType": "kml",
            "name": "Test Upload KML",
            "files": [
               {
                  "name": kml_filename,
                  "recordId": "",
                  "data": kml_data
               }
            ]
        }]
      }

      #payload = urlencode(payload)
      response = requests.post(cbrn_equipment_data_api.URL_EQUIPMENT_DATA_API, 
              headers = headers, data = payload)
    
      if response.ok:
        print("KML file uploaded successfully!")
        print(response.json()) # httpbin.org returns JSON
      else:
        print(f"Error uploading KML file: {response.status_code} - {response.text}")

  def retrieve_access_token(self) -> str:
    '''
    Instance method to get CBRN Responder API access
    token for a equipment API. 
    '''
    # dump the payload into a ampersand separated string
    # --------------------------------------------------
    payload_body = ''
    for key, value in self.body.items():
      payload_body += ''.join([key, '=', value])

    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.post(cbrn_equipment_data_api.URL_ACCESS_TOKEN, 
            headers = headers, data = payload_body) 
    
    if response.status_code == 200:
      return response.json()['access_token']
    else:
      print(f'error: {response.status_code} for: \
              {cbrn_equipment_data_api.URL_ACCESS_TOKEN}')
      return None

def main():

  # define variables that are specific to CBRN Responder event (Equipment Data API)
  # -------------------------------------------------------------------------------
  api_client_application_secret = 'z8YYxY0Q3S9l3qAvZV17AnrA9r8enj83LBZrWh2u'
  client_id = '457143eb-c398-45a1-b563-be86c27e9a36'
  equipment_serial_number = '2024-001'
 
  # more parameters that may or not be needed
  # -----------------------------------------
  registration_code = 'uploaderkml'
  registration_url = 'https://www.cbrnresponder.net/#equipment/register/uploaderkml'

  cbrn_api_body = {
    'grant_type': 'client_credentials&',
    'client_id': f'{client_id}&',
    'client_secret': api_client_application_secret 
  }

  # define name of sample KML file in local directory
  # -------------------------------------------------
  kml_filename = 'testdata/test.kml'

  # create a CBRN API object using client-class
  # -------------------------------------------
  cbrn_ob = cbrn_equipment_data_api(cbrn_api_body)

  # attempt to upload KML file
  # --------------------------
  cbrn_ob.upload_kml_cbrn_responder(kml_filename, equipment_serial_number)

if __name__ == '__main__':
  main()
