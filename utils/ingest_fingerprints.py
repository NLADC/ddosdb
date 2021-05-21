#! /usr/bin/env python3

import sys
import os
import datetime
import pprint
import json
import requests
import random
import urllib3

DDOSDB_URL='https://127.0.0.1'
USERNAME='upload'
PASSWORD='uploadupload'

def openJSON(filename):
    """open the JSON (result) file and return it as a json structure"""
    data = {}
    with open(filename) as f:
        data = json.load(f)
    return data

#############################################

pp = pprint.PrettyPrinter(indent=4)

if len(sys.argv) < 2 :
    print('Usage: ')
    print(sys.argv[0], ' <JSON fingerprint file|JSON fingerprints directory> ')
    quit(1)


filelist=[]
filename = sys.argv[1]

if os.path.isdir(filename):
    if not filename.endswith("/"):
        filename=filename+'/'
    with os.scandir(filename) as it:
        for entry in it:
            if not entry.name.startswith('.') and entry.is_file() and entry.name.endswith('.json'):
                    filelist.append('{0}{1}'.format(filename, entry.name))
else:
    filelist.append(filename)

pp.pprint(filelist)

for fn in filelist:
    data = openJSON(fn)
#    pp.pprint(data)
    if 'key' in data:
        try:
            for i in range(0, 5):
                data['key'] = "".join([random.choice("abcdef0123456789") for i in range(15)])
                print("{}: ".format(data['key']), end="")
                urllib3.disable_warnings()
                r = requests.post("{}/fingerprints".format(DDOSDB_URL),
                                  auth=(USERNAME, PASSWORD),
                                  json=data,
                                  timeout=10,
                                  verify=False)
                print(r.status_code)
        except Exception as e:
            print(e)
            continue

# All done
