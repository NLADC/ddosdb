import traceback
import logging
import requests
import urllib3
from pymisp import ExpandedPyMISP, MISPEvent, MISPObject
import json
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

    # Maximum number of source IPs to include
    # 0 means all (no limit)
    source_ips_limit = 1

    # Possible dicts in each attack_vector of the fingerprint
    # that will be added as comments (with the dict as value) to the event (not the ddos objects)
    attack_vector_dicts = [
        'ttl',
        'tcp_flags',
        'fragmentation_offset',
        'ethernet_type',
        'frame_len',
        'dns_query_name',
        'dns_query_type',
        'ICMP type',
        'ntp_requestcode',
        'http_uri',
        'http_method',
        'http_user_agent',
    ]

    # Possible fields in each attack_vector of the fingerprint
    # that will be added as comments to the event (not the ddos objects)
    attack_vector_fields = [
        'service',
        'fraction_of_attack',
        'nr_flows',
        'nr_packets',
        'nr_megabytes',
        'time_start',
        'duration_seconds',
    ]

    # Possible fields in the fingerprint
    # that will be added as comments to the event
    fingerprint_fields = [
        'time_start',
        'time_end',
        'duration_seconds',
        'total_flows',
        'total_megabytes',
        'total_packets',
        'total_ips',
        'avg_bps',
        'avg_pps',
        'avg_Bpp',
    ]

    try:
        misp = ExpandedPyMISP(rmisp.url, rmisp.authkey, ssl=rmisp.check_cert, tool="DDoSDB", debug=False)

        # Create the DDoSCH tag (returns existing one if already present)
        ddosch_tag = add_misp_tag(rmisp, 'DDoSCH', '#ff7dfd')
        logger.debug(ddosch_tag)

        # Create an event to link everything to
        logger.info("Creating a new event")
        event = MISPEvent()
        event.info = fp['key']

        # TARGET
        event.add_attribute(category='Network activity', type='ip-dst', value=fp['target'], comment='target')
        # KEY
        event.add_attribute(category='Network activity', type='md5', value=fp['key'], comment='attack key')

        for fp_field in fingerprint_fields:
            if fp_field in fp:
                event.add_attribute(category='Network activity',
                                    type='comment',
                                    value=fp[fp_field],
                                    comment=fp_field)

        # TAGS
        if 'tags' in fp:
            for tag in fp['tags']:
                event.add_tag(tag=tag)
        event.add_tag(tag='validated')

        # ATTACK VECTORS
        for attack_vector, i in zip(fp['attack_vectors'], range(len(fp['attack_vectors']))):
            ddos = MISPObject(name="ddos")
            # ATTACK VECTOR PROTOCOL
            ddos.add_attribute('protocol',
                               attack_vector['protocol'],
                               comment=f'vector {i}')

            for av_dict in attack_vector_dicts:
                if av_dict in attack_vector and type(attack_vector[av_dict]) == dict:
                    logger.info(f'Adding {av_dict}')
                    event.add_attribute(category='Network activity', type='comment',
                                        value=json.dumps(attack_vector[av_dict]),
                                        comment=f'vector {i} {av_dict} ({av_dict}:fraction)')

            for av_field in attack_vector_fields:
                if av_field in attack_vector and attack_vector[av_field]:
                    logger.info(f'Adding {av_field}')
                    event.add_attribute(category='Network activity', type='comment',
                                        value=attack_vector[av_field],
                                        comment=f'vector {i} {av_field}')

            # ATTACK VECTOR SOURCE_PORT
            if type(attack_vector['source_port']) == int:
                logger.info('Adding source ports')
                ddos.add_attribute('src-port', attack_vector['source_port'], comment='src-port')

            # ATTACK VECTOR DESTINATION PORTS
            if type(attack_vector['destination_ports']) == dict:
                logger.info('Adding destination ports')
                for port in attack_vector['destination_ports'].keys():
                    ddos.add_attribute('dst-port', int(port),
                                       comment='fraction={}'.format(attack_vector['destination_ports'][port]))

            # ATTACK VECTOR DNS
            if 'dns_query_name' in attack_vector or 'dns_query_type' in attack_vector:
                ddos.add_attribute('type', 'dns', comment='type of attack vector')
                ddos.add_attribute('type', 'dns-amplification', comment='type of attack vector')

            # ATTACK VECTOR ICMP
            if 'ICMP type' in attack_vector:
                ddos.add_attribute('type', 'icmp', comment='type of attack vector')

            # ATTACK VECTOR NTP
            if 'ntp_requestcode' in attack_vector:
                ddos.add_attribute('type', 'ntp-amplification', comment='type of attack vector')

            # ATTACK VECTOR SOURCE IPS
            if 'source_ips' in attack_vector and source_ips_limit > 0:
                for src_ip, i in zip(attack_vector['source_ips'], range(len(attack_vector['source_ips']))):
                    ddos.add_attribute('ip-src', src_ip, comment='source IP list truncated')
                    if i >= source_ips_limit-1:
                        break

            event.add_object(ddos, pythonify=True)

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
