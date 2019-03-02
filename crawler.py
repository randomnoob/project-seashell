import argparse
import os
from multiprocessing import Pool
import logging
import traceback
logger = logging.getLogger(__name__)
from initsocks.initsocks import SockSpin
from crawler_helper import batch_split, all_dirs, all_files, get_filenames, make_dir, check_make_dir, read_sort_filter_resave_keywords, save_json, filterout_downloaded, get_numfiles, balance_check, roundrobin
from engine import GoogleRequest
import pprint
pp = pprint.PrettyPrinter(indent=3)



class Crawler:
    def __init__(self, ssh_dump=None, keyword_filename='keywords.txt', n_threads=4, keywords_per_session=20, download_dir='download'):
        """
        :param n_threads: Number of threads to download.
        :param do_google: Download from google.com (boolean)
        """
        self.engine = GoogleRequest()
        self.keyword_filename = keyword_filename
        self.keywords_filepath = os.path.join(os.getcwd(), keyword_filename)
        self.n_threads = n_threads
        self.download_path = os.path.join(os.getcwd(), download_dir)
        check_make_dir(self.download_path) #Create download directory if not exist
        self.kps = keywords_per_session

        if ssh_dump:
            self.num_ssh = round(n_threads*2)
            sockspinner = SockSpin(ssh_dump_filename=ssh_dump, num_socks=self.num_ssh)
            self.ssh_list = sockspinner.spin_socks()


    def crawl_list(self, keyword_list, socks5_port=''):
        logger.warning('------------|||||SOCKS PORT : {}'.format(socks5_port))
        scraped = self.engine.request_list(keyword_list, socks5_port)
        for item in scraped:
            if item[0] and item[1]:
                save_json(download_dirpath=self.download_path, filename=item[0], data=item[1])
        return True

    def crawl_stub(self, args):
        # print('ARGS : {}'.format(args))
        return self.crawl_list(keyword_list=args[0], socks5_port=args[1])

    def pool_crawl(self):
        keywords = filterout_downloaded(self.download_path, self.keywords_filepath)
        
        try:
            kw_chunks = batch_split(keywords, n_size=self.kps)
            paired_kwchunks = roundrobin(kw_chunks, self.ssh_list)
            pool = Pool(processes=self.n_threads)
            # pool.map_async(self.download, ssh_pair)
            pool.map_async(self.crawl_stub, paired_kwchunks)
            pool.close()
            pool.join()
            logger.info('Pool Joined')
            logger.info('End Program')
            if not balance_check(self.download_path, self.keywords_filepath):
                self.pool_crawl()

        except AttributeError: #no self.ssh_list
            logger.warning('Crawling without proxies')
            self.crawl_list(keywords)



