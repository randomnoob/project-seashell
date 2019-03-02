# -*- coding: utf-8 -*-
import os
import requests
import shutil
from multiprocessing import Pool
import argparse
# from gcrawl_collect_links import CollectLinks
from gcrawl_googlequest import RequestGoogle
import itertools
from gcrawl_sockspin import SockSpin
import ast
import subprocess
import json

GLOBAL_DEFAULT_KEYWORD_PER_SESSION = 2
GLOBAL_KEYWORDS_FILE = 'combine-shopeed.txt'
GLOBAL_DOWNLOAD_PATH = 'combine-shopeed_download'
# PROXYFIED_SSH = ['', '8123', '8124', '8125', '8126', '8129', '8131', '8136', '8138', '8142']
DEFAULT_PROXYFIED_SSH = ['', '8123', '8124', '8126', '8131', '8136', '8138', '8142']
GLOBAL_SSH_DUMP='KR_FRESH_12-25-2018_4937.txt'
KEYWORD_THRESHOLD = 0.98 # Means 98%
# ssh -D 8125 -f -C -q -N hippo@hippo.thitgaluoc.com

class AutoCrawler:
    def __init__(self, skip_already_exist=True, n_threads=4, keywords_per_session=10,download_path=GLOBAL_DOWNLOAD_PATH, ssh=3):
        """
        :param skip_already_exist: Skips keyword already downloaded before. This is needed when re-downloading.
        :param n_threads: Number of threads to download.
        :param do_google: Download from google.com (boolean)
        :param do_naver: Download from naver.com (boolean)
        """
        self.skip = skip_already_exist
        self.n_threads = n_threads
        self.download_path = download_path
        self.num_keywords_per_session = keywords_per_session
        self.num_ssh = ssh
        sockspinner = SockSpin(ssh_dump_filename=GLOBAL_SSH_DUMP, num_socks=ast.literal_eval(self.num_ssh))
        self.ssh_list = sockspinner.spin_socks()

        # If download_path doesn't exist -> make one
        if not os.path.exists('./{}'.format(self.download_path)):
            os.mkdir('./{}'.format(self.download_path))

    def batch_split(self, iterable, n_size):
        l = len(iterable)
        for ndx in range(0, l, n_size):
            yield iterable[ndx:min(ndx + n_size, l)]

    def roundrobin(self, longer_iterable, shorter_iterable):
        """
        Suppose that longer comes first
        """
        for i, j in zip(longer_iterable, itertools.cycle(shorter_iterable)):
            yield [i,j]

    @staticmethod
    def all_dirs(path):
        paths = []
        for dir in os.listdir(path):
            if os.path.isdir(path + '/' + dir):
                paths.append(path + '/' + dir)

        return paths

    @staticmethod
    def all_files(path):
        paths = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if os.path.isfile(path + '/' + file):
                    paths.append(path + '/' + file)

        return paths

    @staticmethod
    def get_filename(path):
        downloaded = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if os.path.isfile(path + '/' + file):
                    downloaded.append(os.path.splitext(file)[0])
        return downloaded

    @staticmethod
    def make_dir(dirname):
        current_path = os.getcwd()
        path = os.path.join(current_path, dirname)
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def get_keywords(downloaded_keywords, keywords_file=GLOBAL_KEYWORDS_FILE):
        # read search keywords from file
        with open(keywords_file, 'r', encoding='utf-8') as f:
            text = f.read()
            lines = text.split('\n')
            if '' in lines:
                lines.remove('')
            keywords = sorted(set(lines))

        print('{} keywords found: '.format(len(keywords)))

        exclude_downloaded = list(set(keywords)-set(downloaded_keywords))

        print ('{} keywords downloaded/{} keywords in queue for crawling'\
                .format(len(downloaded_keywords), len(keywords)-len(downloaded_keywords)))

        # re-save sorted keywords
        with open(keywords_file, 'w+', encoding='utf-8') as f:
            for keyword in keywords:
                f.write('{}\n'.format(keyword))

        return exclude_downloaded

    def download_from_site(self, keyword_list, proxified_ssh):
        print('**********\nCollecting METADATA... {} from GOOGLE, with SOCKS : {}\n**********'.format(keyword_list, proxified_ssh))
        all_results= RequestGoogle().request_list(keyword_list, proxified_ssh)

        for index, kw in enumerate(keyword_list):
            dirname = '{}/{}'.format(self.download_path, kw)
            if os.path.exists(os.path.join(os.getcwd(), dirname)) and self.skip:
                print('Skipping already existing directory {}'.format(dirname))
                return
            self.save(kw, all_results[index])


    def save(self, filename, data):
        try:
            output_path = '{}/{}.json'.format(self.download_path, filename)
            if len(data['metadata']) > 10:
                with open(output_path, 'w', encoding='utf-8') as output_file:
                    # print ('[DEBUG] Saving file named :  |||{}.json|||'.format(filename))
                    # print (data)
                    json.dump(data, output_file)
                print ('[DEBUG] Saved {}.json'.format(filename))
            else:
                print ('Not saving anything, result doesn\'t seem right')
        except OSError:
            pass #fixme : dirty hacks


    def download(self, args):
        """
        Stub function
        """
        # print ('Passed ARGS : {}'.format(args))
        self.download_from_site(keyword_list=args[0], proxified_ssh=args[1])


    def do_crawling(self):
        downloaded = self.get_filename(self.download_path)
        keywords = self.get_keywords(downloaded)
        kw_chunks = self.batch_split(keywords, n_size=self.num_keywords_per_session)
        ssh_pair = self.roundrobin(kw_chunks, self.ssh_list)

        pool = Pool(self.n_threads)
        # pool.map_async(self.download, ssh_pair)
        pool.map(self.download, ssh_pair)
        pool.close()
        pool.join()
        print('pool join')

        print('End Program')
        return self.balance_check()

    @staticmethod
    def count_files(path) :
        num_files = subprocess.check_output('ls -1 {} | wc -l'.format(path), shell=True)
        return ast.literal_eval(num_files.decode('utf-8').strip())

    def balance_check(self):
        num_downloaded_files = self.count_files(self.download_path)
        with open(GLOBAL_KEYWORDS_FILE, 'r', encoding='utf-8') as kw_file:
            num_keywords = len(list(kw_file.readlines()))
        print ("num_downloaded_files : {} / num_keywords : {}".format(num_downloaded_files, num_keywords))
        if num_downloaded_files/num_keywords > KEYWORD_THRESHOLD:
            return True
        else:
            return self.do_crawling()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip', type=str, default='true',
                        help='Skips keyword already downloaded before. This is needed when re-downloading.')
    parser.add_argument('--nosocks', type=str, default='false',
                        help='Skips keyword already downloaded before. This is needed when re-downloading.')
    parser.add_argument('--ssh', type=str, default=3,
                        help='Spin a number of SOCKS5 proxy through SSH to send requests through.')
    parser.add_argument('--threads', type=int, default=3, help='Number of threads to download.')
    parser.add_argument('--kps', type=int, default=GLOBAL_DEFAULT_KEYWORD_PER_SESSION, help='Number of keywords per browser session.')
    args = parser.parse_args()

    _skip = False if str(args.skip).lower() == 'false' else True
    _nosocks = False if str(args.skip).lower() == 'false' else True
    _threads = args.threads
    _kps = args.kps
    _ssh = args.ssh

    print('Options - skip:{}, threads:{}, SSH :{}, {} keywords per session'.format(_skip, _threads, _ssh, _kps))

    crawler = AutoCrawler(skip_already_exist=_skip, n_threads=_threads, keywords_per_session=_kps, ssh=_ssh)
    crawler.do_crawling()
    crawler.balance_check()
