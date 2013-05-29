#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import sqlite3
import os
from collections import defaultdict
os.environ['PYWIKIBOT2_DIR'] = '/home/notconfusing/workspace/WikidataVIAFbot_branch'
import pywikibot
import json
import urllib2
import time
import mwparserfromhell
import logging
logging.basicConfig(filename='logofcleanviafbot.log',level=logging.DEBUG)

en_wikipedia = pywikibot.Site('en', 'wikipedia')
wikidata = en_wikipedia.data_repository()

if not wikidata.logged_in(): wikidata.login()
if not en_wikipedia.logged_in(): en_wikipedia.login()


propertyMap = {'TYp': 'p107',
             'LCCN': 'p244',
             'VIAF':'p214',
             #'ORCID':, 
             'GND':'p227', 
             #'pND':, 
             #'SELIBR':, 
             #'GDK':, 
             #'GDK-V1':, 
             #'SWD':, 
             'BNF':'p268', 
             #'BpN':,
             #'RID':, 
             #'Scopus':, 
             #'BIBSYS':, 
             #'ULAN':,
             #'NDL':, 
             'SUDOC':'p269', 
             #'KID':, 
             #'WORLDCATID':
             'ISNI': 'p213',}
         
sourceMap = {'imported from':'P143',
             'en':'Q328',
             'de':'Q48183',
             'fr':'Q8447',
             'it':'Q11920',
             'xx':'Q423048',} #this is from isni, i couldn't think of a better two letter shortcode

gndMap = {'p': 'Q215627',
          'k': 'Q43229',
          'v': 'Q1656682',
          'w': 'Q386724',
          's': 'Q1969448',
          'g': 'Q618123',
          'n': 'Q4167410',}


violationsPage = pywikibot.Page(wikidata, 'Wikidata:Database reports/Constraint violations/P214')
violationsPage = violationsPage.get()
violationsCode = mwparserfromhell.parse(violationsPage)

#print violationsCode

violationsSections = violationsCode.get_sections()

for section in violationsSections:
    if section[:10] == '== "Format':
        totalRemoved = 0
        for ul in section.nodes:
            if ul.startswith('[[Q'):
                pagestr = str(ul)
                qid = pagestr.replace('[', '')
                qid = qid.replace(']', '')
                print qid
                
                pageToClean = pywikibot.ItemPage(wikidata, qid)
                pageToCleanParts = pageToClean.get()
                claimsToClean = pageToCleanParts['claims']
                hasVIAF = False
                for pid, clm in claimsToClean.iteritems():
                    if pid == propertyMap['VIAF']:
                        pageToClean.removeClaims(clm)
                        print 'removing ', clm, ' from ' , pageToCleanParts['aliases']
                        totalRemoved += 1
        print totalRemoved


print 'end'