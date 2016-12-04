from __future__ import print_function
import httplib2
import os
from frappeclient import FrappeClient
import traceback
import csv
import sys
import time
import string
import random
import threading
from pubnub import Pubnub
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
import requests

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'
SERVER_URL = "http://pds.intego.rw:8000"
client = FrappeClient("http://pds.intego.rw:8000", "administrator", "pds")

pubnub = Pubnub(publish_key="pub-c-21663d8a-850d-4d99-adb3-3dda55a02abd", subscribe_key="sub-c-266bcbc0-9884-11e6-b146-0619f8945a4f")


def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))


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

def send_location(typ,entity, location):
	location_data = {
		"doctype": "Location",
		"type": typ,
		"latitude": location.latitude,
		"longitude": location.longitude,
		"order_number": entity  if typ == 'Client' else None,
		"delivery_clerk": entity if typ == 'Delivery Clerk' else None,
		"location_number": location.number
	       }
	try:
		client.insert(location_data)
	except:
		print("*** print_exc:")
		traceback.print_exc()

def post_request(order_number, pickup_point, dropoff_point):
        request_data= {
                       "doctype": "Delivery Request",
                       "customer": "Kasha Inc",
		       "client_names": "AAAAA BBBBBBB",
                       "order_number": order_number,
                       "pickup_point": pickup_point.formatted(),
                       "pickup_point_number": pickup_point.number

               }
        try:
                request = client.insert(request_data)
                return request['name']
        except:
                pass

def update_request(name, field, value):
	request = client.get_doc("Delivery Request", name)
	request[field] = value
	try:
		client.update(request)
		print(request)
	except:
		 pass
class Coordinate():
	def __init__(self, number, coordinates):
		self.number = int(number)
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
    all_locations = []
    for number, location in enumerate(result.get('values', [])):
		all_locations.append(Coordinate(number, location))
    return all_locations

def initialize_clerks(clerks, locations):
	for clerk in clerks:
		clerk = client.get_doc("User", clerk)
		location = locations[random.randint(1, len(locations) -1)]
		clerk['location'] = location.formatted()
		clerk['location_number'] = location.number
		#clerk['status'] = 'Free' if clerk['email'] == 'sebudandi@gmail.com' else 'Busy'
		clerk['status'] = 'Free'
		try:
			client.update(clerk)
		except:
			 pass
		

class Delivery(threading.Thread):
	def __init__(self, order_id, order_number, pickup_point, dropoff_point):
		threading.Thread.__init__(self)
		self.order_id = order_id
		self.order_number = order_number
		self.pickup_point = pickup_point
		self.dropoff_point = dropoff_point

	def callback(self, message, channel):
		if message['type'] == 'Assigned':
			update_request(self.order_id, 'status', 'Assigned')
			for location in self.locations[self.pickup_point.number:self.dropoff_point.number]:
				send_location('Delivery Clerk', message['message'], location)

	def start_delivering(self):
		r = requests.get(SERVER_URL+"/api/method/pds.api.start_delivering?order_number=%s" % self.order_id)
		update_request(self.order_id, 'status', 'Delivering')
		return r.status_code

	def finish_delivering(self):
		r = requests.get(SERVER_URL+"/api/method/pds.api.finish_delivering?order_number=%s" % self.order_id)
		update_request(self.order_id, 'status', 'Delivered')
		return r.status_code

	def run(self):
		pubnub.subscribe(channels=self.order_number, callback=self.callback)


class Clerk(threading.Thread):
	def __init__(self, locations, location, email, delivery = None):
		threading.Thread.__init__(self)
		self.locations = locations
		self.location = location
		self.email = email
		self.delivery = delivery

	def set_location(self, location):
		self.location = location 

	def move(self, start, end):
		direction  = -1 if start.number > end.number else 1
		for location_number in range(start.number, end.number, direction):
			self.set_location(self.locations[location_number])
			send_location('Delivery Clerk', self.email, self.locations[location_number])

	def deliver(self):
		update_request(self.delivery.order_id, 'status', 'Assigned')
		self.move(self.location, self.delivery.pickup_point)
		self.delivery.start_delivering()
		self.move(self.delivery.pickup_point, self.delivery.dropoff_point)
		self.delivery.finish_delivering()
		self.move(self.delivery.dropoff_point, self.delivery.pickup_point)


	def run(self):
		if self.delivery:
			self.deliver()
			

if __name__ == '__main__':
	#loading dummy locations
	print("Loading dummy locations")
	locations = locations()
	#pick a random point as the warehouse
	warehouse = locations[random.randint(1, len(locations) -1)]  
	print("Picked warehouse %s" % warehouse)

	#initialise clerk to the warehouse as their location
	clerks = ["sebudandi@gmail.com", "arwema@gmail.com", "renekabagamba@gmail.com", "basorot@gmail.com"]
	print("Initializing clerk positions")
	initialize_clerks(clerks, locations)
	while True:
		order_number = "sim_order_"+id_generator(size=6) 
		pickup_point = warehouse
		#wait random seconds
		wait_time = random.randint(0, 10)
		print("waiting for %i seconds" % wait_time)
		time.sleep(wait_time)
		#pick a random dropoff point for this order
		dropoff_point = locations[random.randint(1, len(locations) -1)]
		order_id = post_request(order_number, pickup_point, dropoff_point)
		print("Create delivery request %s" %  order_id)
		#send client location
		send_location('Client', order_number, dropoff_point)

	"""
	order_number = "sim_order_"+id_generator(size=6)
	dropoff_point = locations[random.randint(1, len(locations) -1)]
	order_id = post_request(order_number, warehouse, dropoff_point)
	delivery = Delivery(order_id, order_number, warehouse, dropoff_point)
	update_request(order_id, 'status', 'Assigned')
	payload = {'usr': 'sebudandi@gmail.com', 'pwd': 'sebudandi'}
	print(requests.post("http://pds.intego.rw:8000/api/method/login", data=payload))
	print(delivery.start_delivering())
	print(delivery.finish_delivering())
	"""
