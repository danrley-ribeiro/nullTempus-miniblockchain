# Usa uma imagem oficial do Python, versão slim para ser mais leve
FROM python:3.11-slim

# Impede que o Python crie arquivos .pyc em disco
ENV PYTHONDONTWRITEBYTECODE 1
# Garante que os logs printados pelo Python sejam enviados direto pro terminal (importante pro Cloud Run)
ENV PYTHONUNBUFFERED 1

# Estipula o diretório de trabalho principal dentro do container
WORKDIR /app

# Copia e instala apenas os requisitos primeiro (aproveita cache de build do docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do projeto
COPY . .

# Comando que será executado quando o container ligar
CMD ["python", "web_server.py"]
