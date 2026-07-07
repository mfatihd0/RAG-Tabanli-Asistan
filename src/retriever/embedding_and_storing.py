import os
import json
import glob
import time
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

def load_chunks_from_json(json_path):
    """json dosyasındaki chunkları doc listesine çevirir"""
    with open(json_path, "r", encoding="utf-8") as f:
        chunk_data = json.load(f)
    
    documents = []
    for chunk in chunk_data:
        content = chunk.get("chunk_text") or chunk.get("content", "")
        documents.append(Document(
            page_content=content,
            metadata=chunk.get("metadata", {})       
        ))

    return documents


def create_vectorstore(documents, persist_dir):
    """embedding işlemi yapılır ve vector store oluşturulur"""
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")
    print(f"embedding işlemi: ({len(documents)} chunk)")
    # ilk batch ile vector store oluştur
    batch_size = 50
    first_batch = documents[:batch_size]
    vectorstore = Chroma.from_documents(
        documents=first_batch,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    print(f"  batch 1/{-(-len(documents)//batch_size)} tamamlandı")

    # kalan batch'leri ekle
    for i in range(batch_size, len(documents), batch_size):
        time.sleep(60)  # rate limit için 60 saniye bekle
        batch = documents[i:i + batch_size]
        vectorstore.add_documents(batch)
        print(f"  batch {i//batch_size + 1}/{-(-len(documents)//batch_size)} tamamlandı")
    print(f"vector store oluşturuldu: {persist_dir}")

    return vectorstore


def load_vectorestore(persist_dir):
    """oluşturulmuş vectore store'u diskten yükleyen fonk."""

    embeddings=GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")
    vectorstore=Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )    

    print(f"vectore store yüklendi: {persist_dir}")
    return vectorstore


def test_search(vectorstore, query, k=3):
    """vectorstore üzerinde benzerlik araması yapar (top-k 3)"""

    print(f"\nsoru: {query}")
    
    results = vectorstore.similarity_search(query, k=k)

    for i, doc in enumerate(results, start=1):
        print(f"\nkaynak: {doc.metadata.get('src_file', 'bilinmiyor')}")
        if doc.metadata.get("page_number"):
            print(f"\nsayfa: {doc.metadata['page_number']}")
        print(f"\niçerik: {doc.page_content[:200]}")

    return results


if __name__ == "__main__":
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, "..", "..")

        processed_dir = os.path.join(project_root, "data", "processed")
        vectorstore_path = os.path.join(project_root, "data", "vectorstore")

        # tüm json ve chunkları topla

        all_documents = []
        json_files = glob.glob(os.path.join(processed_dir, "**", "*.json"), recursive=True)

        if not json_files:
            print(f"dosya bulunamadı: {processed_dir}")        
            exit()

        for json_file in json_files:
            print(f"yükleniyor: {os.path.basename(json_file)}")
            docs = load_chunks_from_json(json_file)
            all_documents.extend(docs)

        print(f"\ntoplam chunk sayısı: {len(all_documents)}")

        #vectore store oluşturup kaydet       
        vectorstore = create_vectorstore(all_documents, vectorstore_path)

        #test araması
        test_search(vectorstore, "stajda ne yapmam gerekiyor?")
        test_search(vectorstore, "yoklama cezası var mı?")