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

if "activate_session_id" not in st.session_state:
    if not st.session_state.chat_history:
        new_id, new_name = create_session("Sohbet 1")
        st.session_state.chat_history[new_id] = {"name": new_name, "messages": []}
        st.session_state.active_session_id = new_id
    else:
        st.session_state.active_session_id = list(st.session_state.chat_history.keys())[-1]


with st.sidebar:
    st.title(" Oturumlar")

    if st.button ("+ Yeni Sohbet Başlat", use_container_width=True):
        isim = f"Sohbet {len(st.session_state.chat_history) + 1}"
        new_id, new_name = create_session(isim)
        st.session_state.chat_history[new_id] = {"name": new_name, "messages": []}
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

    st.markdown(" + Sohbete Dosya Ekle")
    uploaded_file = st.file_uploader("PDF Yükle", type=["pdf"])

    if uploaded_file:
        with st.spinner("Dosya yükleniyor..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            loader = PyPDFLoader(tmp_path)
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
            docs = loader.load_and_split(text_splitter)

            active_id = st.session_state.active_session_id
            for doc in docs:
                doc.metadata["session_id"] = active_id
                doc.metadata["src_file"] = uploaded_file.name 

            vstore.add_documents(docs)

            os.remove(tmp_path)
            st.success(f"{uploaded_file.name} dosyanız eklendi.")


# chat ui
st.title(" RAG ANALİZ ASİSTANI")
active_session = st.session_state.active_session_id

for message in st.session_state.chat_history[active_session]["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query := st.chat_input("Doküman hakkında soru sorun..."):
    st.session_state.chat_history[active_session]["messages"].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Dokümanlar inceleniyor..."):
            answer, docs = ask_to_rag(query, vstore, session_id = active_session, k=5)

            if isinstance(answer, list):
                answer = answer[0]["text"]

            st.markdown(answer)

            tabu_words = ["bulunmamaktadır", "bilgi yok", "yer almamaktadır", "bahsedilmemektedir", "düzenleme bulunmamaktadır", "bulunamadı"]
            if any (word in answer.lower() for word in tabu_words) or not docs: 
                full_response = answer
            else:
                with st.expander(f" Yararlanılan Kaynaklar: ({len(docs)})"):
                    unique_sources = set()
                    for d in docs:
                        src = d.metadata.get('src_file', 'Dosya')
                        page = d.metadata.get('page_number', '?')
                        unique_sources.add(f" -{src} , (Sayfa: {page})")

                    for src_str in sorted(unique_sources):
                        st.markdown(src_str)
                full_response = f"{answer}\n\n Kaynak sayısı: {len(docs)}*"
    
    st.session_state.chat_history[active_session]["messages"].append({"role": "assistant", "content": full_response})
    save_history(st.session_state.chat_history)