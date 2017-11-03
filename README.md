# mkpeer

A script to be run by hand or from Ansible to automagically give you router config for peering requests.

`usage: mkpeer.py [-h] [-i {equinix_ashburn,six}] ASN`

Make sure to have `$PEERINGDB_USERNAME` and `$PEERINGDB_PASSWORD` set in your environment, or you can use email overrides to fill in the NOC contacts in the output.

Output is hard coded to junos set commands [right now](https://github.com/yeled/mkpeer/issues/2).

### TODO

 - [x] Figure out a way to only output the IXPs you are interested in.
       use a yaml dict to lookup ASNs in bulk, and match against a region or IXP?
 - [ ] Specify ASNs in bulk.
 - [ ] Switch for cli use vs Ansbile templates (set commands vs config replace: code?)
 - [ ] Make the config idempotent (diff clean) across multiple runs. Useful for updating prefix counts.

 ### License
 Based on MIT licensed https://github.com/rucarrol/PeerFinder/blob/master/peerfinder.py 
