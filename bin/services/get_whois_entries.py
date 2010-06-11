#!/usr/bin/python
# -*- coding: utf-8 -*-
# Inspired by : http://gitorious.org/forban/forban/blobs/master/bin/forbanctl

import os 
import sys
import ConfigParser
config = ConfigParser.RawConfigParser()
config.read("../../etc/bgp-ranking.conf")
root_dir = config.get('global','root')
sys.path.append(os.path.join(root_dir,config.get('global','lib')))
services_dir = os.path.join(root_dir,config.get('global','services'))
sleep_timer = int(config.get('global','sleep_timer_short'))

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=os.path.join(root_dir,config.get('logging','log_get_whois_entries')))

from helpers.initscript import *
from db_models.ranking import *
import time

"""
Start the getting processes on an interval of entry to process: 
use *a way* less memory and is multithreaded 
"""

service = os.path.join(services_dir, "get_range_whois_entries")
pids = []

ip_counter = init_counter(IPsDescriptions.query.filter(IPsDescriptions.whois==None).count())
while 1:
    print "Start getting whois entries..."
    logging.info("Start getting whois entries...")
    while ip_counter['total_ips'] > 0:
        while len(pids) < ip_counter['processes'] :
            option = str(ip_counter['min']) + ' ' + str(ip_counter['max'])
            print('Starting interval: '+ option + '. Total ips: ' + str(ip_counter['total_ips']))
            logging.info('Starting interval: '+ option + '. Total ips: ' + str(ip_counter['total_ips']))
            pids.append(service_start(servicename = service, param = option))
            ip_counter['min'] = ip_counter['max'] +1
            ip_counter['max'] += ip_counter['interval']
        while len(pids) == ip_counter['processes']:
            time.sleep(sleep_timer)
            pids = update_running_pids(pids)
        ip_counter = init_counter(IPsDescriptions.query.filter(IPsDescriptions.whois==None).count())
    time.sleep(sleep_timer)
