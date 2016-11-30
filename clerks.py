from pubnub import Pubnub
import sys
from frappeclient import FrappeClient
import locations
import simulation
import traceback

pubnub = Pubnub(publish_key="pub-c-21663d8a-850d-4d99-adb3-3dda55a02abd", subscribe_key="sub-c-266bcbc0-9884-11e6-b146-0619f8945a4f")
client = FrappeClient("http://pds.intego.rw:8000", "administrator", "pds")


locations = locations.locations()

def update_request(name, field, value):
        request = client.get_doc("Delivery Request", name)
        request[field] = value
        try:
                client.update(request)
                print(name)
        except:
                 pass


def callback(message, channel):
	print(channel)
	print(message)
	if 'type' in message and message['type'] == 'Delivery Request':
		try:
        		request = client.get_doc("Delivery Request", message['order_id'])
			update_request(message['order_id'], 'status', 'Assigned')
			start = request['pickup_point_number']
			finish = request['dropoff_point_number']
			direction  = -1 if start > finish else 1
			for location_number in range(start, finish, direction):
				simulation.send_location('Delivery Clerk', request['assigned_clerk'], locations[location_number])
		except:
			print "*** print_exc:"
			traceback.print_exc()
			print("Byanze")
  
  
def error(message):
    print("ERROR : " + str(message))
  
  
def connect(message):
    print("CONNECTED")
    message = [{'latlng':[-1.9500000, 30.1044288]}]
    print(pubnub.publish(channel='sebudandi@gmail.com', message=message))
  
  
  
def reconnect(message):
    print("RECONNECTED")
  
  
def disconnect(message):
    print("DISCONNECTED")


  
  
clerks = ["sebudandi@gmail.com", "arwema@gmail.com", "renekabagamba@gmail.com", "basorot@gmail.com"]
pubnub.subscribe(channels=clerks, callback=callback, error=callback,
                 connect=connect, reconnect=reconnect, disconnect=disconnect)
