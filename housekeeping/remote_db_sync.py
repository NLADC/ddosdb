#!/usr/bin/env python
import requests
from requests.auth import HTTPBasicAuth
import pprint

pp = pprint.PrettyPrinter(indent=4)

def get_shareable_fingerprints(base_url, user, password):
    fps = []
    resp = requests.get('http://localhost:8000/fingerprints?q=shareable:true', auth=HTTPBasicAuth('ddosdb', 'ddosdbddosdb'))
    if resp.status_code != 200:
        # This means something went wrong.
        print('Something went wrong: {}'.format(resp.status_code))
    else:
        fps = resp.json()
    return fps

def get_unknown_fingerprints(fps, base_url, user, password):
    unk_fps = []
    resp = requests.post('http://localhost:8000/unknown-fingerprints', json=fps, auth=HTTPBasicAuth('ddosdb', 'ddosdbddosdb'))
    if resp.status_code != 200:
        # This means something went wrong.
        print('Something went wrong: {}'.format(resp.status_code))
    else:
        unk_fps = resp.json()
    return unk_fps

fps = get_shareable_fingerprints('http://localhost:8000', 'ddosbd', 'ddosdbddosdb')

print("Found {} fingerprints".format(len(fps)))
for key in fps:
    print("Fingerprint key {}".format(key))
fps.append("1234")

print()
fps = get_unknown_fingerprints(fps, 'http://localhost:8000', 'ddosbd', 'ddosdbddosdb')
print("Found {} unknown fingerprints".format(len(fps)))
for key in fps:
    print("Fingerprint key {}".format(key))

