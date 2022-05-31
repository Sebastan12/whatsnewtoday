import requests
import hashlib
import pandas as pd
from bs4 import BeautifulSoup
import time
start_time = time.time()


def get_soup(current_url):
    request = requests.get(current_url)

    return BeautifulSoup(request.text, "lxml")


#steps - list all categories using bs4
#get total article number in each category
#then cut it by date relvancy
#find a way to it in excel
#find a way to compare at least 1 value
#to generate requirements for github
#usefull link https://stackoverflow.com/questions/51863155/do-we-need-to-upload-virtual-env-on-github-too
#can calulate checksum of each indiviual article https://www.geeksforgeeks.org/python-script-to-monitor-website-changes/
#only calculate of the part that is ONLY the article - not the ads around it

#get number of total articles
url_base="https://www.waffengebraucht.at/?page="

#find max page number
limiter_soup = get_soup(url_base + "100000000000000000")
pagination = limiter_soup.find("ul", {"class": "pagination"})
maximum = int(pagination.find("li", {"class": "active"}).getText())
maximum_page_number = maximum - 1

article_list = []
product_list = []
#ends starts at zero stops 1 before number
for i in range(maximum_page_number + 1):
    print ("-----PAGE-----" + str(i+1))
    url_prefix = "https://www.waffengebraucht.at"
    for listing in get_soup(url_base + str(0)).find_all("a", {"class": "classified-teaser-title"}):
        article_list.append(url_prefix + listing['href'])
        print(url_prefix + listing['href'])

print(len(article_list))
amount_of_articles = len(article_list)

#process once we have article page!
#url = "https://www.waffengebraucht.at/munition/buechsenpatronen/65x68-aus-nachlass-65x68-repetierer-bockbuechse-thiersee-tirol--381198"

for idx, url in enumerate(article_list):
    soup = get_soup(url)
    article = soup.find('article')

    #remove contact info - as we do not care for its changes
    if len(article.find_all("div", {"class": "panel panel-default"})) > 2:
        print("EXCEPTION IN ARTICLE OR DESCRIPTION")
        quit()
    article.find_all("div", {"class": "panel panel-default"})[-1].decompose()
    currentHash = hashlib.sha224(article.prettify().encode('utf-8')).hexdigest()
    #to see all
    #print(article.prettify())
    print("----Article " + str(idx+1) + "/" + str(amount_of_articles) + " ----")
    print(currentHash)
    print(article.h1.getText())
    print("----END ARTICLE---")
    #print(article.find("div", {"class": "panel-body"}).getText())
    #print(article.find("td", {"class": "classified-detail-value price"}).getText())
    product = []
    product.append(currentHash)
    product.append(article.h1.getText())
    product.append(article.find("div", {"class": "panel-body"}).getText())
    product.append(article.find("td", {"class": "classified-detail-value price"}).getText())
    product.append(url)
    product_list.append(product)

listings = pd.DataFrame(product_list)
file_name = 'listings.xlsx'
listings.to_excel(file_name)
print("--- %s seconds ---" % (time.time() - start_time))
