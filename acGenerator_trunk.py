#!/usr/bin/python
# -*- coding: utf-8 -*-


#for use in trunk and not rewrite branch of pywikipedia
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
          
import pywikibot
import time
import mwparserfromhell
import multiprocessing
import sqlite3


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
                     ) ) 
                         for l in langTemplateDict)


#make a sqlite database
conn = sqlite3.connect('/data/users/kleinm/wikidata/authorities.db')
c = conn.cursor()
# Create table if necessary
try:
    c.execute('''CREATE TABLE authorities
                 (lang, qnum, idtyp, idval)''')
    # Save (commit) the changes
    conn.commit()
except sqlite3.OperationalError:
    pass

#Our datatype maker
def makeALocalRecord(lang, qnum, idtyp, idval):
    idrec = (lang, qnum, idtyp, idval)
    try:
        c.execute('''INSERT INTO authorities VALUES (?,?,?,?)''', idrec)
        conn.commit()
    #if the db is locked, just keep trying, not elegant, but should work
    except OperationalError:
        makeALocalRecord(qnum, lang, idtyp, idval)
    
#Our per-language crawler that calls the datatype maker

def crawlLanguage(lang, fullrun=True):
    print lang, 'executed'
    #for reporting
    seen = 0
    starttime = time.time()
    #start crawling
    
    for authorityPage in langAuthorityDict[lang]:
        print seen
        #if we're just testing
        if (not fullrun) and (seen > 10):
            return
        else:
            
            seen += 1
            print seen
            if seen % 10 == 0:
                temptime = time.time()
                print lang, 'seen: ', seen, 'time: ', temptime - starttime, 'speed: ', seen / (temptime - starttime)
            
            try:
                #find the Wikidata page
                item = pywikibot.pywikibot.DataPage(authorityPage)
                #then get it
                item.get()
                qnum = item._title
                print item._title
                #get the wikipedia page
                authorityText = authorityPage.get() 
                #load it into mwparserfromhell
                authorityCode = mwparserfromhell.parse(authorityText)
                #extract the templates
                authorityTemplates = authorityCode.filter_templates()
                #look through the templates
                for authorityTemplate in authorityTemplates:
                    #are these the droids we're looking for?    
                    if authorityTemplate.name == langTemplateShort[lang]:
                        if hasNonPGND(authorityTemplate):
                            break
                        for param in authorityTemplate.params:
                            pn = param.name.strip() #making sure it's nonempty
                            pv = param.value.strip() #making sure it's nonempty    
                            if pv:
                                if pn in ['TYP', 'LCCN', 'VIAF', 'GND', 'PND','BNF', 'SUDOC']:
                                    makeALocalRecord(lang, qnum, pn, pv)
                                              #'ORCID', 
                                              #'SELIBR', 'GDK', 
                                              #'GDK-V1', 'SWD', 'BPN',
                                              #'RID', 'Scopus', 'BIBSYS', 'ULAN',
                                              #'NDL', 'SUDOC', 'KID', 'WORLDCATID']:
                                              
                                    
            except pywikibot.NoPage:
                pass

#crawlLanguage('en', False)
#crawlLanguage('de', False)
#crawlLanguage('it', False)
#crawlLanguage('fr', False)

#call the crawler on every language in a multiprocessed way
jobs = []
for lang in langAuthorityDict:
    proc = multiprocessing.Process(target=crawlLanguage, args=(lang,False))
    jobs.append(proc)

for job in jobs: 
    job.start()
for job in jobs: 
    job.join()
    print job
    
print'finished'