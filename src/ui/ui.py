import os
import sys
import streamlit as st
import tempfile
import hashlib

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
    st.session_state.active_session_id = None

with st.sidebar:
    st.title(" Sohbetler")

    if st.button ("+ Yeni Sohbet Başlat", use_container_width=True):
        new_id, new_name = create_session("Yeni Sohbet")
        
        st.session_state.chat_history[new_id] = {"name": new_name, "messages": [], "uploaded_files": []}
        st.session_state.active_session_id = new_id
        save_history(st.session_state.chat_history)
        st.rerun()

    st.divider()

    for s_id, s_data in st.session_state.chat_history.items():
        col1, col2 = st.columns([4,1])

        button_text = f" {s_data['name']}" if s_id != st.session_state.active_session_id else f" {s_data['name']}"

        with col1:
            if st.button(button_text, key=f"btn_{s_id}", use_container_width=True):
                st.session_state.active_session_id = s_id
                st.rerun()

        with col2:
            if st.button("✖", key=f"del_{s_id}", use_container_width=True):
                delete_hash = [f.get("hash") for f in s_data.get("uploaded_files", [])]

                for h_code in delete_hash:
                    any_session_use = False
                    for other_sid, other_sdata in st.session_state.chat_history.items():
                        if other_sid != s_id:
                            if any(f.get("hash") == h_code for f in other_sdata.get("uploaded_files", [])):
                    
                                any_session_use=True
                                break
                            
                    if not any_session_use:
                        try:
                            vstore._collection.delete(where={"doc_hash": h_code})
                        except Exception:
                            pass
                
                del st.session_state.chat_history[s_id]
                save_history(st.session_state.chat_history)

                if st.session_state.active_session_id == s_id:
                    st.session_state.active_session_id = None

                st.rerun()
                    
    st.divider()

    if st.session_state.active_session_id is not None:
        active_id = st.session_state.active_session_id
        with st.popover("➕ Bu Sohbete Yeni Dosya Yükle"):
            uploaded_file = st.file_uploader("PDF Yükle", type=["pdf"])
        
        if uploaded_file:

            file_bytes = uploaded_file.getvalue()
            file_hash = hashlib.md5(file_bytes).hexdigest()

            already_in_session = any(f.get("hash") == file_hash 
            for f in st.session_state.chat_history[active_id].get("uploaded_files", []))

            if already_in_session:
                st.info(f" {uploaded_file.name} isimli bu dosya sohbette zaten yüklü")
            else:
                with st.spinner("Dosya sisteme işleniyor..."):
                    is_in_system = False
                    for sid, sdata in st.session_state.chat_history.items():
                        if any(f.get("hash") == file_hash for f in sdata.get("uploaded_files", [])):
                            is_in_system = True
                            break

                    if not is_in_system:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")as tmp_file:
                            tmp_file.write(file_bytes)
                            tmp_path = tmp_file.name

                        loader = PyPDFLoader(tmp_path)
                        text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=400)
                        docs = loader.load_and_split(text_splitter)

                        for doc in docs:
                            doc.metadata["doc_hash"] = file_hash
                            doc.metadata["src_file"] = uploaded_file.name

                        vstore.add_documents(docs)
                        os.remove(tmp_path)
                        
                    new_file_object = {"name": uploaded_file.name, "hash": file_hash}
                    st.session_state.chat_history[active_id]["uploaded_files"].append(new_file_object)
                    save_history(st.session_state.chat_history)
                    st.rerun()

        st.markdown("### Bu Sohbetteki Dokümanlar")
       
        active_files = st.session_state.chat_history[active_id].get("uploaded_files", [])
        
        if not active_files:
            st.info("Bu sohbete henüz bir dosya yüklenmedi.")
        else:
            for dosya in active_files:
                st.markdown(f"- {dosya.get('name', 'Bilinmeyen Dosya')}")
# chat ui
if st.session_state.active_session_id is None:
    st.title("Merhaba! \nYeni bir sohbet başlatın veya sohbetinize devam edin.")
    st.stop()

active_session = st.session_state.active_session_id
sohbet_adi = st.session_state.chat_history[active_session]["name"]

st.title(f" {sohbet_adi}")

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
            hash_list = [f["hash"] for f in 
            st.session_state.chat_history[active_session].get("uploaded_files",[])]
            answer, docs = ask_to_rag(query, vstore, doc_hashes=hash_list, k=10)

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
                            page ="?" 
                        unique_sources.add(f" -{src} , (Sayfa: {page})")

                    for src_str in sorted(unique_sources):
                        st.markdown(src_str)
                full_response = answer
    
    st.session_state.chat_history[active_session]["messages"].append({"role": "assistant", "content": full_response})
    save_history(st.session_state.chat_history)