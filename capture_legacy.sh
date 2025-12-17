#!/bin/bash
# vitalia-platform/capture_legacy.sh em 2025-12-14 11:48
# -----------------------------------------------------------------------------
# Objetivo: Gerar o arquivo "wellness_legacy.sql" a partir do estado atual
# do container de banco de dados. Isso "congela" os dados legados para
# que outros desenvolvedores possam usar.
# -----------------------------------------------------------------------------

set -e # Para se houver erro

# Definições
CONTAINER_NAME="vitalia_db" # Nome do container definido no docker-compose
DB_USER="vitalia_user"
SOURCE_DB="wellness_legacy"
OUTPUT_FILE="docs/migration/wellness_legacy.sql"

echo "📦 Iniciando captura do banco de dados legado..."

# Verifica se o diretório de destino existe
mkdir -p docs/migration

# Executa o pg_dump dentro do container
# Flags utilizadas:
# --clean: Inclui comandos DROP TABLE antes dos CREATE (limpeza)
# --if-exists: Evita erros se a tabela não existir ao tentar dropar
# --no-owner: Remove comandos de alteração de dono (evita erros de permissão em outros PCs)
# --no-privileges: Remove comandos de grant/revoke (simplifica)
docker compose exec -T db pg_dump \
    -U "$DB_USER" \
    -d "$SOURCE_DB" \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    > "$OUTPUT_FILE"

echo "✅ Sucesso! Arquivo gerado em: $OUTPUT_FILE"
echo "   Tamanho do arquivo: $(du -h $OUTPUT_FILE | cut -f1)"
echo "   Agora faça o commit deste arquivo no Git."