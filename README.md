# DDoS Clearing House.

DDoSCH is a platform used to share DDoS fingerprints. The system is composed by a set of software modules available in this repository and described in our research  [paper](https://research.utwente.nl/en/publications/ddos-as-a-service-investigating-booter-websites](https://research.utwente.nl/en/publications/ddos-as-a-service-investigating-booter-websites)). 

- [DDoSDB](https://github.com/ddos-clearing-house/ddosdb):  this is the backend database and grafical interface used to share the fingerprints.
- [Dissector](https://github.com/ddos-clearing-house/ddos_dissector]):  responsible for summarizing the DDoS traffic and generate the proper fingerprint.
- [Converters](https://github.com/ddos-clearing-house/ddos_fingerprint_converters]):  translate fingerprints to mitigation rules.
