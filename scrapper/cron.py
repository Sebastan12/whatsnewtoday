from django.shortcuts import render
from django.http import HttpResponse
from .models import Articles
from .models import Image
from django.db import IntegrityError
#myimports
from django.utils import timezone
import requests
import hashlib
import pandas as pd
from bs4 import BeautifulSoup
import time
from django.db.models.aggregates import Count
import datetime

def hoi():
    print("HOI CRON RUNNING!!!!!")


def get_soup(current_url):
    request = requests.get(current_url)
    return BeautifulSoup(request.text, "lxml")


def cron_scrape():
    context = {}
    start_time = time.time()

    # get number of total articles
    url_base = "https://www.waffengebraucht.at/?page="
    print(str(datetime.datetime.now()) + " START CRON SCRAPE - scraping page: " + url_base)
    # find max page number
    limiter_soup = get_soup(url_base + "100000000000000000")
    pagination = limiter_soup.find("ul", {"class": "pagination"})
    maximum = int(pagination.find("li", {"class": "active"}).getText())
    maximum_page_number = maximum - 1
    entries = 0
    article_list = []
    product_list = []
    # ends starts at zero stops 1 before number
    for i in range(maximum_page_number + 1):
        print("-----PAGE-----" + str(i + 1))
        print("--- %s seconds ---" % (int(time.time() - start_time)))
        url_prefix = "https://www.waffengebraucht.at"
        for listing in get_soup(url_base + str(i)).find_all("a", {"class": "classified-teaser-title"}):
            entries = entries + 1
            article_url = url_prefix + listing['href']
            obj, created = Articles.objects.get_or_create(url=article_url)
            if created:
                #DEBUG
                article_list.append("ADDED: " + article_url)
                print("ADDED: " + article_url)
                #create first image
                make_image_from_single_article_object(obj)
            else:
                if not Image.objects.filter(article_id=obj):
                    make_image_from_single_article_object(obj)
                    #DEBUG
                    article_list.append("Original Image Created: " + article_url)
                else:
                    if has_changed_since_last_time(obj):
                        make_image_from_single_article_object(obj)
                        # DEBUG
                        article_list.append("Newer Image Created: " + article_url)
                    else:
                        # DEBUG
                        article_list.append("NO Change: " + article_url)

    print("--SUMMARY--")
    context['links'] = article_list
    print("--Done!--")
    print("Entries: " + str(entries))
    print("--- %s seconds ---" % (time.time() - start_time))
    print(str(datetime.datetime.now()) + " END CRON SCRAPE ")


def has_changed_since_last_time(articles_object):
    print("checking: " + articles_object.url)
    soup = get_soup(articles_object.url)
    # nichtexistne artikel leiten auf hauptkategory zurück
    # checke of kein title vorhanden ist
    if soup.find('article') is None:
        #Find proper solution at later time
        print("--ENTRY DOES NOT EXIST--")
        return True
    article = soup.find('article')
    if len(article.find_all("div", {"class": "panel panel-default"})) > 2:
        #Find proper solution at later time
        print("EXCEPTION IN ARTICLE OR DESCRIPTION")
        return True
    if not Image.objects.filter(article_id=articles_object):
        #need to creat article
        print("No Image exists")
        return True
    article.find_all("div", {"class": "panel panel-default"})[-1].decompose()
    currentHash = hashlib.sha224(article.prettify().encode('utf-8')).hexdigest()

    objects = Image.objects.filter(article_id=articles_object).order_by('-created_at')
    #print("current Hash" + currentHash)
    #print("old Hash" + objects[0].hash)
    if objects[0].hash == currentHash:
        print("NO Changes")
        return False
    else:
        print("Change happened")
        return True
    #COMPARE WITH CURRENT ENTRY OF EXISTING
    # to see all
    # print(article.prettify())


def make_image_from_single_article_object(articles_object):
    soup = get_soup(articles_object.url)
    # nichtexistne artikel leiten auf hauptkategory zurück
    # checke of kein title vorhanden ist
    if soup.find('article') is None:
        print("--Image not created - ENTRY DOES NOT EXIST-- " + articles_object.url)
        return
    article = soup.find('article')
    if len(article.find_all("div", {"class": "panel panel-default"})) > 2:
        print("Image not created - EXCEPTION IN ARTICLE OR DESCRIPTION")
        return
    article.find_all("div", {"class": "panel panel-default"})[-1].decompose()
    currentHash = hashlib.sha224(article.prettify().encode('utf-8')).hexdigest()
    title = article.h1.getText()
    price = article.find("td", {"class": "classified-detail-value price"}).getText()
    description = article.find("div", {"class": "panel-body"}).getText()
    is_searching_for = False
    if "Suche" == price:
        price = float(0)
        is_searching_for = True
    else:
        try:
            price = float(price.replace("\xa0€", ""))
        except Exception as e:
            print(e)

    try:
        new_image = Image(article_id=articles_object, title=title, hash=currentHash, price=price, description=description, is_searching_for=is_searching_for)
        new_image.save()
        print("Create Image for: " + articles_object.url)
    except Exception as e:
        print(e)