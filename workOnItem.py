import pwb #only needed if you haven't installed the framework as side-package
import pywikibot
site = pywikibot.Site('en','wikipedia') #  any site will work, this is just an example
page = pywikibot.Page(site, 'Douglas Adams')
item = pywikibot.ItemPage.fromPage(page) #  this can be used for any page object
item.get() #  you need to call it to access any data.
sitelinks = item.sitelinks
aliases = item.aliases

print type(item.claims)
for i in item.claims:
    print item.claims[i][0].target

