import sqlite3
import json

#constants

VIAFISNImapfile = open('VIAFISNImap.json', 'r')
VIAFISNImap = json.load(VIAFISNImapfile)


#conn = sqlite3.connect('/data/users/kleinm/wikidata/authorities.db')
conn = sqlite3.connect('/data/users/kleinm/wikidata/tests.db')
c = conn.cursor()

isniWrites = list()

def inISNIwrites(idrec):
    qnum = idrec[1]
    isni = idrec[3]
    
    for willWrite in isniWrites:
        #if the the isni number exists
        if willWrite[3] == isni:
            #and if the it's the same wikidata item
            if willWrite[1] == qnum:
                #then we've found a duplicate
                return True
    #otherwise either the isni is unique in the idval sense, or it belongs to two wikidata item
    return False


for row in c.execute('''select * from authorities where idtyp like 'VIAF';'''):
    qnum = row[1] 
    viafnum = row[3]
    print qnum, viafnum
    try:
        isnilist = VIAFISNImap[viafnum]
        for isni in isnilist:
            idrec = ('xx', qnum, 'ISNI', isni)
            if not inISNIwrites(idrec):
                isniWrites.append(idrec)
            else:
                pass
    except KeyError:
        pass

#write isnis to db
print len(isniWrites)

c.executemany('''INSERT INTO authorities VALUES (?,?,?,?)''', isniWrites)
conn.commit()