import os
import sys
import streamlit as st

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..","..")
if project_root not in sys.path:
    sys.path.append(project_root)

from src.retriever.embedding_and_storing import load_vectorstore
from src.llm.generator import ask_to_rag

# sayfa arayüzü
st.set_page_config(page_title="RAG Tabanlı Doküman Botu",layout="centered")
st.title("Doküman Analiz Yapay Zekası")
st.write("Hoşgeldiniz! PDF, docx veya md uzantılı dosyalarınızı buraya atarak yapay zeka tarafından analiz edilmesini sağlayabilirsiniz.")

# vector database yükleme
@st.cache_resource
def get_vectorstore():
    vs_path = os.path.join(project_root, "data", "vectorstore")
    return load_vectorstore(vs_path)

vstore = get_vectorstore()

# sohbet geçmişini hafızada saklama
if "messages" not in st.session_state:
    st.session_state.messages = []

# önceki mesajlara ekrana bas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# kullanıcıdan input alma (soru)
if query := st.chat_input("Doküman ile ilgili sorunuzu buraya yazın..."):
    
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Dokümanlar taranıyor, cevabınız hazırlanıyor..."):
                answer, docs = ask_to_rag(query, vstore, k=5)

                if isinstance(answer, list):
                    answer = answer[0]["text"]

                st.markdown(answer)

                olumsuz_kelimeler = [
                "bulunmamaktadır", "bilgi yok", "yer almamaktadır", 
                "bahsedilmemektedir", "düzenleme bulunmamaktadır", "bulunamadı"
            ]
            
            if any(kelime in answer.lower() for kelime in olumsuz_kelimeler) or not docs:
                # Bilgi yoksa ya da olumsuz cevapsa kaynak kutusu hiç açılmasın!
                full_response = answer
            else:
                # Bilgi varsa kaynakları açılır kutuda göster
                with st.expander(f"🔍 Yararlanılan Kaynakları Göster ({len(docs)} Parça)"):
                    unique_sources = set()
                    for d in docs:
                        src = d.metadata.get('src_file', 'Dosya')
                        page = d.metadata.get('page_number', '?')
                        unique_sources.add(f"- 📄 **{src}** *(Sayfa: {page})*")
                    
                    for src_str in sorted(unique_sources):
                        st.markdown(src_str)
                full_response = f"{answer}\n\n*Yararlanılan Kaynak Sayısı: {len(docs)}*"

    st.session_state.messages.append({"role": "assistant", "content": full_response})