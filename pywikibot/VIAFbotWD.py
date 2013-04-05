#!/usr/bin/python
# -*- coding: utf-8 -*-
import sqlite3
import os
from collections import defaultdict
os.environ['PYWIKIBOT2_DIR'] = '/home/kleinm/workspace/WikidataVIAFbot_branch'
import pywikibot
import json
import urllib2
import time
import mwparserfromhell

en_wikipedia = pywikibot.Site('en', 'wikipedia')
wikidata = en_wikipedia.data_repository()

if not wikidata.logged_in(): wikidata.login()
if not en_wikipedia.logged_in(): en_wikipedia.login()

try:
    positionsJSON = open('positions.JSON')
    positions = json.load(positionsJSON)
    positionsJSON.close()
except IOError:
    positions = {'prevtouched': 0, 'viafredirs': 0, 'isniadds': 0, 'claimadds':0, 'sourceadds':0}
    
def savePositions():
    positionsJSON = open('positions.JSON', 'w')
    json.dump(positions, positionsJSON, indent=4)
    positionsJSON.close()

propertyMap = {'TYP': 'P107',
             'LCCN': 'P244',
             'VIAF':'P214',
             #'ORCID':, 
             'GND':'P227', 
             #'PND':, 
             #'SELIBR':, 
             #'GDK':, 
             #'GDK-V1':, 
             #'SWD':, 
             'BNF':'P268', 
             #'BPN':,
             #'RID':, 
             #'Scopus':, 
             #'BIBSYS':, 
             #'ULAN':,
             #'NDL':, 
             'SUDOC':'P269', 
             #'KID':, 
             #'WORLDCATID':
             'ISNI': 'P213',}
         
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


remotePIDList = list()
for v in propertyMap.itervalues():
    remotePIDList.append(v)
    
langSiteDict =  {'en': pywikibot.Site('en','wikipedia'),
                 'de': pywikibot.Site('de','wikipedia'),
                 'fr': pywikibot.Site('fr','wikipedia'),
                 'it': pywikibot.Site('it','wikipedia'),
                 #'co': pywikibot.Site('en','commons')
                 }

langTemplateDict = {'en': 'Template:Authority control', 
                    'de': 'Vorlage:Normdaten', 
                    'fr': 'Modèle:Autorité',
                    'it': 'Template:Controllo di autorità',
                    #'co': 'Template:Authority control'
                    }

langTemplateShort= {'en': 'Authority control', 
                    'de': 'Normdaten', 
                    'fr': 'Autorité',
                    'it': 'Controllo di autorità',
                    #'co': 'Authority control'
                    }

#makes dictionary Page instances for each template
langPageDict = dict((l, 
                     pywikibot.Page(langSiteDict[l], langTemplateDict[l]) ) 
                    for l in langSiteDict) 

#makes a dictionary of languages along with an iterable over all their authortiy containing pages  
langAuthorityDict = dict((l, 
                          langPageDict[l].getReferences(follow_redirects=True, withTemplateInclusion=True,
                      onlyTemplateInclusion=True, redirectsOnly=False,
                      namespaces=None, step=None, total=None, content=False) ) 
                         for l in langTemplateDict)
    
def getRemoteClaims(qnum):
    remoteClaims = list()
    remoteClaimsWithSources = list()
    
    page = pywikibot.ItemPage(wikidata, qnum) #  this can be used for any page object
    page.get() #  you need to call it to access any data.
    claimObjs = page.claims
    
    #get all the right claims
    for claimID in claimObjs:
        claimlist = page.claims[claimID]
        for claim in claimlist:
            pid = claim.id.upper()
            if pid in remotePIDList:
                remoteClaims.append(claim)
            else:
                pass
    #then make it look like local
    #which is a list of my special types which are lists whose fisrst elements are claims, and whose secodn elements is a list of sources
    for remoteClaim in remoteClaims:
        remoteClaimsWithSources.append([remoteClaim, remoteClaim.sources])
    
    return remoteClaimsWithSources

def lccnNormalize(lccn):
    '''see http://www.loc.gov/marc/lccn-namespace.html'''
    returnstring = ''
    lccn = lccn.split('/')
    while (not (len(lccn[-1]) == 6)):
        lccn[-1] = '0' + lccn[-1]
    for i in lccn:
        returnstring += i
    return returnstring
        

