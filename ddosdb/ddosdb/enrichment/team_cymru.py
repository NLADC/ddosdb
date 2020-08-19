import nclib


class TeamCymru(object):
    fingerprint = {}

    def __init__(self, fingerprint):
        # This is the fingerprint from the JSON input file
        self.fingerprint = fingerprint

    def parse(self):
        nc = nclib.Netcat(("whois.cymru.com", 43))
        nc.send("begin\n".encode("utf-8"))
        nc.send("verbose\n".encode("utf-8"))
        for ip in self.fingerprint["src_ips"]:
            nc.send((str(ip) + " " + self.fingerprint["start_time"] + "\n").encode("utf-8"))
        nc.send("end\n".encode("utf-8"))

        data = nc.recv_all().decode()
        print(data)
        lines = data.split("\n")
        # Remove the first line where it says "Bulk mode; ..."
        lines.pop(0)

        parsed = []
        for line in lines:
            if not line:
                continue
            # Example line:
            # 1133    | 130.89.25.25 | 130.89.0.0/16 | NL | ripencc  | 1991-04-12 | UTWENTE-AS University Twente, NL
            split_line = line.split("|")
            pa_line = {}

            pal_as = split_line[0].strip()
            pal_ip = split_line[1].strip()
            pal_cc = split_line[3].strip()

            pa_line["ip"] = pal_ip
            if pal_as != "NA":
                pa_line["as"] = pal_as
                pa_line["cc"] = pal_cc
            parsed.append(pa_line)
#            parsed.append({
#                "as": split_line[0].strip(),
#                "ip": split_line[1].strip(),
                # "bgp_prefix": split_line[2].strip(),
#                "cc": split_line[3].strip(),
                # "registry": split_line[4].strip(),
                # "allocated": split_line[5].strip(),
                # "as_name": split_line[6].strip()
#            })

        self.fingerprint["src_ips"] = parsed
        print(self.fingerprint["src_ips"])
        return self.fingerprint
