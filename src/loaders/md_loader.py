import os
import json 
import re
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def clean_text(text):
    """metnin içindeki gereksiz boşlukları ve satır atlamalarını temizleyen fonksiyon"""
    text = re.sub(r'\n{3,}','\n\n', text)  # 3 ten fazla enter varsa 2 ye düşürecek, aşağı yönde
    text = re.sub(r' {2,}',' ', text)  # ekstra yan yana boşlukları teke düşürüyor, 2 den fazla
    return text.strip()

def process_md(file_path, output_dir):
    """md dosyasını okuyup temizledikten sonra chunklara ayırır ve json formatına çevirir"""

    loader = TextLoader(file_path, encoding='utf-8')
    docs = loader.load()

    for doc in docs:
        doc.page_content = clean_text(doc.page_content)
        doc.metadata["src_file"] = os.path.basename(file_path)
        doc.metadata["doc_type"] = "md"

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " ", ""]
    )        

    chunks = text_splitter.split_documents(docs)
    print(f"toplam chunk sayısı: {len(chunks)}")

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "md_chunks_output.json")

    chunk_data = []
    for i, chunk in enumerate(chunks):
        chunk_data.append({
            "chunk_id": i+1,
            "content": chunk.page_content,
            "metadata": chunk.metadata
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunk_data, f, ensure_ascii=False, indent=4)

    print(f"kaydedilen dosya: {output_file}")
    return chunks

if __name__ == "__main__":

    current_dir = os.path.dirname(os.path.abspath(__file__))

    input_path = os.path.join(current_dir, "..", "..","data","raw","md","example.md")
    output_path = os.path.join(current_dir, "..", "..","data","processed", "md")

    if os.path.exists(input_path):
        process_md(input_path, output_path)
    else:
        print(f"Dosya bulunamadı: {input_path}")
    


