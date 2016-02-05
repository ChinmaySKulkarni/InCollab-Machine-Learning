#!/usr/bin/python
import urllib2
from bs4 import BeautifulSoup
from cookielib import CookieJar
from HTMLParser import HTMLParser
import random

#url = "http://www.nytimes.com/reuters/2015/05/03/business/03reuters-berkshire-buffett-weeekend.html"


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


def strip_tags(web_page_text):
    s = MLStripper()
    s.feed(web_page_text)
    return s.get_data()


def get_html(url):
    try:
        print url
        cj = CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        response = opener.open(url)
        html = response.read()
        return html
    except urllib2.HTTPError, e:
        print 'We failed with error code - %s.' % e.code
        return None


def process_html_page(html):
    if (html == None):
        return None
    soup = BeautifulSoup(html)
    article_text_html = soup.find_all("p", "story-body-text story-content")
    article_text = strip_tags(str(article_text_html))
    return article_text


def concat_string(field):
    if (field != None):
        return field
    return ""

def return_random_type():
    types = ["Hobby","Work"]
    i = random.randint(0,1)
    return types[i]

def predict_type_articles(articles_list):
    refined_articles_list = []
    for article in articles_list:
        #TODO: Future work: if the text in "type_of_material", "lead_paragraph", "abstract", etc. is not enough,
        #retrieve the text content of the entire article and find the type of the article using NLP methods.
        #html = get_html(article["web_url"])
        html = 1
        if (html == None):
	        continue
        else:
            #all_text = concat_string(article["type_of_material"]) + "\t" + concat_string(article["lead_paragraph"]) + "\t" + concat_string(article["headline"]) + "\t" + concat_string(article["abstract"]) + "\t" + concat_string(article["snippet"]) + "\t"
            #article_text = process_html_page(html)
            #print article_text
            #all_text += "\t" + concat_string(process_html_page(html))
            #all_text = u'\t'.join((all_text,article_text)).encode('utf-8'
            #print all_text,"\n\n"
            #TODO: Get type of interest by processing all the text.
            #Currently, just setting the type to "WORK"
            if article["type_of_material"] == "Blog":
                article["TYPE"] = "Hobby"
            else:
                article["TYPE"] = return_random_type()
            refined_articles_list.append(article)
    return refined_articles_list


def get_article_types(articles_interests):
    for interest in articles_interests:
        articles_interests[interest] = predict_type_articles(articles_interests[interest])
    return articles_interests

if __name__ == "__main__":
    html = get_html(url)
    random.seed()
    summary_text = process_html_page(html)


