import json
import os
import sys

from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS

from ResourceAllocator import ResourceAllocator
app = Flask(__name__)
cors = CORS(app)
keys_state = dict()

# init_state fonksiyonu num_key adında bir parametre alır ve bu parametre kullanılacak twitter anahtaarının sayısını temsil eder.  
def init_state(num_keys):
    print("No. of twitter keys : {}".format(num_keys))  # ekrana twitter annahtarlarının sayısını yazdırır.
    keys_state["get_retweet"] = ResourceAllocator(num_keys, time_window=905, window_limit=75) # key_state adlı bir söxcüğe getretweet adında bir anahtar ekler. BU anahtar değeri "ResourceAllocator" sınıfından bir örnektir. Time_window: belirli bir eylemin gerçekleştirilebileceği süreyi ifade eder. Time_Window: brlirli bir zaman arasınd agerçkleşecek eylemlerin max sayısını ifade eder.
    keys_state["get_tweet"] = ResourceAllocator(num_keys, time_window=905, window_limit=900)
    keys_state["get_follower_friends_ids"] = ResourceAllocator(num_keys, time_window=920, window_limit=15)
    keys_state["get_followers_ids"] = ResourceAllocator(num_keys, time_window=900, window_limit=15)
    keys_state["get_friends_ids"] = ResourceAllocator(num_keys, time_window=900, window_limit=15)
    keys_state["get_user"] = ResourceAllocator(num_keys, time_window=905, window_limit=900)
    keys_state["get_user_tweets"] = ResourceAllocator(num_keys, time_window=925, window_limit=900)

 #Bu kod, bir Flask uygulamasının bir endpoint'ini (/get-keys) tanımlar. Bu endpoint, HTTP GET isteğine yanıt olarak belirli bir "resource_type" değeri için bir kaynak indeksi sağlar. endpoint:yazılım uygulamasına, servisine veya API'ye erişim sağlayan belirli bir URL'yi ifade eder.
@app.route('/get-keys', methods=['GET'])  #endpoint'i için bir yönlendirme tanımlar ve bu endpoint'e sadece HTTP GET isteklerine izin verir.
def get_key_index():
    args = request.args  # HTTP isteği içindeki argümanları alır. Bu, URL'de geçen parametreleri içerir.

    try:
        type = args["resource_type"] # resource_type: kaynak türü(kategorik) demektir. Örneğin server, database, nertwork.

        allocator = keys_state[type] #keys_state adlı bir yapı içinden, "resource_type" değerine karşılık gelen bir kaynak tahsis ediciyi alır
        resource_index = allocator.get_resource_index() # allocator.get_resource_index(): Alınan kaynak tahsis ediciden get_resource_index metodunu çağırarak bir kaynak indeksi alır

        response = {}  #sonuçları içermek için boş bir sözlük oluşturur.
        if resource_index < 0:
            response["status"] = 404  # not faund
            response["wait_time"] = abs(resource_index) # Beklenen kaynak indeksi negatif olduğu için, bu değer hata durumunda kaç saniye beklenmesi gerektiğini temsil eder.
        else:
            response["status"] = 200
            response["id"] = resource_index

        return jsonify(response)  #Oluşturulan response sözlüğünü JSON formatına dönüştürerek isteği yanıt olarak gönderir.

    except Exception as ex:
        print(ex)

    return jsonify({'result': 500}) #Eğer herhangi bir hata durumu oluşursa, HTTP durum kodunu 500 (Internal Server Error) olarak ayarlar ve bir JSON yanıtı döndürür.


def get_num_process():

    json_object =json.load(open(os.path.dirname(__file__) + "/config.json"))
    return int (json_object["num_twitter_keys"])


if __name__ == '__main__':
    init_state(get_num_process())
    app.run(host='0.0.0.0', port= 5000, debug=True)
