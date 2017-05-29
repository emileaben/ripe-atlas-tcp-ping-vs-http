#!/usr/bin/env python
import sys
import requests
import arrow
import json
import numpy as np
import argparse
from ripe.atlas.cousteau import ( AtlasResultsRequest, Measurement )

'''
{"original": {"af": 4, "target_asn": 43996, "creation_time": 1441631541, "probes_requested": 201, "result": "https://atlas.ripe.net/api/v2/measurements/2394116/results", "id": 2394116, "size": 48, "group": "https://atlas.ripe.net/api/v2/measurements/groups/2394116", "packet_interval": null, "spread": null, "stop_time": null, "resolve_on_probe": false, "type": "ping", "status": {"id": 2, "name": "Ongoing"}, "is_all_scheduled": true, "description": "Anchoring Measurement: Ping IPv4 for anchor us-abn-as43996.anchors.atlas.ripe.net", "participant_count": 511, "start_time": 1441631541, "in_wifi_group": false, "target_ip": "185.28.222.65", "is_public": true, "is_oneoff": false, "target": "us-abn-as43996.anchors.atlas.ripe.net", "resolved_ips": ["185.28.222.65"], "interval": 240, "packets": 3, "probes_scheduled": 511, "group_id": 2394116}, "response": {"measurements": [7817006]}}
'''

'''
{u'lts': 8, u'size': 48, u'group_id': 7817006, u'from': u'62.255.85.253', u'dst_name': u'185.28.222.65', u'fw': 4740, u'proto': u'TCP', u'af': 4, u'msm_name': u'Traceroute', u'prb_id': 4961, u'result': [{u'result': [{u'from': u'185.28.222.65', u'hdropts': [{u'mss': 1460}], u'rtt': 109.217, u'flags': u'SA', u'ttl': 47, u'size': 4}, {u'from': u'185.28.222.65', u'hdropts': [{u'mss': 1460}], u'rtt': 109.074, u'flags': u'SA', u'ttl': 47, u'size': 4}, {u'from': u'185.28.222.65', u'hdropts': [{u'mss': 1460}], u'rtt': 109.081, u'flags': u'SA', u'ttl': 47, u'size': 4}], u'hop': 255}], u'timestamp': 1487146332, u'src_addr': u'10.10.250.210', u'paris_id': 9, u'endtime': 1487146332, u'type': u'traceroute', u'dst_addr': u'185.28.222.65', u'msm_id': 7817006}
'''
def get_tcp_stats( msm_id, start, stop, res ):
   # not doing anything with start/stop
   print >>sys.stderr, "loading msm: %s" % msm_id
   is_success, results = AtlasResultsRequest(msm_id=msm_id).create()
   print >>sys.stderr, "loaded msm: %s (result:%s, entries:%s)" % (msm_id,is_success, len(results))
   if is_success:
      for r in results:
         try:
            prb = r['prb_id'] 
            res.setdefault( prb , {'tcp': []} )
            for rr in r['result']:
               if 'result' in rr:
                  for rrr in rr['result']:
                     if 'rtt' in rrr:
                        res[ prb ]['tcp'].append( rrr['rtt'] )
                        #print rrr
                     else:
                        res[ prb ]['tcp'].append( None )
                        #print rrr
               else:
                  # u'result': [{u'hop': 255, u'error': u'connect failed: Network is unreachable'}]
                  res[ prb ]['tcp'].append( None )
         except:
            print >>sys.stderr, "err> %s" % r
   else:
         print >>sys.stderr, "fetch failure"

'''
{u'af': 4, u'prb_id': 10222, u'result': [{u'rtt': 120.54012}, {u'rtt': 120.3295}, {u'rtt': 120.302505}], u'ttl': 49, u'avg': 120.3907083333, u'size': 48, u'from': u'89.176.252.58', u'proto': u'ICMP', u'timestamp': 1487136630, u'dup': 0, u'type': u'ping', u'sent': 3, u'msm_id': 2394116, u'fw': 4740, u'max': 120.54012, u'step': 240, u'src_addr': u'192.168.11.41', u'rcvd': 3, u'msm_name': u'Ping', u'lts': 64, u'dst_name': u'185.28.222.65', u'min': 120.302505, u'group_id': 2394116, u'dst_addr': u'185.28.222.65'}
'''

