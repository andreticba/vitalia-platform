# backend/Dockerfile em 2025-12-14 11:48

# Estágio 1: Imagem Base
# Usamos uma imagem slim oficial do Python para um tamanho de imagem otimizado.
# A tag específica garante builds reprodutíveis.
FROM python:3.11-slim-bookworm

# Define variáveis de ambiente para otimizar a execução do Python em containers
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema necessárias para compilar algumas bibliotecas Python (ex: psycopg2)
# e depois limpa o cache do apt para manter a imagem leve.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Atualiza o pip para a versão mais recente
RUN pip install --upgrade pip

# Copia apenas o arquivo de requisitos primeiro para aproveitar o cache de camadas do Docker.
# Esta camada só será reconstruída se o requirements.txt mudar.
COPY requirements.txt .

# Instala as dependências do Python
RUN pip install -r requirements.txt

# Cria um usuário e grupo de sistema não-root para executar a aplicação por segurança
RUN addgroup --system django-group && adduser --system --ingroup django-group django-user

# Copia o restante do código da aplicação para o diretório de trabalho
COPY . .

# Concede permissão de execução para o script de inicialização
# e define o usuário não-root como o dono de todos os arquivos da aplicação.
RUN chmod +x run_server.sh
RUN chown -R django-user:django-group /app

# Muda para o usuário não-root
USER django-user

# Define o comando padrão para executar quando o container iniciar
CMD ["./run_server.sh"]
# Expondo a porta 8000 para acesso externo
EXPOSE 8000
