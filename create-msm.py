#!/usr/bin/env python
import time
import sys
import requests
import arrow
import json
from ripe.atlas.cousteau import ( Traceroute, Http, AtlasCreateRequest, AtlasSource, ProbeRequest )

ATLAS_API_KEY=None
with open('/users/emile/.atlas/auth') as inf:
   ATLAS_API_KEY=inf.readline()
   ATLAS_API_KEY=ATLAS_API_KEY.rstrip('\n')

msms = set()

def process( d ):
   results = d['results']
   for r in results:
      if r['type'] == 'ping':
         msm_string = r['measurement']
         msm_string_parts = msm_string.split('/')
         msm_id = int( msm_string_parts[-1] )
         msms.add( msm_id )

def get_done_msms( fname ):
   done = set()
   with open(fname) as inf:
      for line in inf:
         d = json.loads( line )
         if 'response' in d:
            if 'measurements' in d['response']:
               if len( d['response']['measurements'] ) > 0:
                  ## OK we had success, now record the original msm
                  done.add( d['original']['id'] )
   return done
         
'''
{"original": {"af": 4, "target_asn": 43996, "creation_time": 1441631541, "probes_requested": 201, "result": "https://atlas.ripe.net/api/v2/measurements/2394116/results", "id": 2394116, "size": 48, "group": "https://atlas.ripe.net/api/v2/measurements/groups/2394116", "packet_interval": null, "spread": null, "stop_time": null, "resolve_on_probe": false, "type": "ping", "status": {"id": 2, "name": "Ongoing"}, "is_all_scheduled": true, "description": "Anchoring Measurement: Ping IPv4 for anchor us-abn-as43996.anchors.atlas.ripe.net", "participant_count": 511, "start_time": 1441631541, "in_wifi_group": false, "target_ip": "185.28.222.65", "is_public": true, "is_oneoff": false, "target": "us-abn-as43996.anchors.atlas.ripe.net", "resolved_ips": ["185.28.222.65"], "interval": 240, "packets": 3, "probes_scheduled": 511, "group_id": 2394116}, "response": {"measurements": [7817006]}}
'''

IV=600

def main():
   done_msms = get_done_msms( sys.argv[1] )
   #start_url = "https://atlas.ripe.net:443/api/v2/anchor-measurements/"
   start_url = "https://atlas.ripe.net:443/api/v2/anchor-measurements/"
   d = requests.get( start_url ).json()
   process( d )
   while d['next'] != None:
      d = requests.get( d['next'] ).json()
      process( d )
   for msm in msms:
      if msm in done_msms:
         print >>sys.stderr, "already have a matching msm for original %s, skipping" % ( msm )
         continue
      ## fetch measurement metadata
      meta = requests.get( "https://atlas.ripe.net/api/v2/measurements/{pk}/".format(pk=msm) ).json()
      if meta['type'] != 'ping':
         continue
      spec = {}
      spec['af'] = meta['af']
      spec['dst_name'] = meta['target']
      spec['dst_ip'] = meta['target_ip']
      iv = IV
      ## make it staggered with the original
      o_start_mod_offset = meta['start_time'] % iv
      # start_this_slot + slot + half_slot + original offset
      start = int( arrow.utcnow().timestamp / iv ) * iv + iv + iv/2 + o_start_mod_offset
      stop  = start + 3600*24
   
      tcpping_msm_spec = Traceroute(
         description="campaign:compare_tcp_http sub:tcp_ping dst:%s" % spec['dst_name'],
         af=spec['af'],
         target=spec['dst_ip'],
         protocol='TCP',
         size=0, ## otherwise this is a SYN with data!
         first_hop=255,
         max_hops=255,
         port=80,
         interval = iv
      )
      http_msm_spec = Http(
         description="campaign:compare_tcp_http sub:http dst:%s" % spec['dst_name'],
         af=spec['af'],
         target=spec['dst_name'],
         extended_timing=True,
         interval = iv
      )

      source = AtlasSource(
         type="msm",
         value=msm,
         requested=-1,
      )
      atlas_request = AtlasCreateRequest(
         start_time=start,
         stop_time=stop,
         key=ATLAS_API_KEY,
         measurements=[tcpping_msm_spec,http_msm_spec],
         sources=[source],
      )

      (is_success, response) = atlas_request.create()
      d = {
         'spec': spec,
         'response': response,
         'start': start,
         'stop': stop
      }
      print json.dumps( d )
      time.sleep(5)

main()

'''
{u'af': 4, u'target_asn': 43996, u'creation_time': 1416218112, u'probes_requested': 145, u'result': u'https://atlas.ripe.net/api/v2/measurements/1790208/results', u'id': 1790208, u'size': 48, u'group': u'https://atlas.ripe.net/api/v2/measurements/groups/1790208', u'packet_interval': None, u'spread': None, u'stop_time': None, u'resolve_on_probe': False, u'type': u'ping', u'status': {u'id': 2, u'name': u'Ongoing'}, u'is_all_scheduled': True, u'description': u'Anchoring Measurement: Ping IPv4 for anchor uk-slo-as43996.anchors.atlas.ripe.net', u'participant_count': 552, u'start_time': 1416218112, u'in_wifi_group': False, u'target_ip': u'5.57.16.65', u'is_public': True, u'is_oneoff': False, u'target': u'uk-slo-as43996.anchors.atlas.ripe.net', u'resolved_ips': [u'5.57.16.65'], u'interval': 240, u'packets': 3, u'probes_scheduled': 552, u'group_id': 1790208}
'''
