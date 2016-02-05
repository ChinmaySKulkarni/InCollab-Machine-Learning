#!/usr/bin/python
# This program retrieves articles using the NY Times API related to a given interest.
# This article information will be inserted into a MySQL table.
# Reference: http://developer.nytimes.com/docs/read/article_search_api_v2
#
# For every article, the following information is stored:
#
#        article_data["type_of_material"] = article["type_of_material"]
#        article_data["lead_paragraph"] = article["lead_paragraph"]
#        article_data["headline"] = article["headline"]["main"]
#        article_data["abstract"] = article["abstract"]
#        article_data["snippet"] = article["snippet"]
#        article_data["web_url"] = article["web_url"]
#        article_data["multimedia"] = article["multimedia"]
#        article_data["TYPE"] => As got from article_type.py
#
from __future__ import print_function
from nytimesarticle import articleAPI
import sys
import time
import base64
import urllib
import cql
import json
import MySQLdb as mdb
import article_type as at

#TODO: Use 'fq' option instead of just 'q' for specific querying. This will improve results. It is based on Lucene Syntax
#TODO: What about the headlines/title of the article. I can give that too.
interests = ["Science", "Arts", "Math", "Sports","History", "Geography", "Languages"]
fields = ["web_url","snippet","lead_paragraph","abstract","headline","keywords","pub_date"]
# mysql is running on localhost itself
mysql_ip = "127.0.0.1"
cassandra_ip = "172.31.18.149"
image_dir = "/home/ubuntu/machine-learning-incollab/Images/"
temp_dir_downloaded_images = image_dir + "nytimes_downloaded_images/"


def pretty_print(d,indent):
    for key in d:
        string = "\t" * indent + str(key)
        print(string)
        if isinstance(d[key], dict):
            pretty_print(d[key], indent + 1)
        elif isinstance(d[key], list):
            for item in d[key]:
                string = "\t" * indent + str(item)
                print(string)
        else:
            string = "\t" * (indent + 1) + str(d[key])
            print(string)


#Returns a list of dicts. Each element of the list is an article, represented as a dict of the following keys.
def extract_useful_fields(articles):
    all_articles_information = []
    for article in articles["response"]["docs"]:
        article_data = {}
        article_data["type_of_material"] = article["type_of_material"]
        article_data["lead_paragraph"] = article["lead_paragraph"]
        article_data["headline"] = article["headline"]["main"]
        article_data["abstract"] = article["abstract"]
        article_data["snippet"] = article["snippet"]
        article_data["web_url"] = article["web_url"]
        article_data["multimedia"] = article["multimedia"]
        all_articles_information.append(article_data)
    return all_articles_information


def retrieve_articles(search_term, api,date_start):
    global fields
    articles = api.search( q = search_term, begin_date = date_start, f1 = fields)
    if(articles["status"] != "OK"):
        python_print("Error retrieving articles for interest \t" + search_term)
        return 1
    #articles["response"] has keys: "meta" and "docs". articles["response"]["meta"] is useless
    number_of_articles_found = len(articles["response"]["docs"])
    if(number_of_articles_found == 0):
        python_print("No articles found for interest \t" + search_term +"!")
        return 1
    else:
        all_articles_information = extract_useful_fields(articles)
        return all_articles_information


def print_urls(data):
    for interest in data:
        for article in data[interest]:
            python_print(interest , "\t", article["web_url"])


#Returns a dict with key = interest. The value is the list of dicts returned by retrieve_articles
def process_interests(api,date_start):
    global interests
    articles_retrieved_for_interests = {}
    for search_term in interests:
        articles_for_interest = retrieve_articles(search_term,api,date_start)
        if(articles_for_interest == 1):
            continue
        articles_retrieved_for_interests[search_term] = articles_for_interest
    return articles_retrieved_for_interests

#TODO Find a proper way to escape quotes
def escape_quotes(string):
    string = string.replace('"','')
    string = string.replace("'","")
    return string

def escape_quotes_MySQL(cur,string):
    cur.execute('SELECT QUOTE("%s")' %(string))
    string = cur.fetchone()[0]
    return string