def get_icmp_stats( msm_id, start, stop, res ):
   # find start and end time
   kwargs = {
      "msm_id": msm_id,
      "start": start,
      "stop": stop
   }
   print >>sys.stderr, "loading msm: %s (args: %s)" % (msm_id, kwargs)
   is_success, results = AtlasResultsRequest(**kwargs).create()
   print >>sys.stderr, "loaded msm: %s (result:%s, entries:%s)" % (msm_id,is_success, len(results))
   if is_success:
      for r in results:
         try:
            prb = r['prb_id'] 
            res.setdefault( prb , {'icmp': []} )
            res[prb].setdefault( 'icmp', [] )
            for rr in r['result']:
               if 'rtt' in rr:
                  res[ prb ]['icmp'].append( rr['rtt'] )
               else:
                  res[ prb ]['icmp'].append( None )
         except:
            print >>sys.stderr, "err> %s" % r
   else:
         print >>sys.stderr, "fetch failure"

def main():
   parser = argparse.ArgumentParser()
   parser.add_argument('inputfile',help="file with Atlas measurement results")
   args = parser.parse_args() 
   print "#prb dst af tcp10 icmp10 diff tcpvalcount icmpvalcount tcpcount icmpcount"
   with open( args.inputfile ) as inf:
      for line in inf:
         d = json.loads( line )
         if 'response' in d:
            if 'measurements' in d['response']:
               if len( d['response']['measurements'] ) == 1:
                  ## OK we had success, now record the original msm
                  dst=d['original']['target']
                  af=d['original']['af']
                  tcp_msm_id = d['response']['measurements'][0]
                  icmp_msm_id = d['original']['id']
                  # load measurement data
                  tmeta = Measurement( id=tcp_msm_id )
                  imeta = Measurement( id=icmp_msm_id )
                  print >>sys.stderr, "tcp:%s icmp:%s" %  ( tcp_msm_id, icmp_msm_id )
                  res = {}
                  get_tcp_stats( tcp_msm_id, d['start'], d['stop'], res )
                  #print res
                  get_icmp_stats( icmp_msm_id, d['start'], d['stop'], res )
                  #print res
                  for prb,info in res.iteritems():
                     if 'tcp' in info and 'icmp' in info:
                        tvals = filter(lambda x: x != None, info['tcp'] )
                        ivals = filter(lambda x: x != None, info['icmp'] )
                        tcp10 = None
                        icmp10 = None
                        if len( tvals ) > 0:
                           tcp10 = np.percentile( tvals, 10 )
                        if len( ivals ) > 0:
                           icmp10 = np.percentile( ivals, 10 )
                        diff=None
                        if icmp10 != None and tcp10 != None:
                           diff = 100.0*(tcp10-icmp10)/min(tcp10,icmp10)
                           ## tcp=10ms  icmp=20ms  ->   (10-20)/10 = -100%  <- minus = tcp is faster
                           ## tcp=20ms  icmp=10ms  ->   (20-10)/10 = +100%  <- plus  = icmp is faster
                        print "%s %s %s %s %s %s %s %s %s %s" % ( prb, dst, af, tcp10, icmp10, diff, len( tvals ), len( ivals ), len( info['tcp'] ), len( info['icmp'] ) )
         print >>sys.stderr, "line done: %s" % ( line )
main()

'''
{u'af': 4, u'target_asn': 43996, u'creation_time': 1416218112, u'probes_requested': 145, u'result': u'https://atlas.ripe.net/api/v2/measurements/1790208/results', u'id': 1790208, u'size': 48, u'group': u'https://atlas.ripe.net/api/v2/measurements/groups/1790208', u'packet_interval': None, u'spread': None, u'stop_time': None, u'resolve_on_probe': False, u'type': u'ping', u'status': {u'id': 2, u'name': u'Ongoing'}, u'is_all_scheduled': True, u'description': u'Anchoring Measurement: Ping IPv4 for anchor uk-slo-as43996.anchors.atlas.ripe.net', u'participant_count': 552, u'start_time': 1416218112, u'in_wifi_group': False, u'target_ip': u'5.57.16.65', u'is_public': True, u'is_oneoff': False, u'target': u'uk-slo-as43996.anchors.atlas.ripe.net', u'resolved_ips': [u'5.57.16.65'], u'interval': 240, u'packets': 3, u'probes_scheduled': 552, u'group_id': 1790208}
'''
