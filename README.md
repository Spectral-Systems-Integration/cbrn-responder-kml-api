###### CBRN Responder KML/KMZ Uploader Code 
    
    This is a python program that is intended to be run on a UNIX and/or Linux (or similar)
    command-line. It is intended to upload a set of KMLs and/or KMZs to CBRN Responder via
    an already-existing Equipment Data API. 
     
###### INSTALLATION and/or Pre-requisites:

    To use this code, please have a version of Python 3 installed onto your system.
    There are several 3rd party Python libraries are required. These can usually be
    installed with the "pip3" command-line utility. See below:

    1. pyyaml (pip3 install pyyaml)
    2. dotenv (pip3 install dotenv) 
    3. pathlib (pip3 install pathlib)

    Other modules like requess, zipfile, datetime, and base64 usually come built-in with
    later versions of Python 3 (certainly Python 3.8.10, which is running on my
    system). If these other modules may be missing, please install.

###### USAGE VIA COMMAND LINE:
 
    To use this script, first update the configuration file 'config.yaml' with
    the following contents:

    ---
    client_id: 457143eb-c398-45a1-b563-be86c27e9a36
    client_secret: <your_secret> 
    equipment_serial_number: 2024-001
    kml_file_dir: /home/gerasimos/Desktop/work/kalman_and_ssi/cbrn_responder_api/github_20251210/cbrn-responder-kml-api/testdata
    event_id: 1284200
 
    This is just an example that you see. So you will need to update/change the
    values for: 

    (1) CBRN responder event ID (e.g. https://www.cbrnresponder.net/app/index#event/1284200/gis/index
        whereas the event ID here is "1284200")
    (2) A full (absolute) path on your LOCAL file-system containing the KML files you wish to upload
    (3) Equipment Serial number associated with existing CBRN Responder Equipment Data API
    (4) Client secret associated with existing CBRN Responder Equipment Data API
    (5) Client ID associated with existing CBRN Responder Equipment Data API
   
    To run the script, make sure 'config.yaml' and 'upload_kml.py' are in the SAME directory.
    Then invoke python3:
    
    $ python3 upload_kml.py
 
###### PYTHON VERSION:
     
    Supports Python 3.x
    Try Python 3.8.10+ (e.g. Ubuntu 20.04)
       
###### @author: 
    Gerasimos 'Geri' Michalitsianos
    lakithra@protonmail.com
    12 December 2025 
