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

#helpers
def get_soup(current_url):
    request = requests.get(current_url)
    return BeautifulSoup(request.text, "lxml")

# Create your views here.


def say_hello(request):
    return render(request, 'hello.html', {'name': 'Mosh'})

def filter(request):
    context = {}
    start_time = time.time()

    try:
        min_price = float(request.GET.get('min_price', 0))
    except:
        min_price = 0

    context['min_price'] = min_price

    try:
        max_price = float(request.GET.get('max_price', 100000))
    except:
        max_price = 100000

    context['max_price'] = max_price


    choice = request.GET.get('selection', "all")
    context['choice'] = choice

    searching = request.GET.get('searching', "buy")
    context['searching'] = searching

    searching_for = False

    if searching == "search":
        searching_for = True

    #today_entries = (Image.objects.filter(created_at__gte=timezone.now().replace(hour=0, minute=0, second=0))).order_by('article_id')
    articles_today = Image.objects.filter(price__range=(min_price, max_price), is_searching_for=searching_for, created_at__gte=timezone.now().replace(hour=0, minute=0, second=0)).values('article_id').annotate(total=Count('article_id')).order_by('total')
    today_index = []
    for article_today in articles_today:
        today_index.append(Image.objects.filter(article_id=article_today['article_id']).order_by("-created_at"))

    results = []
    if choice == "all":
        results = today_index


    if choice == "new":
        for index in today_index:
            if len(index) == 1:
                results.append(index)

    if choice == "changed":
        for index in today_index:
            if len(index) > 1:
                results.append(index)

    title = request.GET.get('title', "")
    context['title'] = title
    if title != "":
        print("SEARCH")
        search_result = []
        for result in results:
            if title.lower() in result[0].title.lower():
                search_result.append(result)
        results = search_result

    description = request.GET.get('description', "")
    context['description'] = description
    if description != "":
        search_result = []
        for result in results:
            if description.lower() in result[0].description.lower():
                search_result.append(result)
        results = search_result


    context['results'] = results
    print("--- %s seconds ---" % (time.time() - start_time))
    return render(request, 'filter.html', context)


def morethanone(request):
    context = {}
    entry_list = []
    entries = 0
    start_time = time.time()

    today_entries = Image.objects.filter(created_at__gte=timezone.now().replace(hour=0,minute=0,second=0))
    if today_entries:
        for today_entry in today_entries:
            if len(Image.objects.filter(article_id=today_entry.article_id)) == 1:
                continue
            print(today_entry.article_id.url)
            print(today_entry.created_at)
            entries = entries + 1
    print("Entries found: " + str(entries))
    print(timezone.now().replace(hour=0, minute=0, second=0))
    print("--- %s seconds ---" % (time.time() - start_time))

    context['links'] = entry_list
    return render(request, 'links.html', context)

def scrape(request):
    context = {}
    start_time = time.time()

    # get number of total articles
    url_base = "https://www.waffengebraucht.at/?page="

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

    print("Entries: " + str(entries))
    print("--- %s seconds ---" % (time.time() - start_time))
    context['links'] = article_list
    return render(request, 'links.html', context)


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
