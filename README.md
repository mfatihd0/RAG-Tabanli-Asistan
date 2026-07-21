# RAG Tabanlı Döküman Analizi Asistanı

Bu projenin amacı, kurum içi belgelerin veya akademik makalelerin RAG tabanlı bir asistan tarafından okunarak kullanıcının bir arayüz aracılığı ile sorduğu sorulara yanıt alabilmesidir.

## Kulanılan Teknolojiler

* **Dil:** Python 3.14
* **Framework:** LangChain
* **Vector Database:** ChromaDB
* **LLM:** Llama-3.3-70B-versatile
* **UI:** Streamlit

## Sistem Mimarisi

Aşağıdaki akış diyagramı, sistemin veri hazırlama ve soru-cevap boru hatlarının nasıl çalıştığını göstermektedir

![RAG Sistem Mimarisi](assets/flowchart.svg)

## Kurulum ve Çalıştırma

**Kütüphane Kurulumu**

python -m pip install -r requirements.txt

**API Kurulumu**

.env dosyası oluşturun ve API_KEY'inizi girin. 

GROQ_API_KEY="api_key"


