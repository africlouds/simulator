from __future__ import print_function
#import httplib2
import os
from frappeclient import FrappeClient
import traceback
import csv
import sys
import time



from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


client = FrappeClient("http://pds.intego.rw:8000", "administrator", "pds")


def requests():
	request_data= {
		       "doctype": "Delivery Request",
		       "customer": "Kasha Inc",
		       "order_number": "0001",
		       "pickup_point": "-1.9594849,30.1062469" 
	       }
	try:
	    client.insert(request_data)
	except:
	    pass


if __name__ == '__main__':
	requests()
