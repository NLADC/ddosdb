import os

import requests


def upload(pcap, fingerprint, username, password, key):
    """
    Upload a fingerprint and attack vector to DDoSDB
    :param pcap: Path to the pcap file
    :param fingerprint: Path to the fingerprint file
    :param username: DDoSDB username
    :param password: DDoSDB password
    :param key: ID to identify this attack, also the filename of the pcap_file.
    :return:
    """
    files = {
        "json": open(fingerprint, "rb"),
        "pcap": open(pcap, "rb")
    }
    headers = {
        "X-Username": username,
        "X-Password": password,
        "X-Filename": key
    }
    ddosdb_url = "http://127.0.0.1/"
    r = requests.post(ddosdb_url+"upload-file", files=files, headers=headers)

    return r.status_code

if __name__ == "__main__":
    path = "/some/path/"
    username = ""
    password = ""

    files = os.listdir(path)
    files = [x for x in files if x.endsWith(".json")]
    for file in files:
        json = path + file
        pcap = path + file.replace(".json", ".pcap")
        key = file.replace(".json", "")
        upload(pcap, json, username, password, key)