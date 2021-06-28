from .celery import app
import requests
import urllib3
import logging
import pymongo
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


@app.task(name='ddosdb.tasks.check_to_sync', bind=True)
def check_to_sync(self):
    remotes = RemoteDdosDb.objects.filter(active=True)
    logger.info("Remote DDoSDBs:")
    i = 0
    for remote in remotes:
        i += 1
        logger.info("Remote DDoSDB #{}:{} - {}@{}".format(i, remote, remote.username, remote.url))
        sync_remote.delay(remote.id)


@app.task(name='ddosdb.tasks.sync_remote', bind=True)
def sync_remote(self, remote_id):
    logger.info("sync_remote id# {}".format(remote_id))
    rdb = RemoteDdosDb.objects.get(pk=remote_id)
    logger.info("Contacting remote DDoSDB:{} @ {}".format(rdb, rdb.url))

    fingerprints = _search({'shareable': True}, {'_id': 0})
    fp_keys = [fp['key'] for fp in fingerprints]
    result = {
        "remote": rdb.name,
        "keys": fp_keys,
        "result": "Success"
    }
    logger.info("Fingerprints to sync: {}".format(fp_keys))

    url = rdb.url
    if url.endswith('/'):
        url = url[:-1]
    try:
        urllib3.disable_warnings()
        r = requests.post("{}/unknown-fingerprints".format(url),
                        auth=(rdb.username, rdb.password),
                        json=fp_keys,
                        timeout=10,
                        verify=rdb.check_cert)
        logger.info("status:{}".format(r.status_code))
        if r.status_code == 200:
            logger.info("Fingerprint keys unknown to {}: {}".format(rdb.name, r.json()))
            unk_fps = r.json()
            result["keys"] = unk_fps
            if len(unk_fps) > 0:
                # fps_to_sync = []
                # for (unk_fp in unk_fps):
                fps_to_sync = list(filter(lambda fp: fp['key'] in unk_fps, fingerprints))
                logger.debug("Fingerprints to sync: {}".format(fps_to_sync))

                urllib3.disable_warnings()
                r = requests.post("{}/fingerprints".format(url),
                                  auth=(rdb.username, rdb.password),
                                  json=fps_to_sync,
                                  verify=rdb.check_cert)
        logger.info("Sync response:{}".format(r.status_code))
    except Exception as e:
        logger.info("{}".format(e))
        result["result"] = "Failed ({})".format(e)
    return result