def execute_sql_queries(cur,articles_retrieved_for_interests,connection):
    for interest in articles_retrieved_for_interests:
	for article in articles_retrieved_for_interests[interest]:
            cur.execute("SELECT article_id FROM mysql_articleinterests ORDER BY article_id DESC LIMIT 1")
            latest_article_id = cur.fetchone()[0]
            article_id = latest_article_id + 1
            article["article_id"] = article_id
            type_article = article["TYPE"].encode('ascii','ignore')
            headline = article["headline"]
            if (headline is not None):
                headline = headline.encode('ascii','ignore')
            snippet = article["snippet"]
            lp = article["lead_paragraph"]
            abstract = article["abstract"]
            url = article["web_url"]
            if (snippet is not None):
                summary = snippet.encode('ascii','ignore')
            elif (lp is not None):
                summary = lp.encode('ascii','ignore')
            elif (abstract is not None):
                summary = abstract.encode('ascii','ignore')
            else:
                summary = headline.encode('ascii','ignore')
            #headline = escape_quotes_MySQL(cur,headline)
            #interest = escape_quotes_MySQL(cur,interest)
            #type_article = escape_quotes_MySQL(cur,type_article)
            #summary = escape_quotes_MySQL(cur,summary)

            headline = escape_quotes(headline)
            interest = escape_quotes(interest)
            type_article = escape_quotes(type_article)
            summary = escape_quotes(summary)
            cur.execute('INSERT INTO mysql_articleinterests (article_id, interest, type, summary, url, ts) VALUES ("%d","%s","%s","%s","%s",NOW())'\
            % (article_id,interest,type_article,summary,url))
            connection.commit()
        python_print("Inserted articles for interest\t", interest)
    return articles_retrieved_for_interests


def insert_article_data_mysql(articles_retrieved_for_interests):
    global mysql_ip
    try:
        conn = mdb.connect(user = "root", passwd = "test123", db = "user_articles_data", host = mysql_ip)
        python_print("Connected to MySQL Database")
        cur = conn.cursor()
        articles_retrieved_for_interests = execute_sql_queries(cur,articles_retrieved_for_interests,conn)
        cur.close()
        conn.close()
    except mdb.Error as e:
        python_print("Error" + str(e))
    return articles_retrieved_for_interests


def get_default_image(interest):
    global image_dir
    if interest == "Science":
        return image_dir + 'science.png'
    if interest == "Arts":
        return image_dir + 'arts.png'
    if interest == "Math":
        return image_dir + 'math.png'
    if interest == "Sports":
        return image_dir + 'sports.png'
    if interest == "History":
        return image_dir + 'history.png'
    if interest == "Geography":
        return image_dir + 'geo.png'
    if interest == "Languages":
        return image_dir + 'languages.png'


def send_data_to_nodejs(articles_retrieved_for_interests):
    global temp_dir_downloaded_images
    total_count = 0
    for interest in articles_retrieved_for_interests:
        for article in articles_retrieved_for_interests[interest]:
            total_count += 1
    current_count = 0
    for interest in articles_retrieved_for_interests:
        for article in articles_retrieved_for_interests[interest]:
            article_id = article['article_id']
            multimedia = article['multimedia']
            if len(multimedia) == 0:
                python_print("Default image will be added")
                image = get_default_image(interest)
            else:
                image_url = 'http://www.nytimes.com/' + multimedia[0]['url']
                #Save the image locally. Will be removed in the end.
                image = temp_dir_downloaded_images + str(article_id) + '_image'
                urllib.urlretrieve(image_url,image)
            current_count += 1
            message_to_node = '{"article_id":' + '"' + str(article_id) + '"' + ',"image":' + '"' + str(image) + '"'
            message_to_node += ',"current":' + '"' + str(current_count) + '"' + ',"total":' + '"' + str(total_count) + '"}'
            print(message_to_node)
            sys.stdout.flush()
            time.sleep(0.5)


def python_print(*objs):
    print("Python Print:\n", *objs, file=sys.stderr)
    #sys.stderr.flush()
    return

if __name__ == "__main__":
    api_key = "1400c0d261db6c800c93ddea5b406d40:4:71870996"
    api = articleAPI(api_key)
    date_start = int(time.strftime('%Y%m%d'))
    articles_retrieved_for_interests = process_interests(api,date_start)
    articles_retrieved_for_interests = at.get_article_types(articles_retrieved_for_interests)
    articles_retrieved_for_interests = insert_article_data_mysql(articles_retrieved_for_interests)
    send_data_to_nodejs(articles_retrieved_for_interests)
