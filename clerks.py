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
	#print(channel)
	#print(message)
	if 'type' in message and message['type'] == 'Delivery Request':
		try:
			request = client.get_doc("Delivery Request", filters=[["Delivery Request", "name","=",message['order_id']]], fields=["name","pickup_point", "dropoff_point","pickup_point_number","dropoff_point_number","order_number","assigned_clerk"])
			request = request[0]
			pickup_point = request['pickup_point'].split(",")
			dropoff_point = request['dropoff_point'].split(",")
			pickup_point = simulation.Coordinate(request['pickup_point_number'],pickup_point) 
			dropoff_point = simulation.Coordinate(request['dropoff_point_number'],dropoff_point) 
			delivery_request = simulation.Delivery(request['name'], request['order_number'], pickup_point, dropoff_point) 
        		clerk = client.get_doc("User", filters=[["User", "name", "=", request['assigned_clerk']]], fields=["location", "location_number", "email"])
			clerk = clerk[0]
			clerk_location = clerk['location'].split(",")
			clerk_location = simulation.Coordinate(clerk['location_number'], clerk_location) 
			clerk = simulation.Clerk(locations, clerk_location, clerk['email'], delivery_request)
			clerk.start()
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