def makeSourcedClaim(idValCluster):
    #what's the idtype were addng
    
    firstProperty = idValCluster[0] #there's guaranteed to be at least one
    idtyp = firstProperty['idtyp']
    idval = firstProperty['idval']
    if idtyp == 'PND':
        idtyp = 'GND'
    if idtyp == 'LCCN':
        idval = lccnNormalize(idval) #for normalizing purposes.
    claimObj = pywikibot.Claim(site=wikidata, pid=propertyMap[idtyp])
    #gnd needs to be converted
    if idtyp == 'TYP':
        idval = pywikibot.ItemPage(wikidata, gndMap[idval])

    
    claimObj.setTarget(idval)
    
    sourceObjList = list()
    #sources
    for property in idValCluster:
        lang = property['lang']
        sourceObj = pywikibot.Claim(site=wikidata, pid=sourceMap['imported from'])
        sourceObj.setTarget(pywikibot.ItemPage(wikidata, sourceMap[lang]))
        sourceObjList.append(sourceObj)
    
    #i wish python had a good Pair datatype, but alas a list whose first item is the claim object and whose second item is a list of sources whill have to do
    return [claimObj, sourceObjList]


    
def idValClusterer(idTypCluster):
    '''takes a list of property dicts which all have the same idtyp and returns a list of whose sublist all have the same idval'''
    idValClusters = list()
    buckets = defaultdict(list)
    for propertyDict in idTypCluster:
        buckets[propertyDict['idval']].append(propertyDict)
    
    for idval in buckets.iterkeys():
        idValClusters.append(buckets[idval])
    
    return idValClusters
    
def idTypClusterer(qnumCluster):
    '''takes a list of property dicts which all have the same qnum and returns a list of whose sublist all have the same idtyp'''
    idTypClusters = list()
    buckets = defaultdict(list)
    for propertyDict in qnumCluster:
        buckets[propertyDict['idtyp']].append(propertyDict)
    
    for idtyp in buckets.iterkeys():
        idTypClusters.append(buckets[idtyp])
    
    return idTypClusters
    
def propertiesToClaims(qnumCluster):
    '''takes a list of properties that all have the same qnums and returns a list of claims, who have the same idvals with sourced languages'''
    localClaimsList = list() #we're returning this
    
    idTypClusters = idTypClusterer(qnumCluster)
    for idTypCluster in idTypClusters:
        idValClusters = idValClusterer(idTypCluster)
        for idValCluster in idValClusters:
            sourcedClaim = makeSourcedClaim(idValCluster)
            localClaimsList.append(sourcedClaim)

    return localClaimsList

def addPair(page, localClaimWithSource):
    lc = localClaimWithSource[0]
    lsl = localClaimWithSource[1]
    
    page.addClaim(lc)
    positions['claimadds'] += 1
    
    for ls in lsl:
        lc.addSource(ls)
        positions['sourceadds'] += 1

def claimMatch(lc, rc):
    if (lc.id == rc.id) and (lc.target == rc.target):
        return True
    return False

def sourceMatch(ls, rsl):
    for rs in rsl:
        if (ls.id == rs.id) and (ls.target == rs.target):
            return True
    
    return False

def writeACluster2(qnumCluster):
    qnum = qnumCluster[0]['qnum'] #any elemnt of qnumClusterList should have the same qnum
    page = pywikibot.ItemPage(wikidata, qnum)
    
    localClaimsWithSources = propertiesToClaims(qnumCluster)  
    remoteClaimsWithSources = getRemoteClaims(qnum)
    
    for lcs in localClaimsWithSources:
        lc = lcs[0] #the claim part
        lsl = lcs[1] #the sources list part
        
        matchingClaimWithSource = False
        
        for rcs in remoteClaimsWithSources:
            rc = rcs[0] #the claim part
            
            if claimMatch(lc, rc):
                matchingClaimWithSource = rcs
            else:
                pass
    
        if not matchingClaimWithSource: #then we didn't find an exact match
            print 'decision add pair ', lcs
            addPair(page, lcs)
        
        else: #maybe we can add a source
            sourcesToAdd = list() #the sources that we'll push to the remoteClaimWithSource, if we find any
            rsl = matchingClaimWithSource[1] #the source part of the pair
            for ls in lsl: #localsource in localsourcelist
                if sourceMatch(ls, rsl):
                    pass
                else:
                    sourcesToAdd.append(ls)
            for ls in sourcesToAdd:
                rs = matchingClaimWithSource[0] #the claim oart if the pair
                print 'add source', ls
                rs.addSource(ls)
                positions['sourceadds'] += 1
                

