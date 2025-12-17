#!/bin/bash
# backend/run_server.sh em 2025-12-14 11:48
# Script de inicialização Vitalia Backend

set -e

# Carrega variáveis
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

# Garante diretório de chaves
if [ ! -d "$CRYPTO_KEY_PATH" ]; then
    echo "Criando diretório de chaves em $CRYPTO_KEY_PATH..."
    mkdir -p "$CRYPTO_KEY_PATH"
fi

# Gera chaves se não existirem (usando o manage.py do django-crypto-fields)
# Nota: O comando generate_keys precisa que o app esteja instalado.
# Se for a primeira execução, pode falhar se o banco não estiver pronto, 
# mas o django-crypto-fields costuma lidar bem.
echo "Verificando chaves de criptografia..."
python manage.py generate_keys || echo "Aviso: Verifique a configuração de chaves."

# Migrações
echo "Aplicando migrações..."
python manage.py migrate

# Inicia Daphne
echo "Iniciando servidor Vitalia (Daphne) em 0.0.0.0:8000..."
daphne -b 0.0.0.0 -p 8000 config.asgi:application
