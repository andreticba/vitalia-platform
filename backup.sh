#!/bin/bash
# /vitalia-platform/backup.sh em 2025-12-14 11:48

# ==============================================================================
# VITALIA PLATFORM - SCRIPT DE BACKUP INTEGRAL em 2025-12-13 18:30
# ==============================================================================
# Este script realiza o backup de:
# 1. Banco de Dados PostgreSQL (Dump completo)
# 2. Arquivos de Mídia (Uploads de exames, avatares)
# 3. Chaves de Criptografia (CRÍTICO: Sem isso, o banco é ilegível)
# 4. Arquivos de Ambiente (.env)
# ==============================================================================

# Configurações
BACKUP_ROOT="./backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_NAME="vitalia_backup_$TIMESTAMP"
TARGET_DIR="$BACKUP_ROOT/$BACKUP_NAME"
CONTAINER_DB_NAME="vitalia_db" # Nome definido no docker-compose.yml
DB_USER="vitalia_user"         # Usuário definido no .env

# Cores para logs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[INFO] Iniciando processo de backup da Vitalia...${NC}"
echo -e "${YELLOW}[INFO] Timestamp: $TIMESTAMP${NC}"

# 1. Criar diretório de destino
mkdir -p "$TARGET_DIR"

# 2. Backup do Banco de Dados (PostgreSQL)
echo -e "${YELLOW}[1/4] Realizando Dump do Banco de Dados...${NC}"
if docker compose exec -T db pg_dump -U "$DB_USER" vitalia_db > "$TARGET_DIR/database.sql"; then
    echo -e "${GREEN}[OK] Dump do banco realizado com sucesso.${NC}"
else
    echo -e "${RED}[ERRO] Falha ao realizar dump do banco. Verifique se o container '$CONTAINER_DB_NAME' está rodando.${NC}"
    rm -rf "$TARGET_DIR"
    exit 1
fi

# 3. Backup das Chaves de Criptografia (CRÍTICO)
echo -e "${YELLOW}[2/4] Copiando Chaves de Criptografia (encryption_keys)...${NC}"
if [ -d "encryption_keys" ]; then
    cp -r encryption_keys "$TARGET_DIR/"
    echo -e "${GREEN}[OK] Chaves copiadas.${NC}"
else
    echo -e "${RED}[PERIGO] Diretório 'encryption_keys' não encontrado na raiz! O backup pode ser inútil sem as chaves.${NC}"
    # Não aborta, mas avisa
fi

# 4. Backup de Mídia e Arquivos Estáticos
echo -e "${YELLOW}[3/4] Copiando Arquivos de Mídia (backend/media)...${NC}"
if [ -d "backend/media" ]; then
    mkdir -p "$TARGET_DIR/media"
    cp -r backend/media/* "$TARGET_DIR/media/" 2>/dev/null || :
    echo -e "${GREEN}[OK] Mídia copiada.${NC}"
else
    echo -e "${YELLOW}[AVISO] Diretório de mídia não encontrado ou vazio.${NC}"
fi

# 5. Backup das Variáveis de Ambiente
echo -e "${YELLOW}[4/4] Copiando configurações de ambiente (.env)...${NC}"
if [ -f "backend/.env" ]; then
    cp backend/.env "$TARGET_DIR/backend.env"
fi
if [ -f "frontend/.env.local" ]; then
    cp frontend/.env.local "$TARGET_DIR/frontend.env.local"
fi

# 6. Compactação Final
echo -e "${YELLOW}[INFO] Compactando arquivo final...${NC}"
cd "$BACKUP_ROOT"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME" # Remove a pasta temporária não compactada
cd ..

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN} BACKUP CONCLUÍDO COM SUCESSO! ${NC}"
echo -e "${GREEN} Arquivo: $BACKUP_ROOT/$BACKUP_NAME.tar.gz ${NC}"
echo -e "${GREEN}======================================================${NC}"

# 7. (Opcional) Limpeza de backups antigos (manter últimos 7 dias)
find "$BACKUP_ROOT" -type f -name "*.tar.gz" -mtime +7 -delete
