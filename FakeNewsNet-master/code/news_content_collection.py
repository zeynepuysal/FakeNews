import json
import logging
import time
import requests  # HTTP istekleri göndermek ve almak için kullanılan popüler bir Python modülüdür. Web sitelerinden veri çekmek veya API istekleri göndermek için sıkça kullanılır.
from tqdm import tqdm  #İterasyonlar (for döngüleri vb.) için ilerleme çubukları oluşturmak için kullanılan bir modüldür. Kullanıcıya bir işlemin ne kadar sürede tamamlanacağını göstermek için kullanılır.
from newspaper import Article  #: Haber makalelerini çıkarmak ve analiz etmek için kullanılan bir Python modülüdür. İnternet üzerinden haber sitelerinden makaleleri çekmek ve içeriğini analiz etmek için kullanılır.

#import sys
#sys.path.append("C:/Users/USER/Desktop/FakeNewsNet-master/FakeNewsNet-master/code/resource_server/util")


from resource_server.util.util import DataCollector #u modül, DataCollector adlı bir sınıfı içerir. Bu sınıf muhtemelen veri toplama işlemleri için kullanılır.


from resource_server.util.util import Config, create_dir  #Bu modül, Config adlı bir sınıfı içerir. Bu sınıf, konfigürasyon ayarlarını yönetmek ve kullanmak için tasarlanmış olabilir. creat_dir: Bu fonksiyon, dizin oluşturma işlemleri için kullanılır. Yani, belirtilen bir dizini oluşturur
from resource_server.util import Constants #. Bu dosya içinde genellikle sabit değerler (constants) bulunur, bu değerler genellikle uygulama içinde değişmeyen değerleri temsil eder.

"""
    Verilen URL'den bir makale çıkartma işlemini gerçekleştirir.

    Parameters:
    - url (str): Çıkartılacak makalenin URL'si.

    Returns:
    - dict or None: Çıkartılan makale bilgilerini içeren bir sözlük (dict) veya hata durumunda None.
    """
def crawl_link_article(url):
    result_json = None

    try:
        if 'http' not in url:  # url de http olup olmadığını kontrol et.
            if url[0] == '/':
                url = url[1:]
            try:  # HTTP ile başlamayan URL'yi 'http://' ile dene, ardından 'https://' ile dene
                article = Article('http://' + url)
                article.download()
                time.sleep(2)
                article.parse()
                flag = True
            except:
                logging.exception("Exception in getting data from url {}".format(url))
                flag = False
                pass
            if flag == False:
                try:
                    article = Article('https://' + url)
                    article.download()
                    time.sleep(2)
                    article.parse()
                    flag = True
                except:
                    logging.exception("Exception in getting data from url {}".format(url))
                    flag = False
                    pass
            if flag == False:
                return None  ## Eğer her iki durumda da başarısızsa, None döndür.
        else:
            try:
                article = Article(url)
                article.download()
                time.sleep(2)
                article.parse()
            except:
                logging.exception("Exception in getting data from url {}".format(url))
                return None

        if not article.is_parsed:  ## Makale başarıyla çıkartıldı mı?
            return None
        # Makale bilgilerini çıkart.
        visible_text = article.text
        top_image = article.top_image
        images = article.images
        keywords = article.keywords
        authors = article.authors
        canonical_link = article.canonical_link
        title = article.title
        meta_data = article.meta_data
        movies = article.movies
        publish_date = article.publish_date
        source = article.source_url
        summary = article.summary
         # Çıkartılan bilgileri sözlüğe ekle.
        result_json = {'url': url, 'text': visible_text, 'images': list(images), 'top_img': top_image,
                       'keywords': keywords,
                       'authors': authors, 'canonical_link': canonical_link, 'title': title, 'meta_data': meta_data,
                       'movies': movies, 'publish_date': get_epoch_time(publish_date), 'source': source,
                       'summary': summary}
    except:
        logging.exception("Exception in fetching article form URL : {}".format(url))

    return result_json


def get_epoch_time(time_obj): 
    if time_obj:
        return time_obj.timestamp()

    return None

"""
    Belirli bir URL için web arşivlenmiş sonuçları alır.

    Parameters:
    - search_url (str): Arşivlenmiş verilere erişmek istenen URL.

    Returns:
    - list or None: Arşivlenmiş verilerin bir listesi veya hata durumunda None.
    """
def get_web_archieve_results(search_url):
    try:
        archieve_url = "http://web.archive.org/cdx/search/cdx?url={}&output=json".format(search_url)  # # Web arşiv URL'sini oluştur.

        response = requests.get(archieve_url)  #   # HTTP GET isteği yap ve yanıtı al.
        response_json = json.loads(response.content) #   # Yanıtın içeriğini JSON formatına çevir.

        response_json = response_json[1:]  ## İlk satır genellikle başlık bilgilerini içerir, bu nedenle onu atla.

        return response_json

    except:
        return None

