import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI não encontrada no arquivo .env!")

# Instanciamos o cliente MongoDB. 
# O parâmetro tls=True já é parte do padrão para se conectar com Atlas/GCP via mongos.
client = MongoClient(MONGO_URI)

# O URI já costuma apontar para o banco /nt-data, mas vamos resgatá-lo nativamente.
db = client.get_default_database()
