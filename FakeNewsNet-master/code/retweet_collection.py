import json
import logging
from twython import TwythonError, TwythonRateLimitError # API ile etkileşimde bulunmak için kullanılır.


from tweet_collection import Tweet #tweetleri temsil eder.
from resource_server.util.TwythonConnector import TwythonConnector
from resource_server.util.util import create_dir, Config, multiprocess_data_collection

from resource_server.util.util import DataCollector # sınıfı, belirli bir veri türünü toplamak için temel bir sınıftır. 
from resource_server.util import Constants

"""
    Belirli bir tweet'in retweet'lerini toplamak ve bu retweet'leri bir JSON dosyasına kaydetmek için kullanılan fonksiyon.

    Parameters:
    - tweet (Tweet): Retweet'leri toplanacak olan tweet nesnesi.
    - config (Config): Ayarları içeren bir Config nesnesi.
    - twython_connector (TwythonConnector): TwythonConnector nesnesi, Twitter API ile bağlantı kurmak için kullanılır.

    Returns:
    - None
    """
def dump_retweets_job(tweet: Tweet, config: Config, twython_connector: TwythonConnector):
    retweets = []
    connection = None
    try:
        connection = twython_connector.get_twython_connection("get_retweet") # # Twitter API ile bağlantı kur.
        retweets = connection.get_retweets(id=tweet.tweet_id, count=100, cursor=-1) # Belirli bir tweet'in retweet'lerini al.

    except TwythonRateLimitError:
        logging.exception("Twython API rate limit exception - tweet id : {}".format(tweet.tweet_id)) # # Twitter API rate limit hatası durumunda logla.

    except Exception:
        logging.exception(
            "Exception in getting retweets for tweet id %d using connection %s" % (tweet.tweet_id, connection)) # # Diğer hata durumlarında logla.

    retweet_obj = {"retweets": retweets} ## Retweet'leri içeren bir sözlük oluştur.
    ## Retweet'leri saklamak için dizinleri oluştur.
    dump_dir = "{}/{}/{}/{}".format(config.dump_location, tweet.news_source, tweet.label, tweet.news_id)
    retweet_dir = "{}/retweets".format(dump_dir)
    create_dir(dump_dir)
    create_dir(retweet_dir)
    json.dump(retweet_obj, open("{}/{}.json".format(retweet_dir, tweet.tweet_id), "w")) ## JSON dosyasına retweet'leri kaydet.

"""
    Belirli bir haber listesindeki tweet'lerin retweet'lerini toplamak için kullanılan fonksiyon.

    Parameters:
    - news_list (list): Retweet'leri toplanacak haber nesnelerinin listesi.
    - news_source (str): Haber kaynağının adı.
    - label (str): Haberlerin etiketi.
    - config (Config): Ayarları içeren bir Config nesnesi.

    Returns:
    - None
    """
def collect_retweets(news_list, news_source, label, config: Config):
    create_dir(config.dump_location) # # Dökümanları saklamak için gerekli dizinleri oluştur.
    create_dir("{}/{}".format(config.dump_location, news_source))
    create_dir("{}/{}/{}".format(config.dump_location, news_source, label))

    save_dir = "{}/{}/{}".format(config.dump_location, news_source, label)

    tweet_id_list = []
  # Her bir haber nesnesi için döngü.
    for news in news_list:
        for tweet_id in news.tweet_ids:   # Her bir haber nesnesi için döngü.
            tweet_id_list.append(Tweet(tweet_id, news.news_id, news_source, label))  # Tweet ID'leri içeren bir liste oluştur ve tweet nesneleri ile doldur.

    multiprocess_data_collection(dump_retweets_job, tweet_id_list, (config, config.twython_connector), config)    # Multiprocessing kullanarak retweet'leri topla.

"""
    RetweetCollector sınıfı, belirli bir haber listesindeki tweet'lerin retweet'lerini toplamak için kullanılır.
    DataCollector sınıfından türetilmiştir.

    Attributes:
    - config (Config): Ayarları içeren bir Config nesnesi.

    Methods:
    - __init__(self, config): Sınıfın başlatıcı metodu.
    - collect_data(self, choices): Belirli bir haber listesindeki tweet'lerin retweet'lerini toplamak için kullanılan metot.
    """

class RetweetCollector(DataCollector):

    def __init__(self, config):
        super(RetweetCollector, self).__init__(config)

    def collect_data(self, choices):
        for choice in choices:  # Seçeneğe ait haber listesini yükle.
            news_list = self.load_news_file(choice)
            collect_retweets(news_list, choice["news_source"], choice["label"], self.config) # collect_retweets fonksiyonu ile retweet'leri topla.
"""
        Belirli bir haber listesindeki tweet'lerin retweet'lerini toplamak için kullanılan metot.

        Parameters:
        - choices (list): Retweet'leri toplanacak olan haber nesnelerinin seçenekleri.

        Returns:
        - None
        """
