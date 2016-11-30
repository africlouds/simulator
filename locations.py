from __future__ import print_function
import httplib2
import os
from frappeclient import FrappeClient
import traceback
import csv
import sys
import time
import string


from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'




def get_credentials():

    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

class Coordinate():
	def __init__(self, number, coordinates):
		self.number = number
		self.coordinates = coordinates
		self.latitude = coordinates[0]
		self.longitude = coordinates[1]

	def formatted(self):
		return "%s,%s" % tuple(self.coordinates) 

def locations():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    spreadsheetId = '1N3ZvRmdI2Eb3FQjg5oo-GAXH4ZfoC2l5c5ymO8J7SjA'
    rangeName = 'Locations!A2300:B2480'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    locations = []
    for number, location in enumerate(result.get('values', [])):
	locations.append(Coordinate(number, location))
    return locations


if __name__ == '__main__':
	#loading dummy locations
	print("Loading dummy locations")
	locations = locations()
	print(locations)
