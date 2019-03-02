import requests
import time
from bs4 import BeautifulSoup
import json
import logging
logger = logging.getLogger(__name__)
import pprint
pp = pprint.PrettyPrinter(indent=2)


class GoogleRequest:
    def __init__(self):
        self.session = requests.Session()
        ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        self.headers = {'User-Agent': ua, 'Referer':'https://www.google.com'}
        self.search_url = "https://www.google.com/search?q={}&source=lnms&tbm=isch&safe=active" # SafeSearch : on

    def request_list(self, keyword_list, socks5_port=''):
        result = []
        for index, keyword in enumerate(keyword_list):
            entry = self.request_one(keyword, socks5_port)
            logger.info('Parsing keyword {} of total {}'.format(index+1, len(keyword_list)))
            if entry:
                kw_entry = (keyword, entry)
                result.append(kw_entry)
        return result

    def request_one(self, keyword, socks5_port=''):
        try:
            time.sleep(1) #Sleep 1 seconds to avoid banning
            if socks5_port:
                proxy = 'socks5://127.0.0.1:{}'.format(socks5_port)
                _request = self.session.get(self.search_url.format(keyword), headers=self.headers, proxies = {'http': proxy,'https': proxy}, timeout=5)
            else:
                _request = self.session.get(self.search_url.format(keyword), headers=self.headers, timeout=5)
            if _request.status_code==200:
                logger.info('Scraping from result, keyword : {}'.format(keyword))
                soup = BeautifulSoup(_request.text, 'lxml')
                img_metadata_raw = [x.get_text() for x in soup.find_all('div', class_='rg_meta notranslate')]
                if len(img_metadata_raw) < 5:
                    logger.warning('Result doesn\'t seem right, I\'m quitting this whole batch')
                    logger.warning('__________________\n{}\n{}\n____________________'.format(soup.title, img_metadata_raw))
                    return None
                else:
                    entry = {}
                    entry['keyword'] = keyword
                    entry['keyword_title'] = keyword.title()
                    # entry['snippet'] = normal_search
                    entry['metadata'] = [json.loads(x) for x in img_metadata_raw]
                    logger.info('_____________________\nGoogling done, Keyword: {}, Total: {}\n_____________________'.format(keyword, len(img_metadata_raw)))
                    return entry
            else:
                logger.warning('Did not scrape {}, result = {}'.format(keyword, _request))
                return None
        except requests.exceptions.ConnectionError:
            logger.warning('ConnectionError when scrapinng {}'.format(keyword))
            return None




# c = GoogleRequest().request_list(['go girl', 'bulletproof'], socks5_port='9001')
# print (c)