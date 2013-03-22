import urllib2
import sqlite3
from multiprocessing import Pool
import time

conn = sqlite3.connect('/data/users/kleinm/wikidata/authorities.db')
c = conn.cursor()

c.execute("select idval from authorities where idtyp like 'VIAF';")
viaflist = c.fetchall()
viaflist = [viafnum[0] for viafnum in viaflist]


#constants
buildprepath = 'http://viaf.org/viaf/'
buildpostpath = '/'

    #Our datatype maker
def updateALocalRecord(viafnum, updatedVIAFnum):
    try:
        c.execute('''update authorities set idval = ? where idval = ? and idtyp = 'VIAF';''', (updatedVIAFnum, viafnum,))
        conn.commit()
        #print 'different: ' + str(viafnum) + ' vs. '+ str(updatedVIAFnum)
    #if the db is locked, just keep trying, not elegant, but should work
    except sqlite3.OperationalError:
        updateALocalRecord(viafnum, udpatedVIAFnum)

def updateRedir(viafnum):
    addr = buildprepath + viafnum + buildpostpath
    try:
        urlobj = urllib2.urlopen(url=addr, timeout=20)
        
        redirAddr = urlobj.geturl()

        if addr == redirAddr:
            pass
            #print 'same', addr
        else:
            updatedVIAFnum = redirAddr[21:][:-1]
            updateALocalRecord(viafnum, updatedVIAFnum)
    
    except urllib2.URLError: 
        print 'problem with URL', addr
    #TODO log this

starttime = time.time()

pool = Pool(processes=3)              # start 4 worker processes
pool.map(updateRedir, viaflist)

endtime = time.time()
print 'speed: ', (761 /(endtime - starttime))
