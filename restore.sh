#!/bin/bash
# vitalia-platform/restore.sh em 2025-12-14 11:48

# ==============================================================================
# VITALIA PLATFORM - SCRIPT DE RESTAURAÇÃO (RESTORE) em 2025-12-14 11:48
# ==============================================================================
# USO: ./restore.sh <caminho_do_arquivo_tar_gz>
# Exemplo: ./restore.sh ./backups/vitalia_backup_2025-10-25.tar.gz
# ==============================================================================

# Configurações
BACKUP_FILE="$1"
TEMP_DIR="./restore_temp_$(date +%s)"
CONTAINER_DB_NAME="vitalia_db"
DB_USER="vitalia_user"
DB_NAME="vitalia_db"

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Validação de Entrada
if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}[ERRO] Você deve especificar o arquivo de backup.${NC}"
    echo "Uso: ./restore.sh ./backups/arquivo_do_backup.tar.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}[ERRO] Arquivo não encontrado: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${RED}!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!${NC}"
echo -e "${RED} PERIGO: ESTA AÇÃO IRÁ SOBRESCREVER O BANCO DE DADOS ATUAL ${NC}"
echo -e "${RED} E SUBSTITUIR AS CHAVES DE CRIPTOGRAFIA.${NC}"
echo -e "${RED} DADOS CRIADOS APÓS O BACKUP SERÃO PERDIDOS.${NC}"
echo -e "${RED}!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!${NC}"
read -p "Tem certeza absoluta que deseja continuar? (digite 'sim' para confirmar): " CONFIRM
if [ "$CONFIRM" != "sim" ]; then
    echo "Operação cancelada."
    exit 0
fi

echo -e "${YELLOW}[INFO] Iniciando processo de restauração...${NC}"

# 2. Extração do Backup
echo -e "${YELLOW}[1/6] Extraindo arquivos temporários...${NC}"
mkdir -p "$TEMP_DIR"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# O tar cria uma pasta com o nome do backup dentro. Vamos encontrá-la.
EXTRACTED_ROOT=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)

if [ -z "$EXTRACTED_ROOT" ]; then
    echo -e "${RED}[ERRO] Falha ao extrair ou estrutura do backup inválida.${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo -e "${GREEN}[OK] Extraído em: $EXTRACTED_ROOT${NC}"

# 3. Restaurar Chaves de Criptografia (Prioridade Máxima)
echo -e "${YELLOW}[2/6] Restaurando Chaves de Criptografia...${NC}"
if [ -d "$EXTRACTED_ROOT/encryption_keys" ]; then
    # Remove chaves atuais para evitar mistura
    rm -rf encryption_keys
    cp -r "$EXTRACTED_ROOT/encryption_keys" ./
    echo -e "${GREEN}[OK] Chaves restauradas.${NC}"
else
    echo -e "${RED}[ERRO CRÍTICO] Pasta 'encryption_keys' não encontrada no backup! O banco será ilegível.${NC}"
    read -p "Deseja continuar mesmo assim? (s/n): " CONT_KEYS
    if [ "$CONT_KEYS" != "s" ]; then rm -rf "$TEMP_DIR"; exit 1; fi
fi

# 4. Restaurar Variáveis de Ambiente
echo -e "${YELLOW}[3/6] Restaurando arquivos .env...${NC}"
if [ -f "$EXTRACTED_ROOT/backend.env" ]; then
    cp "$EXTRACTED_ROOT/backend.env" backend/.env
    echo -e "${GREEN}[OK] backend/.env restaurado.${NC}"
fi
if [ -f "$EXTRACTED_ROOT/frontend.env.local" ]; then
    cp "$EXTRACTED_ROOT/frontend.env.local" frontend/.env.local
    echo -e "${GREEN}[OK] frontend/.env.local restaurado.${NC}"
fi

# 5. Restaurar Mídia
echo -e "${YELLOW}[4/6] Restaurando arquivos de mídia...${NC}"
if [ -d "$EXTRACTED_ROOT/media" ]; then
    rm -rf backend/media
    mkdir -p backend/media
    cp -r "$EXTRACTED_ROOT/media/"* backend/media/
    echo -e "${GREEN}[OK] Mídia restaurada.${NC}"
fi

# 6. Restaurar Banco de Dados
echo -e "${YELLOW}[5/6] Restaurando Banco de Dados PostgreSQL...${NC}"

# Verificar se o arquivo SQL existe
if [ ! -f "$EXTRACTED_ROOT/database.sql" ]; then
    echo -e "${RED}[ERRO] Arquivo database.sql não encontrado no backup.${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Parar serviços que acessam o banco para evitar locks
# (Se estiver usando docker compose para app, descomente abaixo)
# docker compose stop backend worker

echo "   -> Derrubando conexões ativas e recriando o banco..."
# Este comando força a desconexão de outros clientes e recria o banco limpo
docker compose exec -T db psql -U "$DB_USER" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" > /dev/null 2>&1
docker compose exec -T db dropdb -U "$DB_USER" --if-exists "$DB_NAME"
docker compose exec -T db createdb -U "$DB_USER" "$DB_NAME"

echo "   -> Importando dados (isso pode levar um tempo)..."
cat "$EXTRACTED_ROOT/database.sql" | docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" > /dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[OK] Banco de dados restaurado com sucesso.${NC}"
else
    echo -e "${RED}[ERRO] Falha na importação do SQL via psql.${NC}"
    # Não abortamos aqui para permitir limpeza, mas é crítico.
fi

# 7. Limpeza
echo -e "${YELLOW}[6/6] Limpando arquivos temporários...${NC}"
rm -rf "$TEMP_DIR"

# Reiniciar serviços se foram parados
# docker compose start backend worker

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN} RESTAURAÇÃO CONCLUÍDA! ${NC}"
echo -e "${GREEN} Verifique se a aplicação está acessível e os dados corretos.${NC}"
echo -e "${GREEN}======================================================${NC}"