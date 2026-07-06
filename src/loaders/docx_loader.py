import os
import json
import re
from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def clean_text(text):
    """metnin içindeki gereksiz boşlukları ve satır atlamalarını temizleyen fonksiyon"""
    text = re.sub(r'\n{3,}','\n\n', text)  # 3 ten fazla enter varsa 2 ye düşürecek, aşağı yönde
    text = re.sub(r' {2,}',' ', text)  # ekstra yan yana boşlukları teke düşürüyor, 2 den fazla
    return text.strip()


def table_to_text(table):
    """docx içindeki tabloyu metne çeviren fonksiyon"""
    rows = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        rows.append(" | ".join(cells))
    return "\n".join(rows)


def iter_block_items(parent):
    """bu fonksiyonun amacı paragraf ve tabloları sırayla döndürmeyi sağlamaktır"""

    body = parent.element.body
    for child in body.iterchildren():
        if child.tag.endswith('}p'): # paragraf kısmı
            yield Paragraph(child, parent)

        elif child.tag.endswith('}tbl'): # tablo kısmı
            yield Table(child, parent)


def process_docx(file_path, output_dir):
    """docx dosyasını okuyup temizledikten sonra chunklara ayırır ve json formatına çevirir"""
    
    docx_file = DocxDocument(file_path)

    parts = []
    for block in iter_block_items(docx_file):
        if isinstance(block, Paragraph):
            if block.text.strip() != "":
                parts.append(block.text)

        elif isinstance(block, Table):
            parts.append(table_to_text(block))

    raw_text = "\n\n".join(parts)
    cleaned = clean_text(raw_text)                    

    doc = Document(
        page_content=cleaned,
        metadata={
            "src_file": os.path.basename(file_path),
            "doc_type": "docx"
        }
    )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    chunks = text_splitter.split_documents([doc])
    print(f"toplam chunk sayısı: {len(chunks)}")

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "docx_chunks_output.json")

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

    input_path = os.path.join(current_dir, "..", "..","data","raw","docx","staj_plan.docx")
    output_path = os.path.join(current_dir, "..", "..","data","processed")

    if os.path.exists(input_path):
        process_docx(input_path, output_path)
    else:
        print(f"Dosya bulunamadı: {input_path}")