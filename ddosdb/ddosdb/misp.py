import traceback
import logging
import requests
import urllib3
from pymisp import ExpandedPyMISP, MISPEvent, MISPObject, MISPAttribute, MISPTag
import demjson
import time

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

    try:
        misp = ExpandedPyMISP(rmisp.url, rmisp.authkey, ssl=rmisp.check_cert, tool="DDoSDB", debug=False)

        # Create the DDoSCH tag (returns existing one if already present)
        ddosch_tag = add_misp_tag(rmisp, 'DDoSCH', '#ff7dfd')
        logger.debug(ddosch_tag)

        # Create an event to link everything to
        logger.info("Creating a new event")
        event = MISPEvent()
        event.info = fp['key']

        # ATTACK VECTORS
        for attack_vector, i in zip(fp['attack_vectors'], range(len(fp['attack_vectors']))):
            ddos = MISPObject(name="ddos")
            # ATTACK VECTOR PROTOCOL
            ddos.add_attribute('protocol',
                               attack_vector['protocol'],
                               comment=f'vector {i}')

            # ATTACK VECTOR SERVICE
            event.add_attribute(category='Network activity', type='comment', value=attack_vector['service'],
                                comment=f'vector {i} service')

            # ATTACK VECTOR SOURCE_PORT
            if type(attack_vector['source_port']) == int:
                logger.info('Adding source ports')
                ddos.add_attribute('src-port', attack_vector['source_port'], comment='src-port')

            # ATTACK VECTOR FRACTION OF ATTACK
            if type(attack_vector['fraction_of_attack']) == float:
                event.add_attribute(category='Network activity',
                                    type='comment',
                                    value=attack_vector['fraction_of_attack'],
                                    comment=f'vector {i} fraction_of_attack')

            # ATTACK VECTOR DESTINATION PORTS
            if type(attack_vector['destination_ports']) == dict:
                logger.info('Adding destination ports')
                for port in attack_vector['destination_ports'].keys():
                    ddos.add_attribute('dst-port', int(port),
                                       comment='fraction={}'.format(attack_vector['destination_ports'][port]))

            # ATTACK VECTOR TCP FLAGS
            if type(attack_vector['tcp_flags']) == dict:
                logger.info('Adding TCP flags')
                event.add_attribute(category='Network activity', type='comment',
                                    value=demjson.encode(attack_vector['tcp_flags']),
                                    comment=f'vector {i} TCP flags (flags:fraction)')

            # ATTACK VECTOR NR FLOWS
            event.add_attribute(category='Network activity', type='comment',
                                value=attack_vector['nr_flows'], comment=f'vector {i} nr_flows')

            # ATTACK VECTOR NR PACKETS
            event.add_attribute(category='Network activity', type='comment',
                                value=attack_vector['nr_packets'], comment=f'vector {i} nr_packets')

            # ATTACK VECTOR NR MEGABYTES
            event.add_attribute(category='Network activity', type='comment',
                                value=attack_vector['nr_megabytes'], comment=f'vector {i} nr_megabytes')

            # ATTACK VECTOR TIME START
            event.add_attribute(category='Network activity', type='comment',
                                value=attack_vector['time_start'], comment=f'vector {i} time_start')

            # ATTACK VECTOR DURATION SECONDS
            event.add_attribute(category='Network activity', type='comment',
                                value=attack_vector['duration_seconds'], comment=f'vector {i} duration_seconds')

            # ATTACK VECTOR SOURCE IPS
            # Also for this: this convenience method does not seem to work
            # ddos.add_attributes('ip-src', attack_vector['source_ips'])
            if 'source_ips' in attack_vector:
                for src_ip, i in zip(attack_vector['source_ips'], range(len(attack_vector['source_ips']))):
                    ddos.add_attribute('ip-src', src_ip, comment='source IP list truncated')
                    if i >= 0:
                        break

            event.add_object(ddos, pythonify=True)

        # TARGET
        event.add_attribute(category='Network activity', type='ip-dst', value=fp['target'], comment='target')
        # KEY
        event.add_attribute(category='Network activity', type='md5', value=fp['key'], comment='attack key')
        # TIME START
        event.add_attribute(category='Network activity', type='comment', value=fp['time_start'],
                            comment='attack time_start')
        # DURATION SECONDS
        event.add_attribute(category='Network activity', type='comment', value=fp['duration_seconds'],
                            comment='attack duration_seconds')
        # TOTAL FLOWS
        event.add_attribute(category='Network activity', type='comment', value=fp['total_flows'], comment='total_flows')
        # TOTAL MEGABYTES
        event.add_attribute(category='Network activity', type='comment', value=fp['total_megabytes'],
                            comment='total_megabytes')
        # TOTAL PACKETS
        event.add_attribute(category='Network activity', type='comment', value=fp['total_packets'],
                            comment='total_packets')
        # TOTAL IPS
        event.add_attribute(category='Network activity', type='comment', value=fp['total_ips'], comment='total_ips')
        # AVG BPS
        event.add_attribute(category='Network activity', type='comment', value=fp['avg_bps'], comment='avg_bps')
        # AVG PPS
        event.add_attribute(category='Network activity', type='comment', value=fp['avg_pps'], comment='avg_pps')
        # AVG BPP
        event.add_attribute(category='Network activity', type='comment', value=fp['avg_Bpp'], comment='avg_Bpp')

        # TAGS
        for tag in fp['tags']:
            event.add_tag(tag=tag)
        event.add_tag(tag='validated')

        event.publish()
        # event = misp.add_event(event, pythonify=True)
        event = misp.add_event(event, pythonify=True)

        result = add_misp_tag_to_event(rmisp, event.id, ddosch_tag['Tag']['id'])
        logger.debug(result)
        logger.info("That took {} seconds".format(time.time() - start))
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        raise
