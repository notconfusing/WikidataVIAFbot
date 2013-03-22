import sqlite3
import pywikibot

de_wikipedia = pywikibot.Site('de', 'wikipedia')
wikidata = de_wikipedia.data_repository()

idMap = {'TYP': pywikibot.PropertyPage(wikidata, 'Property:P107'),
         'LCCN': pywikibot.PropertyPage(wikidata, 'Property:P244'),
         'VIAF':pywikibot.PropertyPage(wikidata, 'Property:P214'),
         #'ORCID':, 
         'GND':pywikibot.PropertyPage(wikidata, 'Property:P227'), 
         #'PND':, 
         #'SELIBR':, 
         #'GDK':, 
         #'GDK-V1':, 
         #'SWD':, 
         'BNF':pywikibot.PropertyPage(wikidata, 'Property:P268'), 
         #'BPN':,
         #'RID':, 
         #'Scopus':, 
         #'BIBSYS':, 
         #'ULAN':,
         #'NDL':, 
         'SUDOC':pywikibot.PropertyPage(wikidata, 'Property:P269'), 
         #'KID':, 
         #'WORLDCATID':
         }

targetIDList = list()
for v in idMap.itervalues():
    targetIDList.append(v)


def getCurrentProperties(qnum):
    targetClaims = list()
    page = pywikibot.ItemPage(wikidata, qnum) #  this can be used for any page object
    page.get() #  you need to call it to access any data.
    claimObjs = page.claims
    for claimID in claimObjs:
        claimlist = page.claims[claimID]
        for claim in claimlist:
            if claim in targetIDList:
                targetClaims.append(claim)
                print 'claim in', claim
            else:
                pass
                print'claim out'
        
            


def writeACluster(propCluster):
    qnum = propCluster[0]['qnum'] #any elemnt of propCluster should have the same qnum
    currentProperties = getCurrentProperties(qnum)
        

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
conn = sqlite3.connect('/data/users/kleinm/wikidata/authorities.db')
c = conn.cursor()

c.execute("select * from authorities order by qnum;")
aRow = rowInterpret(c.fetchone())

first = True
propCluster = list() #a list of authority rows (dicts) that should all have the same qnum
currQnum = False
while aRow:
    if first:
        currQnum = aRow['qnum']
        propCluster.append(aRow)
        first = False
    else:
        #is it part of a group, then add it
        if aRow['qnum'] == currQnum:
            propCluster.append(aRow)
        #if its a new qnum, then ship the old one and start a new list
        else:
            writeACluster(propCluster)
            propCluster = [aRow]
            currQnum = aRow['qnum']

    aRow = rowInterpret(c.fetchone())

#there will be a last unaccountedfor item
sendToDiff(propCluster)

print 'end'