"""
    Belirli bir URL için web arşivinden alınan sonuçlar üzerinden, arşivlenmiş bir versiyonuna yönlendiren bir URL oluşturur.

    Parameters:
    - url (str): Arşivlenmiş versiyonu alınacak olan URL.

    Returns:
    - str or None: Oluşturulan arşivlenmiş versiyon URL'si veya hata durumunda None.
    """
def get_website_url_from_arhieve(url): #sitenin sayfasına gider.
    """ Get the url from http://web.archive.org/ for the passed url if exists."""
    archieve_results = get_web_archieve_results(url) # # Belirli bir URL için web arşiv sonuçlarını al.
    if archieve_results:
        modified_url = "https://web.archive.org/web/{}/{}".format(archieve_results[0][1], archieve_results[0][2]) #  # İlk arşiv sonucunu kullanarak bir URL oluştur.
        return modified_url
    else:
        return None
#Eğer arşiv sonuçları mevcutsa, ilk sonuç üzerinden bir URL oluşturulur. Bu oluşturulan URL, web.archive.org üzerinden belirli bir tarihe ait arşivlenmiş bir versiyonu gösterir.

"""
    Bir haber makalesini orijinal web sitesinden veya web arşivinden alır.

    Parameters:
    - url (str): Makalenin alınacağı URL.

    Returns:
    - dict or None: Makale bilgilerini içeren bir sözlük (dict) veya hata durumunda None.
    """
def crawl_news_article(url):
    news_article = crawl_link_article(url) #  Orijinal haber makalesini al.

    # If the news article could not be fetched from original website, fetch from archieve if it exists.
    ## Eğer orijinal web sitesinden haber makalesi alınamazsa, arşivden almayı dene.
    if news_article is None:
        archieve_url = get_website_url_from_arhieve(url)
        if archieve_url is not None:
            news_article = crawl_link_article(archieve_url)

    return news_article

"""
    Belirli bir haber listesini döngüye alarak her bir haberin içeriğini toplar ve belirli bir konumda saklar.

    Parameters:
    - news_list (list): Toplanacak haber nesnelerinin listesi.
    - news_source (str): Haber kaynağının adı.
    - label (str): Haberlerin etiketi.
    - config (Config): Ayarları içeren bir Config nesnesi.

    Returns:
    - None
    """
def collect_news_articles(news_list, news_source, label, config: Config):
    create_dir(config.dump_location) #create_dir fonksiyonu kullanılarak belirli bir konumda gerekli dizinleri oluştur. Bu dizinler, haber kaynağı adı, etiket ve her bir haber için özel dizinleri içerir.
    create_dir("{}/{}".format(config.dump_location, news_source)) #Haber içeriklerini saklamak için bir ana dizin belirlenir (save_dir).
    create_dir("{}/{}/{}".format(config.dump_location, news_source, label))

    save_dir = "{}/{}/{}".format(config.dump_location, news_source, label)

    for news in tqdm(news_list):
        create_dir("{}/{}".format(save_dir, news.news_id))
        news_article = crawl_news_article(news.news_url)
        if news_article:  ## Haber içeriği varsa, JSON formatında kaydet.
            json.dump(news_article,
                      open("{}/{}/news content.json".format(save_dir, news.news_id), "w", encoding="UTF-8"))



"""
    NewsContentCollector sınıfı, belirli bir yapıda verileri toplamak için kullanılır. DataCollector sınıfından türetilmiştir.

    Attributes:
    - config (Config): Ayarları içeren bir Config nesnesi.

    Methods:
    - __init__(self, config): Sınıfın başlatıcı metodu.
    - collect_data(self, choices): Belirli bir yapıdaki verileri toplamak için kullanılan metot.
    """
class NewsContentCollector(DataCollector):
    
    def __init__(self, config):  ## DataCollector sınıfının başlatıcı metodunu çağır.
        super(NewsContentCollector, self).__init__(config)
    
    def collect_data(self, choices):
        for choice in choices:  # # Her bir seçenek için döngü.
            news_list = self.load_news_file(choice)  ## Seçeneğe ait haber listesini yükle.
            collect_news_articles(news_list, choice["news_source"], choice["label"], self.config)  # # collect_news_articles fonksiyonu ile haber içeriklerini topla.

"""
        Belirli bir yapıdaki verileri toplamak için kullanılan metot.

        Parameters:
        - choices (list): Toplanacak verilerin seçenekleri.

        Returns:
        - None
        """





