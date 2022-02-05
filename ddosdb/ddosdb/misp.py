import logging
from pprint import PrettyPrinter, pprint
import requests
import urllib3
from pymisp import ExpandedPyMISP, MISPEvent, MISPObject, MISPAttribute, MISPTag
import demjson
import time
from ddosdb.models import MISP

logger = logging.getLogger(__name__)

logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('pymisp').setLevel(logging.WARNING)



# ------------------------------------------------------------------------------
def search_misp_events(misp, filter={}):
    misp_events = None

    logger.info("Searching events with filter: {}".format(filter))

    try:
        urllib3.disable_warnings()
        r = requests.post("{0}{1}{2}".format(misp.url, "/events/index", ""),
                          json=filter,
                          headers={'Authorization': misp.authkey,
                                   'Accept': 'application/json'},
                          timeout=10, verify=misp.check_cert)
        logger.debug("status:{}".format(r.status_code))
        if r.status_code == 200:
            misp_events = r.json()
    except Exception as e:
        logger.error("{}".format(e))

    return misp_events


# ------------------------------------------------------------------------------
def get_misp_fingerprints(misp):
    misp_events = None
    fingerprints = []

    filter = {
        "minimal": False,
        "sort": "publish_timestamp",
        "direction": "desc",
        "tag": "DDoSCH",
    }

    logger.info("Searching fingerprints with filter: {}".format(filter))

    # try:
    urllib3.disable_warnings()
    r = requests.post("{0}{1}{2}".format(misp.url, "/events/index", ""),
                      json=filter,
                      headers={'Authorization': misp.authkey,
                               'Accept': 'application/json'},
                      timeout=10, verify=misp.check_cert)
    logger.debug("status:{}".format(r.status_code))
    if r.status_code == 200:
        misp_events = r.json()
    # except Exception as e:
    #     logger.error("{}".format(e))

    if misp_events:
        logger.info("There are {} MISP events".format(len(misp_events)))
        for m_e in misp_events:
            fingerprints.append(m_e['info'])
    else:
        logger.info("No MISP events returned")

    return fingerprints


# ------------------------------------------------------------------------------
def add_misp_event(misp, event):
    misp_event = None

    logger.info("Creating an event ({})".format(event))

    try:
        urllib3.disable_warnings()
        r = requests.post("{0}{1}{2}".format(misp.url, "/events/add/", ""),
                          json=event,
                          headers={'Authorization': misp.authkey,
                                   'Accept': 'application/json'},
                          timeout=10, verify=misp.check_cert)
        logger.debug("status:{}".format(r.status_code))
        if r.status_code == 200:
            misp_event = r.json()
    except Exception as e:
        logger.error("{}".format(e))

    return misp_event


# ------------------------------------------------------------------------------
def add_misp_object(misp, event_id, misp_object):
    m_o = None

    logger.info("Creating an object for event #{}".format(event_id))

    logger.debug("URL: {0}{1}{2}".format(misp.url, "objects/add/", event_id))
    try:
        urllib3.disable_warnings()
        r = requests.post("{0}{1}{2}".format(misp.url, "objects/add/", event_id),
                          json=misp_object,
                          headers={'Authorization': misp.authkey,
                                   'Accept': 'application/json'},
                          timeout=60, verify=misp.check_cert)
        logger.debug("status:{}".format(r.status_code))
        if r.status_code == 200:
            m_o = r.json()
        else:
            logger.debug(r)
            print(r.text)
    except Exception as e:
        logger.error("{}".format(e))

    return m_o


# ------------------------------------------------------------------------------
def add_misp_tag(misp, tag_name, tag_colour):
    misp_tag = None

    logger.info("Creating a tag")

    try:
        urllib3.disable_warnings()
        r = requests.post("{0}{1}{2}".format(misp.url, "/tags/add/", ""),
                          json={'name': tag_name, 'colour': tag_colour},
                          headers={'Authorization': misp.authkey,
                                   'Accept': 'application/json'},
                          timeout=10, verify=misp.check_cert)
        logger.debug("status:{}".format(r.status_code))
        if r.status_code == 200:
            misp_tag = r.json()
    except Exception as e:
        logger.error("{}".format(e))

    return misp_tag


# ------------------------------------------------------------------------------
def add_misp_tag_to_event(misp, event_id, tag_id):
    misp_tag = None
    logger.info("Creating a tag")

    try:
        urllib3.disable_warnings()
        r = requests.post("{0}{1}{2}/{3}".format(misp.url, "/events/addTag/", event_id, tag_id),
                          # json={},
                          headers={'Authorization': misp.authkey,
                                   'Accept': 'application/json'},
                          timeout=10, verify=misp.check_cert)
        logger.debug("status:{}".format(r.status_code))
        if r.status_code == 200:
            misp_tag = r.json()
    except Exception as e:
        logger.error("{}".format(e))

    return misp_tag


# ------------------------------------------------------------------------------
def add_misp_fingerprint(rmisp, fp):

    logger.info("Creating/adding a DDOS object")
    start = time.time()

    misp = ExpandedPyMISP(rmisp.url, rmisp.authkey, ssl=rmisp.check_cert, tool="DDoSDB", debug=False)

    ddos = MISPObject(name="ddos")
    fpav = fp['attack_vector'][0]
    if "src_ips" in fpav:
        # ddos.add_attributes("ip-src", *[srcip for srcip in fpav["src_ips"]])
        ddos.add_attributes("ip-src", *[srcip for srcip in fpav["src_ips"][0:10]])
        # ddos.add_attributes("ip-src", *[srcip for index, srcip in zip(range(10), fpav["src_ips"])])
        # ddos.add_attribute("ip-src", fpav["src_ips"][0], comment=','.join(fpav["src_ips"][0:4000]))
    if "dst_ips" in fpav:
        ddos.add_attributes("ip-dst", *[dstip for dstip in fpav["dst_ips"]])
    if "srcport" in fpav:
        ddos.add_attribute("src-port", *[srcport for srcport in fpav["srcport"]])
    if "start_time" in fp:
        ddos.add_attribute("first-seen", fp["start_time"])
    if "ip_proto" in fpav:
        ddos.add_attribute("protocol", fpav["ip_proto"][0])
    if "comment" in fp and len(fp["comment"]) > 0:
        ddos.add_attribute("text", fp["comment"])
    if "avg_bps" in fp:
        ddos.add_attribute("total-bps", fp["avg_bps"])
    if "avg_pps" in fp:
        ddos.add_attribute("total-pps", fp["avg_pps"])

    # Create the DDoSCH tag (returns existing one if already present)
    tag = add_misp_tag(rmisp, 'DDoSCH', '#ed28c2')
    logger.debug(tag)

    # Create an event to link everything to
    logger.info("Creating a new event")
    new_event = MISPEvent()
    new_event.info = fp['key']
    # pprint(new_event.to_dict())
    new_event = misp.add_event(new_event, pythonify=True)
    # pprint(new_event.to_dict())

    # pprint(demjson.decode(ddos.to_json()))
    logger.info("Adding object to the event")
    misp.add_object(new_event.id, ddos)
    result = add_misp_tag_to_event(rmisp, new_event.id, tag['Tag']['id'])
    logger.debug(result)
    logger.info("That took {} seconds".format(time.time()-start))

