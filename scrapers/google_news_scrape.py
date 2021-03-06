import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import re
import unicodedata
import datetime
import ipdb
import time
import sys

class google_scrape():

    def __init__(self, days=7):
        self.days = days
        self.url_add = '&tbs=qdr:d'
        if days == 7:
            self.url_add = '&tbs=qdr:w'
        elif days == 30:
            self.url_add = '&tbs=qdr:m' 

    def get_links(self):
        self.all_dates = []
        DD = datetime.timedelta(2)
        links = []
        current_day = datetime.datetime.now()

        self.start_date = current_day.strftime('%Y-%m-%d')
        for page in range(0, 70, 10):
            base = self.create_base_url(page)
            print base
            req = requests.get(base) 
            time.sleep(3)
            soup = BeautifulSoup(req.text, 'html.parser')
            for a in soup.findAll('a'):
                h = a['href']
                if 'q=http' in h:
                    start = h.index('http')
                    end = h.index('&')
                    links.append(h[start:end])
                    
        self.links = list(set(links))

    def get_unique_links(self):
        df = pd.DataFrame([self.links, self.all_dates]).T
        df = df.drop_duplicates()
        df = df.groupby([0]).min()
        df = df.reset_index()
        self.links = df[0].values.tolist()
        self.all_dates = df[1].values.tolist()

    def get_articles(self):
        descriptions = []
        titles = []
        image_urls = []
        articles = []
        new_links = []
        new_dates = []
        sources = []
        print "num links", len(self.links)

        for i, link in enumerate(self.links):
            print i
            try:
                req = requests.get(link)
            except:
                continue
            new_links.append(link)
            soup = BeautifulSoup(req.text, 'html.parser')
            entire_article = soup.findAll('article')
            text = ''
            if not entire_article:
                text = ' '.join([par.text for par in soup.findAll('p')])
            else:
                for art in entire_article:
                    for par in art.findAll('p'):
                        text += par.text + ' '
            text = self.decode_unicode(text)
            articles.append(text)
            try:
                title = soup.findAll('meta', {'name' : 'dc.title'})[0]['content']
            except:
                try:
                    title = soup.findAll('title')[0].text
                except:
                    title = 'None'
            title = self.decode_unicode(title)
            titles.append(title)
            try:
                desc = soup.findAll(attrs =  {'property' : 'og:description'})[0].attrs['content']
                desc = self.decode_unicode(desc)
            except:
                desc = 'None'
            descriptions.append(desc)
            try:
                image_urls.append(soup.findAll(attrs =  {'property' : 'og:image'})[0].attrs['content'])
            except IndexError:
                image_urls.append('#')
            except KeyError:
                image_urls.append('#')

            #new dates
            if self.days != 1:
                date = self.get_date(req.text) 
                new_dates.append(date)
                if not date:
                    try:
                        new_dates[-1] = new_dates[-2]
                    except IndexError:
                        new_dates[-1] = self.start_date                    
            else:
                new_dates.append(self.start_date)

            sources.append(self.get_source(link))

        frame = pd.DataFrame({'text' : articles, 'url' : new_links, 'source' : sources, \
                'publish_date' : new_dates, 'category' : self.search_term, \
                'title': titles, 'image_url': image_urls, 'description' : descriptions}, \
                columns = ['source', 'url', 'image_url', 'title', 'description', 'text', 'publish_date', 'category'])
        frame = frame.dropna()
        frame.to_csv('data/google_' + self.search_term.replace(' ', '_') + '_data.csv', index=False, encoding='utf-8')
        
    def get_date(self, text):
        try:
            date_reg_exp = re.compile('2014[-/][0-1]\d{1}[-/][0-3]\d{1}')
        except:
            return 0
        matches_list=date_reg_exp.findall(text)
        if matches_list:
            return matches_list[0].replace('/', '-')
        return 0

    def get_source(self, url):
        segs = url.split('.')
        all_pieces = []
        for seg in segs:
            pieces = [piece for piece in seg.split('/') if piece != '']
            all_pieces.extend(pieces)
        url_dests = ['com', 'net', 'co', 'org', 'edu', 'gov', 'ie', 'ca', 'intoday']
        ind = 2
        for url_dest in url_dests:
            if url_dest in all_pieces:
                ind = all_pieces.index(url_dest)
                break
        if len(all_pieces) < 2:
            return 'None'
        return all_pieces[ind - 1]

    def decode_unicode(self, text):
        text = unicode(text)
        a = '/'; b = '\''
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
        text = str(re.sub('[\n]+', ' ', text))
        text = str(re.sub('[\t]+', ' ', text))
        text = text.replace(a, '')
        text = text.replace(b, '')
        return text

    def create_base_url(self, page=0):
        base = 'https://www.google.com/search?hl=en&gl=us&tbm=nws&authuser=0&q=' \
            + self.search_term.replace(' ', '_') + ' &start=' + str(page) + self.url_add
        return base

    def run(self, search_term):
        self.search_term = search_term
        self.get_links()
        self.get_articles()

if __name__ == '__main__':
    search_term = sys.argv[1]
    google = google_scrape()
    google.run(search_term)
