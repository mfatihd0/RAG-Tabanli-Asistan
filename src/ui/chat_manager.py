import os
import json
import uuid

current_dir = os.path.dirname(os.path.abspath(__file__))
chat_history_file = os.path.join(current_dir, "..","..","data","chat_history.json")

def load_history():
    """kayıtlı historyleri dosyadan okur"""
    
    if not os.path.exists(chat_history_file):
        return {}
    try:
        with open(chat_history_file, "r", encoding="utf-8") as f:
            return json.load(f)
        
    except Exception as e:
        print(f"history hatası: {e}")
        return{}
    
def save_history(history_data):
        """sohbetleri json dosyasına yazar"""
        
        os.makedirs(os.path.dirname(chat_history_file), exist_ok = True)
        with open(chat_history_file, "w",encoding="utf-8")as f:
            json.dump(history_data, f, ensure_ascii=False, indent=4)

def create_session(session_name="Yeni Sohbet"):
        """yeni bir chat başlatır ve unique id üretir"""
        
        session_id = str(uuid.uuid4())
        return session_id, session_name