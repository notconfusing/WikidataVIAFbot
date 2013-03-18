import urllib2
import sqlite3

conn = sqlite3.connect('/data/users/kleinm/wikidata/authorities.db')
c = conn.cursor()

c.execute("select idval from authorities where idtyp like 'VIAF';")
viaflist = c.fetchall()

buildprepath = 'http://viaf.org/viaf/'

for viafnum in viaflist:
    addr = buildprepath + viafnum[0]
    try:
        urlobj = urllib2.urlopen(url=addr, timeout=20)
        
        redirAddr = urlobj.geturl()
    
        print addr
        print redirAddr
    
    except urllib2.URLError:
        print 'problem with URL', addr
    #TODO log this