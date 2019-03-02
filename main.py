from crawler import Crawler
import argparse

if __name__ == '__main__':

    # ----------------------------
    # LOGGING
    import logging
    from logging import StreamHandler
    from logging.handlers import RotatingFileHandler
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Create the Handler for logging data to a file
    logger_handler = RotatingFileHandler('applog.log', maxBytes=102400, backupCount=5)
    logger_handler.setLevel(logging.DEBUG)

    #Create the Handler for logging data to console.
    console_handler = StreamHandler()
    console_handler.setLevel(logging.INFO)

    logger.addHandler(logger_handler)
    logger.addHandler(console_handler)
    # ----------------------------


    # ----------------------------
    # PARSING ARGUMENTS    
    parser = argparse.ArgumentParser()
    parser.add_argument('--keywordfile', type=str, default='keywords.txt',
                        help='Keyword filename.')
    parser.add_argument('--ssh', type=str, default='false',
                        help='Name of ssh dump file.')
    parser.add_argument('--threads', type=int, default=3, help='Number of threads to run.')
    parser.add_argument('--kps', type=int, default=20, help='Number of keywords per crawling session.')
    parser.add_argument('--downloaddir', type=str, default='download', help='Name of download directory.')
    args = parser.parse_args()

    _kwfile = args.keywordfile
    _ssh = args.ssh
    _threads = args.threads
    _kps = args.kps
    _download_dir = args.downloaddir



    print('Options - downloaddir: {} | keywordfile :{} | SSH:{} | threads :{} | {} keywords per session'.format(_download_dir, _kwfile, _ssh, _threads, _kps))
    crawler = Crawler(ssh_dump=_ssh, keyword_filename=_kwfile, n_threads=_threads, keywords_per_session=_kps, download_dir=_download_dir)
    crawler.pool_crawl()
    # crawler.balance_check()

    # ----------------------------
    # crawler = Crawler(ssh_dump='KR_FRESH_12-25-2018_4937.txt')
    # crawler.pool_crawl()


