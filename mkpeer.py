#!/usr/bin/env python

import requests
from requests.auth import HTTPBasicAuth
import os
from ruamel import yaml
import argparse

PEERINGDB_USERNAME = os.environ.get('PEERINGDB_USERNAME')
PEERINGDB_PASSWORD = os.environ.get('PEERINGDB_PASSWORD')


config = yaml.load(open('config.yaml'), Loader=yaml.Loader)
self_asn = str(config['self_asn'])
ixp = dict()
ixp_id = dict()
possible_peers = []
ixp_choices = []
noc_email = ''
new_data = dict()
pdata = dict()

for ixp_shortname in config['ixps']:
    ixp_choices.append(ixp_shortname)
parser = argparse.ArgumentParser(description='Query PeeringDB for peer BGP config')
parser.add_argument('-i', '--ixp', choices=ixp_choices, help='restrict config for matching IXP (default: any found)')
parser.add_argument('-a', '--asn', metavar='ASN', nargs="+", action='append', help='peer ASN')
args = parser.parse_args()


# https://bitbucket.org/ruamel/yaml/issues/138/possible-to-dump-without-aliases
class MySD(yaml.SafeDumper):
    def ignore_aliases(self, _data):
        return True


def main():
    list_of_asns = []
    for peer_asn in args.asn:
        asns = [self_asn, peer_asn[0]]
        ixp_restrict = fetch_ixp_id(args.ixp)
        for asn in asns:  # populate pdata with all the json for each -a asn
            pdata[asn] = pdb(asn)
        try:
            for asn in peer_asn:
                asn = pdata[str(asn)]['data'][0]['asn']
        except IndexError:
            print("# Looks like an empty dataset, exiting")
            print("result: %s" % pdata[asn])
            exit(1)
        print_config(ixp_restrict, peer_asn)
        if new_data is None:
            break
        else:
            list_of_asns.append(new_data.copy())
    print yaml.dump(list_of_asns, Dumper=yaml.RoundTripDumper)

def print_config(ix, peer_asn):
    for asn in peer_asn:
        if self_asn not in asn:  # only work on the peer ASN, skip our own API json
            new_data['peer_as'] = asn
            new_data['name'] = pdata[asn]['data'][0]['name']
            max_prefixes_v4 = pdata[asn]['data'][0]['info_prefixes4']
            max_prefixes_v6 = pdata[asn]['data'][0]['info_prefixes6']
            for noc_role in pdata[asn]['data'][0]['poc_set']:
                if 'NOC' in noc_role['role'] and noc_role['email'] is not None:
                    new_data['contact'] = noc_role['email']
                    break
                elif 'Technical' in noc_role['role'] and noc_role['email'] is not None:
                    new_data['contact'] = noc_role['email']
                    break
                elif 'Policy' in noc_role['role'] and noc_role['email'] is not None:
                    new_data['contact'] = noc_role['email']
                    break
            new_data['inet'] = {}
            new_data['inet6'] = {}
            new_data['inet']['peer_ips'] = []
            new_data['inet6']['peer_ips'] = []
            try:
                for i in pdata[asn]['data'][0]['netixlan_set']:
                    if ix == i['ixlan_id']:  # Skip if ix is not in our shared list.
                        new_data['inet']['prefix-limit'] = max_prefixes_v4
                        new_data['inet']['peer_ips'].append(i['ipaddr4'])
                        new_data['inet6']['prefix-limit'] = max_prefixes_v6
                        new_data['inet6']['peer_ips'].append(i['ipaddr6'])
            # if there is no peerable neighbor - delete the whole inet/inet6 list
                        if i['ipaddr4'] is None:
                            del new_data['inet']
                        if i['ipaddr6'] is None:
                            del new_data['inet6']
            except UnboundLocalError:
                new_data.clear()
                return None


def get_facility_name(pdb, nettype):
    fac_set = []
    for item in pdb['data'][0][nettype]:
        fac_set.append(item['ixlan_id'])
    return fac_set


def get_facility_id(pdb, nettype):
    fac_set = []
    for item in pdb['data'][0][nettype]:
        fac_set.append(item['ixlan_id'])
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


def fetch_ixp_id(ixp_name):
    try:
        ixp_restrict = config['ixps'][str(ixp_name)]['pdb_id']
        return ixp_restrict
    except:
        return None


if __name__ == "__main__":
    main()
