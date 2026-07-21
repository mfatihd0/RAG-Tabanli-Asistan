import os
import sys
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..","..")
if project_root not in sys.path:
    sys.path.append(project_root)

from src.retriever.embedding_and_storing import load_vectorstore   

load_dotenv()

def docs_for_prompt(docs):
    """vector storedan gelen chunk listesini llm'in okuyacağı dile çevirir"""
    formatted_chunks = []
    for i, doc in enumerate(docs, start=1):
        src_file = doc.metadata.get("src_file", "dosya hatası")
        page_num = doc.metadata.get("page_number", "sayfa hatası")

        chunk_str = (
            f"parça: {i} | kaynak: {src_file} | sayfa: {page_num}\n"
            f"{doc.page_content}\n"
        )
        formatted_chunks.append(chunk_str)

    return "\n".join(formatted_chunks)    

def ask_to_rag(query, vectorestore, session_id="genel", k=5):
    """kullanıcı sorusunu alır, benzer chunkları bulur ve llm'e gönderir"""

    # 1-vectore store'dan top-k = 5 ile parçaları bul
    print(f"'{query}' sorgusu için döküman taraması (Oturum: {session_id})")
    search_filter = {"$or": [{"session_id": "genel"}, {"session_id": session_id}]}
    relevant_docs = vectorestore.similarity_search(query, k=k, filter=search_filter)

    if not relevant_docs:
        return "dökümanlarda bu sorguyla alakalı bilgi yok", []
    
    # 2-bulunan chunkları llm promptu için tek bir bağlamda birleştir
    context_text = docs_for_prompt(relevant_docs)

    # 3-llm için prompt şablonu hazırlıyoruz
    system_instruction = """Sen, dokümanlara dayanarak soruları cevaplayan profesyonel bir yapay zeka asistanısın.
    Sana aşağıda "BAĞLAM (Doküman Parçaları)" başlığı altında bazı metin parçaları verilecektir.

    BU KURALLARA KESİNLİKLE UY:
    - Sadece ve sadece aşağıda verilen BAĞLAM içerisindeki bilgilere dayanarak cevap ver.
    - Eğer sorunun cevabı verilen bağlam metinlerinde yoksa, sadece "Verilen dokümanlarda bu sorunun cevabına dair bilgi bulunmamaktadır." de. KESİNLİKLE uydurma yapma ve BİLGİ YOKSA ASLA KAYNAK (dosya adı, sayfa numarası) BELİRTME!
    - Cevabını verirken okunaklı ve net bir Türkçe kullan."""

    human_template ="""BAĞLAM (Doküman Parçaları): {context}
    
    KULLANICI SORUSU: {question}
    
    lütfen yukarıdaki bağlam metinlerini inceleyerek sorumu kurallara uygun şekilde cevapla:"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", human_template)
    ])

    # 4-llm modeli tanımlama
    llm = ChatGroq(
        model = "llama-3.3-70b-versatile",
        temperature = 0.2
    )

    chain = prompt | llm

    # 5-llm'e isteği yolla ve cevap al
    print("\nDökümanlar okunuyor ve cevap hazırlanıyor...\n")
    response = chain.invoke({"context": context_text, "question": query})

    # çıktı liste formatındaysa text kısmını alınır
    answer_content = response.content
    if isinstance(answer_content, list):
        answer_content = answer_content[0]["text"]

    return answer_content, relevant_docs     

if __name__ == "__main__":

    # test
    vectorstore_dir = os.path.join(project_root, "data", "vectorstore")

    if not os.path.exists(vectorstore_dir):
        print(f" vektör database bulunamadı: {vectorstore_dir}")
        exit()

    vstore = load_vectorstore(vectorstore_dir)

    # örnek sorular
    test_queries = [
        "hangi durumlarda ceza yerim?"
    ]

    for q in test_queries:
        answer, docs = ask_to_rag(q, vstore, k=10)

        print(f" Kullanılan kaynak parça sayısı: {len(docs)}")
        for idx, d in enumerate(docs, 1):
            print(f"    [{idx}] {d.metadata.get('src_file')} (Sayfa: {d.metadata.get('page_number')})")

        print(f"\nRAG Asistan cevabı:\n{answer}\n") 
    
