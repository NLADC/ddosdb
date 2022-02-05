from . import views
from .celery import app
from .views import remote_push_sync, remote_pull_sync, remote_misp_push_sync, remote_misp_pull_sync
import requests
import urllib3
import logging
import pymongo
from datetime import datetime

# from celery import shared_task
from django.apps import AppConfig
# from ddosdb.models import Query, AccessRequest, Blame, FileUpload, RemoteDdosDb, FailedLogin
from django.conf import settings
from ddosdb.models import RemoteDdosDb


logger = logging.getLogger(__name__)


def _mdb():
    URI = "mongodb://" + settings.MONGODB

    client = pymongo.MongoClient(URI)
    DATABASE = client.ddosdb.fingerprints
    return DATABASE


def _search(query=None, fields=None, order=None):
    q = query
    if order:
        q = {}
        q["$query"] = query
        q["$orderby"] = order

    logger.info("filter={}, fields={}".format(q, fields))
    result = list(_mdb().find(q, fields))
    return result


def _insert(data):
    _mdb().insert(data)


@app.task(name='ddosdb.tasks.push_sync', bind=True)
def push_sync(self):
    return remote_push_sync()


@app.task(name='ddosdb.tasks.pull_sync', bind=True)
def pull_sync(self):
    return remote_pull_sync()


@app.task(name='ddosdb.tasks.misp_push_sync', bind=True)
def misp_push_sync(self):
    return remote_misp_push_sync()


@app.task(name='ddosdb.tasks.misp_pull_sync', bind=True)
def misp_pull_sync(self):
    return remote_misp_pull_sync()



# @app.task(name='ddosdb.tasks.check_to_sync', bind=True)
# def check_to_sync(self):
#     remotes = RemoteDdosDb.objects.filter(active=True, push=True)
#     logger.info("Remote DDoSDBs:")
#     i = 0
#     for remote in remotes:
#         i += 1
#         logger.info("Remote (push) DDoSDB #{}:{} - {}@{}".format(i, remote, remote.username, remote.url))
#         sync_remote_push.delay(remote.id)
#
#     remotes = RemoteDdosDb.objects.filter(active=True, pull=True)
#     logger.info("Remote DDoSDBs:")
#     i = 0
#     for remote in remotes:
#         logger.info("Remote (pull) DDoSDB #{}:{} - {}@{}".format(i, remote, remote.username, remote.url))
#         sync_remote_pull.delay(remote.id)
#
#
# @app.task(name='ddosdb.tasks.sync_remote_push', bind=True)
# def sync_remote_push(self, remote_id):
#     logger.info("sync_remote (push) id# {}".format(remote_id))
#     rdb = RemoteDdosDb.objects.get(pk=remote_id)
#     fingerprints = _search({'shareable': True}, {'_id': 0})
#     fp_keys = [fp['key'] for fp in fingerprints]
#     result = {
#         "remote": rdb.name,
#         "type": "push",
#         "keys": fp_keys,
#         "result": "Success"
#     }
#     logger.info("Fingerprints to sync: {}".format(fp_keys))
#
#     url = rdb.url
#     if url.endswith('/'):
#         url = url[:-1]
#     try:
#         logger.info("Contacting remote (push) DDoSDB:{} @ {}".format(rdb, rdb.url))
#         urllib3.disable_warnings()
#         r = requests.post("{}/unknown-fingerprints".format(url),
#                         auth=(rdb.username, rdb.password),
#                         json=fp_keys,
#                         timeout=10,
#                         verify=rdb.check_cert)
#         logger.info("status:{}".format(r.status_code))
#         if r.status_code == 200:
#             logger.info("Fingerprint keys unknown to (push) {}: {}".format(rdb.name, r.json()))
#             unk_fps = r.json()
#             result["keys"] = unk_fps
#             if len(unk_fps) > 0:
#                 # fps_to_sync = []
#                 # for (unk_fp in unk_fps):
#                 fps_to_sync = list(filter(lambda fp: fp['key'] in unk_fps, fingerprints))
#                 logger.debug("Fingerprints to push: {}".format(fps_to_sync))
#
#                 urllib3.disable_warnings()
#                 r = requests.post("{}/fingerprints".format(url),
#                                   auth=(rdb.username, rdb.password),
#                                   json=fps_to_sync,
#                                   verify=rdb.check_cert)
#         logger.info("Sync push response:{}".format(r.status_code))
#     except Exception as e:
#         logger.info("{}".format(e))
#         result["result"] = "Failed ({})".format(e)
#     return result
#
#
# @app.task(name='ddosdb.tasks.sync_remote_pull', bind=True)
# def sync_remote_pull(self, remote_id):
#     logger.info("sync_remote (pull) id# {}".format(remote_id))
#     rdb = RemoteDdosDb.objects.get(pk=remote_id)
#
#     result = {
#         "remote": rdb.name,
#         "type": "pull",
#         "keys": [],
#         "result": "Success"
#     }
#
#     fps_srch = _search(fields={'key': 1, "_id": 0})
#     fps = [fp['key'] for fp in fps_srch]
#     logger.info("Fingerprints I have: {}".format(fps))
#
#     logger.info("Contacting remote (pull) DDoSDB:{} @ {}".format(rdb, rdb.url))
#     unk_fps = []
#
#     url = rdb.url
#     if url.endswith('/'):
#         url = url[:-1]
#     try:
#         urllib3.disable_warnings()
#         r = requests.get("{}/fingerprints".format(rdb.url),
#                         auth=(rdb.username, rdb.password),
#                         timeout=10, verify=rdb.check_cert)
#         logger.info("status:{}".format(r.status_code))
#         if r.status_code == 200:
#             logger.info("Fingerprints at {}: {}".format(rdb.name, r.json()))
#             rem_fps = r.json()
#             for rem_fp in rem_fps:
#                 if not rem_fp in fps:
#                     unk_fps.append(rem_fp)
#             logger.info("Fingerprints to pull: {}".format(unk_fps))
#             if len(unk_fps) > 0:
#                 for unk_fp in unk_fps:
#                     r = requests.get("{}/fingerprint/{}".format(rdb.url, unk_fp),
#                                      auth=(rdb.username, rdb.password),
#                                      timeout=10, verify=rdb.check_cert)
#                     if r.status_code == 200:
#                         fp = r.json()[0]
#                         fp["shareable"] = False
#                         # Set submit timestamp
#                         fp["submit_timestamp"] = datetime.utcnow().isoformat()
#                         if not 'comment' in fp:
#                             fp['comment'] = ""
#                         _insert(fp)
#             result["keys"] = unk_fps
#     except Exception as e:
#         logger.info("{}".format(e))
#         result["result"] = "Failed ({})".format(e)
#     return result
