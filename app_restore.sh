#!/bin/bash

# vitalia-platform/app_restore.sh em 2025-12-14 11:48
# vitalia platform - app_restore.sh

# =================================================================================
# VITALIA PLATFORM - RESTAURAÇÃO DE AMBIENTE DE DESENVOLVIMENTO em 2025-12-14 11:48
# =================================================================================
# Este script:
# 1. Extrai o código-fonte de um snapshot (.tar.gz).
# 2. Reconstrói o ambiente virtual Python (.venv).
# 3. Reinstala as dependências do Backend.
# 4. Reinstala as dependências do Frontend (npm install limpo).
# =================================================================================

# Uso: ./app_restore.sh <arquivo_snapshot.tar.gz>

# Configurações
SNAPSHOT_FILE="$1"

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Validação
if [ -z "$SNAPSHOT_FILE" ]; then
    echo -e "${RED}[ERRO] Você deve especificar o arquivo de snapshot.${NC}"
    echo "Uso: ./app_restore.sh ./backups/source_code/vitalia_source_v1_....tar.gz"
    exit 1
fi

if [ ! -f "$SNAPSHOT_FILE" ]; then
    echo -e "${RED}[ERRO] Arquivo não encontrado: $SNAPSHOT_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   VITALIA - RECONSTRUÇÃO DE AMBIENTE (RESTORE)       ${NC}"
echo -e "${BLUE}======================================================${NC}"

echo -e "${RED}AVISO: Isso irá sobrescrever arquivos na pasta atual e reinstalar dependências.${NC}"
read -p "Deseja continuar? (s/n): " CONFIRM
if [ "$CONFIRM" != "s" ]; then exit 0; fi

# 2. Extração do Código
echo -e "${YELLOW}[1/4] Extraindo código-fonte...${NC}"
tar -xzf "$SNAPSHOT_FILE"
echo -e "${GREEN}[OK] Código extraído.${NC}"

# 3. Reconstrução do Backend (Python)
echo -e "${YELLOW}[2/4] Configurando Backend (Python/Django)...${NC}"

if [ -d "backend" ]; then
    cd backend
    
    if [ -d ".venv" ]; then
        echo "   -> Removendo .venv antigo..."
        rm -rf .venv
    fi

    echo "   -> Criando novo ambiente virtual..."
    python3 -m venv .venv
    
    echo "   -> Ativando e instalando dependências..."
    source .venv/bin/activate
    
    pip install --upgrade pip > /dev/null
    if pip install -r requirements.txt; then
        echo -e "${GREEN}[OK] Dependências Python instaladas.${NC}"
    else
        echo -e "${RED}[ERRO] Falha ao instalar requirements.txt${NC}"
        exit 1
    fi
    
    chmod +x run_server.sh
    cd ..
else
    echo -e "${RED}[ERRO] Pasta 'backend' não encontrada no snapshot.${NC}"
    exit 1
fi

# 4. Reconstrução do Frontend (Node)
echo -e "${YELLOW}[3/4] Configurando Frontend (Next.js)...${NC}"

if [ -d "frontend" ]; then
    cd frontend
    
    if [ -d "node_modules" ]; then
        echo "   -> Limpando node_modules antigo..."
        rm -rf node_modules
    fi
    
    # Se houver um package-lock.json antigo (que não deveria vir no backup, mas por segurança), removemos
    if [ -f "package-lock.json" ]; then
        rm package-lock.json
    fi

    echo "   -> Instalando dependências (npm install)..."
    # npm install vai ler o package.json e gerar um novo lockfile fresco
    npm install
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[OK] Dependências Frontend instaladas.${NC}"
    else
        echo -e "${RED}[ERRO] Falha no npm install.${NC}"
    fi
    
    cd ..
else
    echo -e "${YELLOW}[AVISO] Pasta 'frontend' não encontrada.${NC}"
fi

# 5. Finalização
echo -e "${YELLOW}[4/4] Ajustando permissões finais...${NC}"
chmod +x *.sh 2>/dev/null || :

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN} AMBIENTE RESTAURADO E PRONTO PARA USO! ${NC}"
echo -e "${GREEN}======================================================${NC}"
echo -e "Próximos passos:"
echo -e "1. Verifique se o arquivo .env está correto."
echo -e "2. Suba o Docker: ${BLUE}docker compose up -d${NC}"
echo -e "3. Inicie o Backend: ${BLUE}cd backend && ./run_server.sh${NC}"
echo -e "4. Inicie o Frontend: ${BLUE}cd frontend && npm run dev${NC}"