def viafredir(viafnum):
    addr = 'http://viaf.org/viaf/' + viafnum + '/'
    try:
        urlobj = urllib2.urlopen(url=addr, timeout=20)
        
        redirAddr = urlobj.geturl()
        
        if addr == redirAddr:
            return viafnum
            #print 'same', addr
        else:
            updatedVIAFnum = redirAddr[21:][:-1]
            positions['viafredirs'] += 1
            return updatedVIAFnum
    
    except urllib2.URLError: 
        return viafnum

VIAFISNImapfile = open('VIAFISNImap.json', 'r')
VIAFISNImap = json.load(VIAFISNImapfile)

def isniEquivs(viafnum):
    '''returns a list of equivalent isnis for a viafnum or None if none exists'''
    try:
        isniEquivList = VIAFISNImap[viafnum]
    except KeyError:
        return False
    return isniEquivList

def makeAC(qnumcluster):
    for clusteritem in qnumcluster:
        if clusteritem['idtyp'] == 'VIAF':
            #lets check if it's moved
            clusteritem['idval'] = viafredir(clusteritem['idval'])
            #find a list of isni equivalents if they exist
            isniEquivList = isniEquivs(clusteritem['idval'])
            if isniEquivList:
                for isninum in isniEquivList:
                    #REMEMBER TO ADD SPACES
                    qnumcluster.append({'lang':'xx', 'qnum':clusteritem['qnum'], 'idtyp':'ISNI', 'idval':isninum})
                    positions['isniadds'] += 1
    writeACluster2(qnumcluster)

def hasNonPGND(authorityTemplate):
    for param in authorityTemplate.params:
                pn = param.name.strip() #making sure it's nonempty
                pv = param.value.strip() #making sure it's nonempty
                pv = pv.lower()
                if pn == 'TYP' and pv != 'p': #its a gnd not of type p
                    return True
                else:
                    return False
    


def crawlLanguage(lang):
    print lang, 'executed'
    #for reporting
    seen = 0
    starttime = time.time()
    #start crawling
    for authorityPage in langAuthorityDict[lang]:
        seen += 1
        if positions['prevtouched'] >= seen:
            continue
        print authorityPage
        qnumcluster = list()
        
        if seen % 10 == 0:
            temptime = time.time()
            print lang, 'seen: ', seen, 'time: ', temptime - starttime, 'speed: ', seen / (temptime - starttime)
        try:
            #find the Wikidata page
            item = pywikibot.ItemPage.fromPage(authorityPage)
            #then get it
            item.get()
            qnum = item.id
            #get the wikipedia page
            authorityText = authorityPage.get() 
            #load it into mwparserfromhell
            authorityCode = mwparserfromhell.parse(authorityText)
            #extract the templates
            authorityTemplates = authorityCode.filter_templates()
            #look through the templates
            for authorityTemplate in authorityTemplates:
                #are these the droids we're looking for?    
                if authorityTemplate.name.strip() == langTemplateShort[lang]:
                    if hasNonPGND(authorityTemplate):
                        break
                    for param in authorityTemplate.params:
                        pn = param.name.strip() #making sure it's nonempty
                        pv = param.value.strip() #making sure it's nonempty    
                        if pv:
                            if pn in ['TYP', 'LCCN', 'VIAF', 'GND', 'PND','BNF', 'SUDOC']:
                                clusteritem ={'lang':lang, 'qnum':qnum, 'idtyp':pn, 'idval':pv}
                                qnumcluster.append(clusteritem)
                                          #'ORCID', 
                                          #'SELIBR', 'GDK', 
                                          #'GDK-V1', 'SWD', 'BPN',
                                          #'RID', 'Scopus', 'BIBSYS', 'ULAN',
                                          #'NDL', 'SUDOC', 'KID', 'WORLDCATID']:
            if qnumcluster:                        
                makeAC(qnumcluster)
            positions['prevtouched'] = seen #remember how many we've done
            savePositions() #save our place in case we crash                 
        except pywikibot.NoPage:
            pass


crawlLanguage('en')

print 'end'