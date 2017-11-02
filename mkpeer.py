#!/usr/bin/env python

import requests
from requests.auth import HTTPBasicAuth
import sys
import os
import yaml

PEERINGDB_USERNAME = os.environ.get('PEERINGDB_USERNAME', 'githubops')
PEERINGDB_PASSWORD = os.environ.get('PEERINGDB_PASSWORD')

CONFIG = 'config.yaml'

config = yaml.load(open(CONFIG))


def override_email(asn):
    try:
        noc_email = config['asn_overrides'][int(asn)]['noc_email']
        return noc_email
    except:
        return None


def main():

    self_asn = '36459'
    asns = [self_asn, sys.argv[1]]
    pdata = dict()
    print("# Fetching PeeringDB info")
    for asn in asns:
        pdata[asn] = pdb(asn)

    try:
        for asn in pdata.keys():
            asn = pdata[str(asn)]['data'][0]['asn']
    except IndexError:
        print("# Looks like an empty dataset, exiting")
        print("result: %s" % pdata[asn])
        exit(1)

    # Dump all our ix names into a list
    ixp = dict()
    for asn in pdata.keys():
        ixp[asn] = get_facility(pdata[str(asn)], "netixlan_set")

# For all our IXs, see if they have the same IX
# Have to seed the common ix list with the first entry

    common_ix_list = ixp[list(ixp)[0]]
    for asn in ixp:
        common_ix_list = list(set(ixp[asn]).intersection(common_ix_list))

    if len(common_ix_list) < 1:
        print("# Didnt find any common IX, exiting...")
        exit(1)
    possible_peers = []
    for asn in pdata.keys():
        possible_peers.append(pdata[asn]['data'][0]['name'])
    print '# ' + possible_peers[0] + ' can peer with ' + possible_peers[1] + '!'

    for ix in common_ix_list:
        print "# " + ix
        for asn in pdata.keys():
            if self_asn not in asn:  # only work on the peer ASN, skip our own API json
                noc_email = override_email(asn)
                max_prefixes_v4 = pdata[asn]['data'][0]['info_prefixes4']
                for noc_role in pdata[asn]['data'][0]['poc_set']:
                    if 'NOC' in noc_role['role']:
                        noc_email = noc_role['email']
                    elif 'Technical' in noc_role['role']:
                        noc_email = noc_role['email']
                for i in pdata[asn]['data'][0]['netixlan_set']:
                    if i['name'] not in common_ix_list:
                        continue
                    if ix == i['name']:
                        # Skip if ix is not in our shared list.
                        for entry in ['ix']:
                            v4 = i['ipaddr4']
                            print "set protocols bgp group IX-PEERS-V4 neighbor %s peer-as %s" % (v4, i['asn'])
                            print "set protocols bgp group IX-PEERS-V4 neighbor %s description \"%s:%s:AS%s\"" \
                                  % (v4, noc_email, possible_peers[0], i['asn'])
                            print "set protocols bgp group IX-PEERS-V4 neighbor %s family inet unicast prefix-limit maximum %s" \
                                  % (v4, max_prefixes_v4)


def get_facility(pdb, nettype):
    fac_set = []
    for item in pdb['data'][0][nettype]:
        fac_set.append(item['name'])
    return fac_set


def pdb(ASN):
    HTTP_OK = 200
    pdb_url = 'https://api.peeringdb.com/api/net?asn__in=%s&depth=2' % ASN
    r = requests.get(pdb_url, auth=HTTPBasicAuth(PEERINGDB_USERNAME, PEERINGDB_PASSWORD))
    if r.status_code != HTTP_OK:
        print("Got unexpected status code, exiting")
        print("%s - %s" % (r.status, r.text))
        exit(1)
    pdb_res = r.json()
    return pdb_res


if __name__ == "__main__":
    main()
