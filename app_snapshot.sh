#!/bin/bash
# vitalia-platform/app_snapshot.sh em 2025-12-14 11:48
# vitalia - snapshot do código fonte (clean backup)

# ==============================================================================
# VITALIA PLATFORM - SNAPSHOT DO CÓDIGO FONTE (CLEAN BACKUP) em 2025-12-14 11:48
# ==============================================================================
# Este script cria um pacote compactado da aplicação, EXCLUINDO automaticamente:
# - Ambientes Virtuais e Dependências (node_modules, .venv)
# - Arquivos de Bloqueio (package-lock.json) -> Força recriação limpa no restore
# - Arquivos de Build e Cache
# - Dados locais
# ==============================================================================

# Configurações
BACKUP_ROOT="./backups/source_code"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
SNAPSHOT_NAME="vitalia_source_v1_$TIMESTAMP.tar.gz"
PROJECT_DIR="."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   VITALIA - GERADOR DE SNAPSHOT LIMPO (SOURCE)       ${NC}"
echo -e "${BLUE}======================================================${NC}"

# 1. Preparar Diretório
mkdir -p "$BACKUP_ROOT"

echo -e "${YELLOW}[INFO] Analisando estrutura do projeto...${NC}"
echo -e "${YELLOW}[INFO] O arquivo será salvo em: $BACKUP_ROOT/$SNAPSHOT_NAME${NC}"
echo -e "${YELLOW}[INFO] Iniciando compactação (ignorando dependências e lockfiles)...${NC}"

# 2. Executar o Tar com Exclusões
tar -czf "$BACKUP_ROOT/$SNAPSHOT_NAME" \
    --exclude='./backups' \
    --exclude='./.git' \
    --exclude='./.idea' \
    --exclude='./.vscode' \
    --exclude='./.venv' \
    --exclude='./backend/.venv' \
    --exclude='./backend/venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='*.log' \
    --exclude='celerybeat.pid' \
    --exclude='celerybeat-schedule' \
    --exclude='./frontend/node_modules' \
    --exclude='./frontend/package-lock.json' \
    --exclude='./frontend/yarn.lock' \
    --exclude='./frontend/pnpm-lock.yaml' \
    --exclude='./frontend/.next' \
    --exclude='./frontend/out' \
    --exclude='./frontend/build' \
    --exclude='./frontend/.turbo' \
    --exclude='./postgres_data' \
    --exclude='./redis_data' \
    --exclude='./ollama_data' \
    --exclude='./whatsapp_session' \
    --exclude='.DS_Store' \
    "$PROJECT_DIR"

# 3. Validação e Feedback
if [ -f "$BACKUP_ROOT/$SNAPSHOT_NAME" ]; then
    FILE_SIZE=$(du -h "$BACKUP_ROOT/$SNAPSHOT_NAME" | cut -f1)
    
    echo -e "${GREEN}======================================================${NC}"
    echo -e "${GREEN} SNAPSHOT CRIADO COM SUCESSO! ${NC}"
    echo -e "${GREEN} Arquivo: $SNAPSHOT_NAME ${NC}"
    echo -e "${GREEN} Tamanho Final: $FILE_SIZE ${NC}"
    echo -e "${GREEN}======================================================${NC}"
else
    echo -e "${RED}[ERRO] Falha ao criar o arquivo de snapshot.${NC}"
    exit 1
fi