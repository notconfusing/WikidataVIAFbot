import sqlite3
import pywikibot
from collections import defaultdict

de_wikipedia = pywikibot.Site('de', 'wikipedia')
wikidata = de_wikipedia.data_repository()

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
             'xx':'Q423048',}

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

def makeSourcedClaim(idValCluster):
    #what's the idtype were addng
    
    firstProperty = idValCluster[0] #there's guaranteed to be at least one
    idtyp = firstProperty['idtyp']
    idval = firstProperty['idval']
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
    
    for ls in lsl:
        lc.addSource(ls)

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
    
    print qnum
    print localClaimsWithSources
    print remoteClaimsWithSources
    
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
            print 'add pair ', lcs
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
                    
                
                
            
    
def writeACluster(qnumCluster):
    qnum = qnumCluster[0]['qnum'] #any elemnt of qnumClusterList should have the same qnum
    page = pywikibot.ItemPage(wikidata, qnum)
    
    localClaimsWithSources = propertiesToClaims(qnumCluster)  
    remoteClaims = getRemoteClaims(qnum)
    
    
    #first see which AC we can add to, or don't have to write, and remove it from out queue
    
    for remoteClaim in remoteClaims:
        #do they have the same idtyp
        for localClaimWithSources in localClaimsWithSources:
            #recall a clam with a source is a list whos first element is the Claim
            localClaim = localClaimWithSources[0]
            localClaimSources = localClaimWithSources[1]
            print qnum, ' claimid compares ', remoteClaim.id, localClaim.id
            print remoteClaim.id == localClaim.id
            if remoteClaim.id == localClaim.id:
                #do they have the same idval?
                print qnum, ' claimtarget compares ', remoteClaim.target, localClaim.target
                print remoteClaim.target == localClaim.target 
                if remoteClaim.target == localClaim.target:
                    #do they have the same source?
                        #for every remote source
                        if remoteClaim.sources:
                            for remoteClaimSource in remoteClaim.sources:
                            #and for every local source
                                for localClaimSource in localClaimSources:
                                    print qnum, ' sourceid compares ', remoteClaimSource.id, localClaimSource.id
                                    print remoteClaimSource.id == localClaimSource.id
                                    if remoteClaimSource.id == localClaimSource.id:
                                        #do those sources have the same target
                                        print qnum, ' sourcetarget compares ', remoteClaimSource.target, localClaimSource.target
                                        print remoteClaimSource.target == localClaimSource.target
                                        if remoteClaimSource.target == localClaimSource.target:
                                            #TODO log this
                                            print 'complete dupe'
                                            localClaimsWithSources.remove(localClaimWithSources)
                                        else:
                                            #maybe the remote source is actually account for later on
                                            print 'would update with another source language'
                                            remoteClaim.addSource(localClaimSource)
                                            #now we don't need to do this claim later
                                            localClaimsWithSources.remove(localClaimWithSources)
                                    else:
                                        print 'would update with another source method i.e. previously was not "imported from"'
                                        remoteClaim.addSource(localClaimSource)
                                        #now we don't need to do this claim later
                                        localClaimsWithSources.remove(localClaimWithSources)
                        #there's not remoteClaim sources
                        else:
                            print 'would add the inaugural source'
                            for localClaimSource in localClaimSources:
                                remoteClaim.addSource(localClaimSource)
                                #now we don't need to do this claim later
                            localClaimsWithSources.remove(localClaimWithSources)
                else:
                    print 'would add a claim with conflicting idval, a human should probably check this'
                    page.addClaim(localClaim)
                    for localClaimSource in localClaimSources:
                        localClaim.addSource(localClaimSource)
                    #now we don't need to do this claim later
                    localClaimsWithSources.remove(localClaimWithSources)
                    
            else:
                pass

    #now that we've look at all the remote data and amended or conflcited, we can push the rest of our queue.
    print qnum, len(localClaimsWithSources)
    for localClaimWithSources in localClaimsWithSources:
        localClaim = localClaimWithSources[0]
        localClaimSources = localClaimWithSources[1]
        print 'claim ', localClaim
        page.addClaim(localClaim)
        
        for localClaimSource in localClaimSources:
            localClaim.addSource(localClaimSource)
            print 'source ', localClaimSource
        
    #then write our clue to the page
    
    #then put the page
        
        

def rowInterpret(sqltuple):
    if sqltuple == None:
        return None
    else:
        row = dict()
        row['lang'] = sqltuple[0]
        row['qnum'] = sqltuple[1]
        row['idtyp'] = sqltuple[2]
        row['idval'] = sqltuple[3]
        return row


#get the query
conn = sqlite3.connect('/data/users/kleinm/wikidata/tests.db')
c = conn.cursor()

c.execute("select * from authorities order by qnum;")
aRow = rowInterpret(c.fetchone())

first = True
qnumCluster = list() #a list of authority rows (dicts) that should all have the same qnum
currQnum = False
while aRow:
    if first:
        currQnum = aRow['qnum']
        qnumCluster.append(aRow)
        first = False
    else:
        #is it part of a group, then add it
        if aRow['qnum'] == currQnum:
            qnumCluster.append(aRow)
        #if its a new qnum, then ship the old one and start a new list
        else:
            writeACluster2(qnumCluster)
            qnumCluster = [aRow]
            currQnum = aRow['qnum']

    aRow = rowInterpret(c.fetchone())

#there will be a last unaccountedfor item
writeACluster(qnumCluster)

print 'end'