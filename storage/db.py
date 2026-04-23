import os
import json

# Tenta carregar o dotenv, mas não falha se não estiver instalado
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MONGO_URI = os.environ.get("MONGO_URI")
LOCAL_DB = os.environ.get("LOCAL_DB", "false").lower() == "true"

# Fallback para constantes do PyMongo
ASCENDING = 1
DESCENDING = -1

try:
    from pymongo import MongoClient
    import pymongo
    ASCENDING = pymongo.ASCENDING
    DESCENDING = pymongo.DESCENDING
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

class LocalCursor:
    def __init__(self, data):
        self.data = data

    def sort(self, field, direction=1):
        reverse = direction == -1
        self.data = sorted(self.data, key=lambda x: x.get(field) if x.get(field) is not None else 0, reverse=reverse)
        return self

    def __iter__(self):
        return iter(self.data)

class LocalCollection:
    def __init__(self, name):
        self.name = name
        self.file_path = os.path.join("data", f"{name}.json")
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def _load(self):
        try:
            if not os.path.exists(self.file_path):
                return []
            with open(self.file_path, "r") as f:
                content = f.read()
                if not content:
                    return []
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save(self, data):
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def find(self, query=None):
        data = self._load()
        return LocalCursor(data)

    def update_one(self, filter, update, upsert=False):
        data = self._load()
        found = False
        new_values = update.get("$set", {})
        
        for i, doc in enumerate(data):
            match = True
            for k, v in filter.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                data[i].update(new_values)
                found = True
                break
        
        if not found and upsert:
            new_doc = filter.copy()
            new_doc.update(new_values)
            if "_id" in filter and "_id" not in new_doc:
                new_doc["_id"] = filter["_id"]
            data.append(new_doc)
            
        self._save(data)

class LocalDatabase:
    def __getitem__(self, name):
        return LocalCollection(name)

    def get_default_database(self):
        return self

if LOCAL_DB or not MONGO_URI:
    if LOCAL_DB:
        print(" [DB] Modo Local Ativado (LOCAL_DB=true)")
    else:
        print(" [DB] MONGO_URI não encontrada. Usando Banco Local (JSON)")
    db = LocalDatabase()
else:
    if not PYMONGO_AVAILABLE:
        print(" [AVISO] Pymongo não instalado. Usando Banco Local (JSON)")
        db = LocalDatabase()
    else:
        client = MongoClient(MONGO_URI)
        db = client.get_default_database()
