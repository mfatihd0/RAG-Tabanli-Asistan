# RAG Tabanlı Döküman Analizi Asistanı

Bu projenin amacı, kurum içi belgelerin veya akademik makalelerin RAG tabanlı bir asistan tarafından okunarak kullanıcının bir arayüz aracılığı ile sorduğu sorulara yanıt alabilmesidir.

## Öne Çıkanlar

- **Çoklu Sohbet Yönetimi:** Birden fazla sohbet açılabilir, geçmiş sohbetlerinize geri dönebilir ve dilediğiniz zaman silebilirsiniz.
- **Sohbete Özel Dokümanlar:** Yüklediğiniz dokümanlar sadece o sohbete özel olarak ayrıştırılır. Sorulan sorular diğer sohbetlerdeki dosyalarla karışmaz.
- **MD5 Hashing:** Aynı doküman birden fazla kez yükleseniz bile sistem bunu algılar ve vektör veritabanını şişirmemek için tekrar işlemeyi reddeder.
- **Çöp Toplama:** Bir sohbet silindiğinde içindeki dokümanlar başka hiçbir sohbette kullanılmıyorsa veritabanında otomatik olarak tamamen silinir.
- **Kaynak Gösterimi:** Yapay zeka bir cevap verdiğinde bu cevabı dokümanın hangi dosyasından ve kaçıncı sayfasından aldığını listere.

## Kulanılan Teknolojiler

* **Dil:** Python 3.14
* **Framework:** LangChain
* **Vector Database:** ChromaDB
* **LLM:** Llama-3.3-70B-versatile (Groq API)
* **Embedding** all-MiniLM-L6-v2 (HuggingFace, Local)
* **UI:** Streamlit

## Sistem Mimarisi

Aşağıdaki akış diyagramı, sistemin veri hazırlama ve soru-cevap boru hatlarının nasıl çalıştığını göstermektedir

![RAG Sistem Mimarisi](assets/flowchart.svg)

## Kurulum ve Çalıştırma

**Kütüphane Kurulumu**

Terminalde aşağıdaki komutu çalıştırarak gerekli kütüphaneleri yükleyin:

python -m pip install -r requirements.txt

**API Ayarları**

Projenizin ana dizininde bir .env dosyası oluşturun ve Groq API anahtarınızı içine yapıştırın:

GROQ_API_KEY="API_Key"

**Uygulamayı Başlatma**

Arayüzü başlatmak için terminale şu komutu yazın:

streamlit run src/ui/ui.py


