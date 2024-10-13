import json
import logging
import csv
import os
import sys
sys.path.append(r"C:/Users/USER/Desktop/FakeNewsNet-master/FakeNewsNet-master/code/resource_server/util")
from multiprocessing.pool import Pool

from resource_server.util.TwythonConnector import TwythonConnector
from twython import TwythonError, TwythonRateLimitError

from resource_server.util.util import News, create_dir, Config, multiprocess_data_collection

from resource_server.util.util import DataCollector
from resource_server.util import Constants

from resource_server.util.util import equal_chunks

"""
    Tweet sınıfı, bir tweet'i temsil eden bir veri yapısını oluşturur.

    Attributes:
    - tweet_id (str): Tweet'in benzersiz kimliği (ID) veya numarası.
    - news_id (str): Tweet'in bağlı olduğu haberin benzersiz kimliği (ID) veya numarası.
    - news_source (str): Haberin kaynağı.
    - label (str): Haberin etiketi.

    Methods:
    - __init__(self, tweet_id, news_id, news_source, label): Sınıfın başlatıcı metodu.
    """
class Tweet:

    def __init__(self, tweet_id, news_id, news_source, label):
        self.tweet_id = tweet_id
        self.news_id = news_id
        self.news_source = news_source
        self.label = label

"""
    Belirli bir tweet grubunun (tweet_chunk) bilgilerini toplamak ve bu bilgileri belirli bir konumda saklamak için kullanılan fonksiyon.

    Parameters:
    - tweet_chunk (list): Bilgileri toplanacak tweet'leri içeren bir liste.
    - config (Config): Ayarları içeren bir Config nesnesi.
    - twython_connector (TwythonConnector): Twitter API'ye bağlanmak için kullanılan bir TwythonConnector nesnesi.

    Returns:
    - None
    """
def dump_tweet_information(tweet_chunk: list, config: Config, twython_connector: TwythonConnector):
    """Collect info and dump info of tweet chunk containing atmost 100 tweets"""

    tweet_list = []
    for tweet in tweet_chunk: # # Tweet ID'lerini içeren bir liste oluştur.
        tweet_list.append(tweet.tweet_id)
        
   # Twitter API'ye bağlanmak için get_twython_connection metodunu kullan.
        # lookup_status metodu, belirtilen tweet ID'leri için ayrıntılı tweet bilgilerini almak için kullanılır.
    try:
        tweet_objects_map = twython_connector.get_twython_connection(Constants.GET_TWEET).lookup_status(id=tweet_list,
                                                                                                    include_entities=True,
                                                                                                    map=True)['id']
        for tweet in tweet_chunk: # Her bir tweet için döngü.
            tweet_object = tweet_objects_map[str(tweet.tweet_id)]
            if tweet_object: # Tweet nesnesi varsa, bilgileri belirtilen konumda sakla.
                dump_dir = "{}/{}/{}/{}".format(config.dump_location, tweet.news_source, tweet.label, tweet.news_id)
                tweet_dir = "{}/tweets".format(dump_dir)
                create_dir(dump_dir)
                create_dir(tweet_dir)

                json.dump(tweet_object, open("{}/{}.json".format(tweet_dir, tweet.tweet_id), "w"))

    except TwythonRateLimitError:
        logging.exception("Twython API rate limit exception")

    except Exception as ex:
        logging.exception("exception in collecting tweet objects")

    return None

"""
    Belirli bir haber listesinden elde edilen tweet ID'leri üzerinden tweet bilgilerini toplamak ve bu bilgileri belirli bir konumda saklamak için kullanılan fonksiyon.

    Parameters:
    - news_list (list): Tweet bilgilerinin elde edileceği haberleri içeren bir liste.
    - news_source (str): Haberin kaynağı.
    - label (str): Haberin etiketi.
    - config (Config): Ayarları içeren bir Config nesnesi.

    Returns:
    - None
    """
def collect_tweets(news_list, news_source, label, config: Config):  # Dizinleri oluştur.
    create_dir(config.dump_location)
    create_dir("{}/{}".format(config.dump_location, news_source))
    create_dir("{}/{}/{}".format(config.dump_location, news_source, label))

    save_dir = "{}/{}/{}".format(config.dump_location, news_source, label)

    tweet_id_list = []

     # Her bir haber için döngü.
    for news in news_list:
        for tweet_id in news.tweet_ids:  # Haberin tweet ID'lerini içeren bir liste oluştur.
            tweet_id_list.append(Tweet(tweet_id, news.news_id, news_source, label))

    tweet_chunks = equal_chunks(tweet_id_list, 100)  # Tweet ID listesini eşit parçalara ayır.
    multiprocess_data_collection(dump_tweet_information, tweet_chunks, (config, config.twython_connector), config) # Her bir parça için dump_tweet_information fonksiyonunu çoklu işlem (multiprocessing) kullanarak çağır.

"""
    Tweet bilgilerini toplamak için kullanılan TweetCollector sınıfı.

    Attributes:
    - config: Ayarları içeren bir Config nesnesi.

    Methods:
    - __init__(self, config): Sınıfın başlatıcı metodu.
    - collect_data(self, choices): Tweet bilgilerini toplamak için kullanılan metot.
    """
class TweetCollector(DataCollector):
    
    def __init__(self, config):
        super(TweetCollector, self).__init__(config)
    def collect_data(self, choices):
        for choice in choices:  # Her bir haber seçeneği için döngü.
            news_list = self.load_news_file(choice)   # Haber dosyasını yükle.
            collect_tweets(news_list, choice["news_source"], choice["label"], self.config)  # collect_tweets fonksiyonunu kullanarak tweet bilgilerini topla.
"""
        Tweet bilgilerini toplamak için kullanılan metot.

        Parameters:
        - choices: Tweet bilgilerinin toplanacağı haber seçeneklerini içeren bir liste.

        Returns:
        - None
        """










