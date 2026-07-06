import os
import json
import re
import pdfplumber
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def clean_text(text):
    """metnin içindeki gereksiz boşlukları ve satır atlamalarını temizleyen fonksiyon"""
    text = re.sub(r'\n{3,}', '\n\n', text)  # 3 ten fazla enter varsa 2 ye düşürecek, aşağı yönde
    text = re.sub(r' {2,}', ' ', text)  # ekstra yan yana boşlukları teke düşürüyor, 2 den fazla
    return text.strip()


def table_to_text(table):
    """tabloyu metne çeviren fonksiyon"""
    rows = []
    for row in table:
        cells =[str(cell).strip() if cell is not None else "" for cell in row]
        rows.append(" | ".join(cells))
    return "\n".join(rows)


def extract_page_content(page):
    """sayfadaki metin ve tabloları sırayla çıkarır ve tablo içi metin tekrarını engeller"""
    tables = page.find_tables()

    # tablo yoksa metni direkt alırız
    if not tables:
        text = page.extract_text()
        return text if text else ""
    
    table_bboxes = [table.bbox for table in tables]


    def not_within_table(obj):
        for bbox in table_bboxes:
            x0, top, x1, bottom = bbox
            obj_top = obj.get("top", 0)
            obj_bottom = obj.get("bottom", 0)
            obj_x0 = obj.get("x0", 0)
            obj_x1 = obj.get("x1", 0)
            if (obj_top >= top and obj_bottom <= bottom and
                obj_x0 >= x0 and obj_x1 <= x1):
                return False
            
        return True
    
    filtered_page = page.filter(not_within_table)
    text_outside_tables = filtered_page.extract_text() 

    parts = []
    if text_outside_tables and text_outside_tables.strip():
        parts.append(text_outside_tables.strip())

    for table in tables:
        table_data = table.extract()
        if table_data:
            parts.append(table_to_text(table_data))

    return "\n\n".join(parts)

def process_pdf(file_path, output_dir):
        docs = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_content = extract_page_content(page)
                if page_content.strip():
                    docs.append(Document(
                        page_content=clean_text(page_content),
                        metadata={
                            "src_file": os.path.basename(file_path),
                            "doc_type": "pdf",
                            "page_number": page_num
                        }
                    ))
                
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
            separators=["\n\n", "\n",".", " ", ""]
        )          

        chunks = text_splitter.split_documents(docs)
        print(f"toplam chunk sayısı: {len(chunks)}")

        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "pdf_chunks_output.json")

        chunk_data = []
        for i, chunk in enumerate(chunks):
            chunk_data.append({
                "chunk_id": i + 1,
                "chunk_text": chunk.page_content,
                "metadata": chunk.metadata
            })

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=4)

        print(f"kaydedilen dosya: {output_file}")    
        return chunks


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))

    input_path = os.path.join(current_dir, "..", "..", "data", "raw", "pdf", "2547_DISIPLIN.pdf")
    output_path = os.path.join(current_dir, "..", "..", "data", "processed", "pdf")

    if os.path.exists(input_path):
        process_pdf(input_path, output_path)

    else:
        print(f"Dosya bulunamadı: {input_path}")    