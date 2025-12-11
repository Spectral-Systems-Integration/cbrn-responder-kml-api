#!/usr/bin/python3
import os
import yaml
import glob
import json
import base64
import sys
import logging
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile
import requests
from dotenv import load_dotenv

# Load environment variables
# --------------------------
load_dotenv()

DEBUG = os.environ.get('DEBUG', '0') != '0'
logging.basicConfig(stream = sys.stderr,
  level = logging.DEBUG if DEBUG else logging.INFO,
  format  =
    '[%(asctime)s.%(msecs)03d %(levelname)s] %(filename)s:%(lineno)d:\n%(message)s'
      if DEBUG else '[%(asctime)s.%(msecs)03d %(levelname)s] %(message)s',
  datefmt = '%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class CBRNEquipmentDataAPI:
  
  # class variables
  # ---------------
  URL_ACCESS_TOKEN = 'https://api.cbrnresponder.net/oauth/token'
  URL_EQUIPMENT_DATA_API = 'https://api.cbrnresponder.net/api/v2/gis'

  def __init__(self, client_id, client_secret):
    self.client_id = client_id
    self.client_secret = client_secret

  def retrieve_access_token(self):
    """Get CBRN Responder API access token"""
    logging.info('Requesting OAuth access token...')

    # Changed Content-Type to application/x-www-form-urlencoded
    # ---------------------------------------------------------
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Removed & from values, proper format
    # ------------------------------------
    payload = {
      'grant_type': 'client_credentials',
      'client_id': self.client_id,
      'client_secret': self.client_secret
    }

    # Use proper URL encoding
    # -----------------------
    response = requests.post(
      self.URL_ACCESS_TOKEN,
      headers = headers,
      data = payload  # requests will auto-encode as x-www-form-urlencoded
    )

    if response.status_code == 200:
      token = response.json()['access_token']
      logging.info(f'Access token obtained ({token[:20]}...)')
      return token
    else:
      logging.error(f'Error {response.status_code} getting token: {response.text}')
      return None

  def upload_kml_file(self, file_path, equipment_serial_number, event_id):
    """
    Upload KML or KMZ file to CBRN Responder
    """

    # log some basic details
    # ----------------------
    logging.info('========================================')
    logging.info('Starting KML upload process')
    logging.info(f'File path: {file_path}')
    logging.info(f'Equipment Serial: {equipment_serial_number}')
    logging.info(f'Event ID: {event_id}')

    # Get access token
    # ---------------
    api_token = self.retrieve_access_token()
          
    if not api_token:
      logging.error('Invalid token. Exiting...')
      sys.exit(1)

    # Handle both KML and KMZ files
    # -----------------------------
    file_ext = Path(file_path).suffix.lower()
    logging.info(f'File extension detected: {file_ext}')

    if file_ext == '.kmz':
      # Extract KML from KMZ if we are dealing with KMZ
      # which is basically a zipped KML
      # -----------------------------------------------
      logging.info('Processing KMZ file...')
      kml_content, file_name = self._extract_kml_from_kmz(file_path)
    elif file_ext == '.kml':
      # Read KML directly if we are dealing simply w/ KML
      # -------------------------------------------------
      logging.info('Processing KML file...')
      with open(file_path, 'r', encoding='utf-8') as f:
        kml_content = f.read()
        file_name = Path(file_path).name
        logging.info(f'Loaded {file_name} ({len(kml_content)} bytes)')
    else:
      # exit if we don't have KML or KMZ
      # --------------------------------
      logging.error('File must be .kml or .kmz')
      sys.exit(1)

    # Encode contents of KML/KMZ to base64
    # which is basically ASCII representation of binary
    # -------------------------------------------------
    logging.info('Preparing KML upload...')
    kml_base64 = base64.b64encode(kml_content.encode('utf-8')).decode('utf-8')
    logging.info(f'Base64 encoded size: {len(kml_base64)} characters')

    # Updated headers and JSON payload
    # --------------------------------
    headers = {
      'Authorization': f'Bearer {api_token}',
      'Content-Type': 'application/json'
    }

    # create payload hash object
    # --------------------------
    payload = {
      "equipmentSerialNumber": equipment_serial_number,
      "gisFiles": [{
        "recordId": "930fde68-2d4e-5089-0000-111000000002",
        "eventId": event_id,
        "fileType": "kml",
        "name": "KML Upload",
        "files": [{
          "name": file_name,
          "recordId": "930fde68-2d4e-5089-0000-111000000003",
          "data": kml_base64
        }]
      }]
    }

    logging.info('Uploading to CBRN Responder API...')
    logging.info(f'Endpoint: {self.URL_EQUIPMENT_DATA_API}')

    # Use json parameter instead of data for JSON payload
    # ---------------------------------------------------
    response = requests.post(
      self.URL_EQUIPMENT_DATA_API,
      headers = headers,
      json = payload
    )

    if response.ok:
      logging.info(f'Upload successful! Status: {response.status_code}')
      logging.info(f'Response: {response.json()}')
      logging.info('========================================')
      logging.info('Upload completed successfully! ✓')
      logging.info('========================================')
      return response.json()
    else:
      logging.error(f'Error uploading: {response.status_code} - {response.text}')
      logging.info('========================================')
      logging.error('Upload failed! ✗')
      logging.info('========================================')
      sys.exit(1)

  def _extract_kml_from_kmz(self, kmz_path):
    """Extract KML content from KMZ archive"""
    with ZipFile(kmz_path, 'r') as zip_file:
      file_list = zip_file.namelist()
      logging.info(f'KMZ contains {len(file_list)} file(s)')

    # Find KML file in archive
    # ------------------------
    kml_files = [f for f in file_list if f.endswith('.kml')]
    if not kml_files:
      logging.error('No KML file found in KMZ archive')
      sys.exit(1)

    kml_filename = kml_files[0]
    kml_content = zip_file.read(kml_filename).decode('utf-8')
    logging.info(f'Extracted {kml_filename} from KMZ ({len(kml_content)} bytes)')
    return kml_content, kml_filename

def export_environment_variables():
  """Export environment variables defined config.yaml"""
  # make sure required config file exists
  # -------------------------------------
  config_filename_yaml = 'config.yaml'

  if not os.path.isfile(config_filename_yaml):
    logger.error(f'error: unable to locate "config.yaml" . Exiting ...')
    sys.exit(1)

  # read the variables within and export as environment variables
  # -------------------------------------------------------------
  config_contents = None
  try:
    with open(config_filename_yaml, 'r') as f:
      config_contents = yaml.safe_load(f)
  except FileNotFoundError:
    logger.error(f'error: unable to locate: {config_filename_yaml}')
    sys.exit(1)
  except yaml.YAMLError as e:
    logger.error(f'error parsing yaml {config_filename_yaml}: {e}')
    sys.exit(1)
  except KeyError as e:
    logger.error(f'error accessing dictionary key {e}')

  # read/export appropriate environment variables
  # ---------------------------------------------
  env_var_hash = {}
  try:
    env_var_hash['client_id'] = config_contents['client_id']
    env_var_hash['client_secret'] = config_contents['client_secret']
    env_var_hash['kml_file_dir'] = config_contents['kml_file_dir']
    env_var_hash['equipment_serial_number'] = config_contents['equipment_serial_number']
    env_var_hash['event_id'] = config_contents['event_id']
  except KeyError as e:
    logger.error(f'missing env. variable: {e}')
  return env_var_hash

def main():

  logging.info('CBRN KML Upload Script Started')
  
  # read YAML configuration file and get environment variables
  # ----------------------------------------------------------
  environment_var_hash = export_environment_variables()

  # iterate through and set environment variables
  # ---------------------------------------------
  for env_variable_key, env_value in environment_var_hash.items():
    logger.info(f'defining following ENV variable: {env_variable_key}  => {env_value}')
    os.environ[env_variable_key.upper()] = str(env_value)
    env_variable_key_upper = env_variable_key.upper()
    os.system(f'export {env_variable_key_upper}={env_value}')
 
  # Load from environment variables
  # -------------------------------
  client_id = os.getenv('CLIENT_ID')
  client_secret = os.getenv('CLIENT_SECRET')
  equipment_serial_number = os.getenv('EQUIPMENT_SERIAL_NUMBER')
  kml_file_dir = os.getenv('KML_FILE_DIR')
  event_id = os.getenv('EVENT_ID')

  # Validate
  # --------
  if not all([client_id, client_secret, equipment_serial_number, kml_file_dir, event_id]):
    logging.error(
            'Missing required environment variables in .env file')
    logging.error(
            'Required: CLIENT_ID, CLIENT_SECRET, EQUIPMENT_SERIAL_NUMBER, KML_FILE_PATH, EVENT_ID')
    sys.exit(1)

  # get the names of the kml files in the KML dir.
  # ----------------------------------------------
  kml_filenames = []
  kml_filenames.extend(glob.glob(kml_file_dir + '/*.kml'))
  kml_filenames.extend(glob.glob(kml_file_dir + '/*.kmz'))
  kml_filenames.extend(glob.glob(kml_file_dir + '/*.KML'))
  kml_filenames.extend(glob.glob(kml_file_dir + '/*.KMZ'))
  
  # report names of KML files found in directory KML_FILE_DIR
  # ---------------------------------------------------------
  api = CBRNEquipmentDataAPI(
          client_id, client_secret)

  for kml_filename in kml_filenames:
    logger.info(f'uploading following KML: {kml_filename}')

    # Upload KML and/or KMZ
    # ---------------------
    api.upload_kml_file(
            kml_filename, equipment_serial_number, event_id)
    break

if __name__ == '__main__':
  main()
