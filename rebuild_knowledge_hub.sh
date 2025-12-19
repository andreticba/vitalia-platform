#!/bin/bash
# vitalia-platform/rebuild_knowledge_hub.sh em 2025-12-14 11:48
# -----------------------------------------------------------------------------
# ORQUESTRADOR MESTRE: Reconstrução do Knowledge Hub
# Executa a sequência de scripts Python para transformar o banco vazio
# em uma inteligência médica granular completa.
# -----------------------------------------------------------------------------

set -e # Para se houver erro

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================================${NC}"
echo -e "${BLUE}   VITALIA - RECONSTRUÇÃO DO KNOWLEDGE HUB              ${NC}"
echo -e "${BLUE}========================================================${NC}"

# Garante que estamos na pasta certa
if [ -d "backend" ]; then cd backend; fi

# Função de execução
run_cmd() {
    echo -e "${YELLOW}▶️  Etapa: $2...${NC}"
    python manage.py $1
    echo -e "${GREEN}✔ Concluído.${NC}\n"
}

# 1. LIMPEZA
run_cmd "reset_anatomy" "Sanitização Completa (Wipe)"

# 2. DADOS BRUTOS & ESQUELETO
run_cmd "import_wellness_legacy" "Importação de Legado (Músculos/Exercícios)"
run_cmd "seed_bones_authoritative" "Criação dos 206 Ossos (Authoritative)"

# 3. CONSTRUÇÃO DO GRAFO
run_cmd "enrich_joints" "Criação de Articulações"
run_cmd "enrich_landmarks" "Criação de Landmarks Genéricos"
run_cmd "repair_granular_landmarks" "Propagação Granular de Landmarks (L1-L5, Costelas)"
run_cmd "enrich_relationships" "Conexão Osteoarticular (Grafo)"

# 4. BIOMECÂNICA
run_cmd "enrich_movements" "Definição de Movimentos e ADM"
run_cmd "enrich_structures" "Criação de Ligamentos e Meniscos"
run_cmd "seed_muscle_attachments_full" "Mapeamento de Origens e Inserções Musculares"

# 5. INTELIGÊNCIA CLÍNICA & SEGURANÇA
run_cmd "update_bone_metadata_granular" "Aplicação de Notas Clínicas (OCR)"
run_cmd "seed_allergens" "Carga de Alérgenos (RDC 26/2015)"

# 6. SETUP DO SISTEMA
run_cmd "seed_roles" "Configuração de RBAC e Permissões"
run_cmd "seed_system_init" "Inicialização de Organizações e Perfis"

echo -e "${BLUE}========================================================${NC}"
echo -e "${GREEN}✅ RECONSTRUÇÃO TOTALMENTE CONCLUÍDA!${NC}"
echo -e "${GREEN}   O Knowledge Hub está carregado, granular e enriquecido.${NC}"
echo -e "${BLUE}========================================================${NC}"