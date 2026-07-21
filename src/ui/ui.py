import os
import sys
import streamlit as st
import tempfile

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..","..")
if project_root not in sys.path:
    sys.path.append(project_root)

from src.retriever.embedding_and_storing import load_vectorstore
from src.llm.generator import ask_to_rag
from src.ui.chat_manager import load_history, save_history, create_session

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# sayfa arayüzü
st.set_page_config(page_title="RAG Tabanlı Doküman Botu",layout="wide")

# vector database yükleme
@st.cache_resource
def get_vectorstore():
    vs_path = os.path.join(project_root, "data", "vectorstore")
    return load_vectorstore(vs_path)

vstore = get_vectorstore()

# history ve session başlatma
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_history()
    
# Eski sohbetlerde dosya çantası uploaded_files yoksa hata vermemesi için ekleyelim
for s_id, s_data in st.session_state.chat_history.items():
    if "uploaded_files" not in s_data:
        s_data["uploaded_files"] = []
if "active_session_id" not in st.session_state:
    if not st.session_state.chat_history:
        new_id, new_name = create_session("Sohbet 1")
        # YENİ: uploaded_files eklendi
        st.session_state.chat_history[new_id] = {"name": new_name, "messages": [], "uploaded_files": []}
        st.session_state.active_session_id = new_id
    else:
        st.session_state.active_session_id = list(st.session_state.chat_history.keys())[-1]


with st.sidebar:
    st.title(" Oturumlar")

    if st.button ("+ Yeni Sohbet Başlat", use_container_width=True):
        isim = f"Sohbet {len(st.session_state.chat_history) + 1}"
        new_id, new_name = create_session(isim)
        # YENİ: uploaded_files eklendi
        st.session_state.chat_history[new_id] = {"name": new_name, "messages": [], "uploaded_files": []}
        st.session_state.active_session_id = new_id
        save_history(st.session_state.chat_history)
        st.rerun()

    st.divider()

    for s_id, s_data in st.session_state.chat_history.items():
        button_text = f" {s_data['name']}" if s_id != st.session_state.active_session_id else f" {s_data['name']}"

        if st.button(button_text, key=s_id, use_container_width=True):
            st.session_state.active_session_id = s_id
            st.rerun()

    st.divider()

    # AKTİF SOHBETİN DOKÜMANLARINI LİSTELE
    st.markdown("### Bu Sohbetteki Dokümanlar")
    aktif_id = st.session_state.active_session_id
    aktif_dosyalar = st.session_state.chat_history[aktif_id].get("uploaded_files", [])
    
    if not aktif_dosyalar:
        st.info("Bu sohbete henüz özel bir dosya yüklenmedi.")
    else:
        for dosya_ismi in aktif_dosyalar:
            st.markdown(f"-  {dosya_ismi}")


# chat ui
active_session = st.session_state.active_session_id
sohbet_adi = st.session_state.chat_history[active_session]["name"]

# 1. DİNAMİK BAŞLIK (Hangi sohbetteysek onun adı yazar)
st.title(f" {sohbet_adi}")

# 2. ŞIK AÇILIR MENÜ İLE DOSYA YÜKLEME (Popover)
with st.popover("➕ Bu Sohbete Yeni Dosya Yükle"):
    uploaded_file = st.file_uploader("PDF Yükle", type=["pdf"])
    
    if uploaded_file:
        with st.spinner("Dosya sisteme işleniyor..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            loader = PyPDFLoader(tmp_path)
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=400)
            docs = loader.load_and_split(text_splitter)

            for doc in docs:
                doc.metadata["session_id"] = active_session
                doc.metadata["src_file"] = uploaded_file.name 

            vstore.add_documents(docs)
            os.remove(tmp_path)
            
            # Yüklenen dosyayı o sohbetin çantasına ekle ve kaydet
            if uploaded_file.name not in st.session_state.chat_history[active_session]["uploaded_files"]:
                st.session_state.chat_history[active_session]["uploaded_files"].append(uploaded_file.name)
                save_history(st.session_state.chat_history)
                
            st.success(f"{uploaded_file.name} eklendi!")
            st.rerun()  
for message in st.session_state.chat_history[active_session]["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query := st.chat_input("Doküman hakkında soru sorun..."):
    if len(st.session_state.chat_history[active_session]["messages"])==0:
        st.session_state.chat_history[active_session]["name"]=query[:25] + ("..." if len(query)>25 else "")

    st.session_state.chat_history[active_session]["messages"].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Dokümanlar inceleniyor..."):
            answer, docs = ask_to_rag(query, vstore, session_id = active_session, k=10)

            if isinstance(answer, list):
                answer = answer[0]["text"]

            st.markdown(answer)

            tabu_words = ["bulunmamaktadır", "bilgi yok", "yer almamaktadır", "bahsedilmemektedir", "düzenleme bulunmamaktadır", "bulunamadı"]
            if any (word in answer.lower() for word in tabu_words) or not docs: 
                full_response = answer
            else:
                with st.expander(f" Yararlanılan Kaynaklar"):
                    unique_sources = set()
                    for d in docs:
                        src = d.metadata.get('src_file', 'Dosya')
                        page = d.metadata.get('page', -1) +1
                        if page == 0:
                            page == "?" 
                        unique_sources.add(f" -{src} , (Sayfa: {page})")

                    for src_str in sorted(unique_sources):
                        st.markdown(src_str)
                full_response = answer
    
    st.session_state.chat_history[active_session]["messages"].append({"role": "assistant", "content": full_response})
    save_history(st.session_state.chat_history)