#!/bin/bash
# vitalia-platform/reset_anatomy.sh em 2025-12-14 11:48
# -----------------------------------------------------------------------------
# Objetivo: Sanitização e Carga Controlada do Knowledge Hub (Anatomia).
# Executa a sequência exata para garantir integridade referencial.
# -----------------------------------------------------------------------------

# Para a execução se qualquer comando falhar
set -e

# --- Definição de Cores para UX ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- Cabeçalho ---
echo -e "${CYAN}========================================================${NC}"
echo -e "${CYAN}   VITALIA PLATFORM - RECARGA DE ANATOMIA (SANITIZED)   ${NC}"
echo -e "${CYAN}========================================================${NC}"
echo ""

# --- Navegação para o Backend ---
if [ -d "backend" ]; then
    echo -e "${BLUE}📂 Entrando no diretório backend...${NC}"
    cd backend
fi

# Verifica se o manage.py existe
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Erro: manage.py não encontrado. Execute na raiz do projeto ou dentro de /backend.${NC}"
    exit 1
fi

# --- Função Auxiliar de Execução ---
run_step() {
    CMD=$1
    DESC=$2
    echo -e "${YELLOW}▶️  Executando: $DESC...${NC}"
    python manage.py $CMD
    echo -e "${GREEN}✔ Sucesso.${NC}\n"
}

# ==============================================================================
# INÍCIO DO PIPELINE
# ==============================================================================

# 1. Limpeza
run_step "reset_anatomy" "Sanitização Completa (Apagando dados anatômicos)"

# 2. Dados Brutos
run_step "import_wellness_legacy" "Importação de Músculos e Exercícios do Legado"

# 3. Estrutura Óssea
run_step "seed_bones_authoritative" "Carga Autoritativa de Ossos (206 Ossos / Granular)"

# 4. Articulações e Landmarks Base
run_step "enrich_joints" "Criação de Articulações"
run_step "enrich_landmarks" "Criação de Acidentes Ósseos (Base)"

# 5. O Passo de Cura (Vital para a Granularidade)
run_step "repair_granular_landmarks" "Propagação de Landmarks para L1-L5 e Costelas"

# 6. Conexões do Esqueleto
run_step "enrich_relationships" "Conexão Osteoarticular (Grafo)"

# 7. Física e Estruturas
run_step "enrich_movements" "Definição de Biomecânica (Movimentos/ROM)"
run_step "enrich_structures" "Criação de Estruturas de Suporte (Ligamentos/Discos)"

# 8. Conexão Muscular (O Passo Complexo)
run_step "seed_muscle_attachments_full" "Mapeamento de Origens e Inserções Musculares"

# 9. Ações Musculares (Verificação de Existência)
echo -e "${YELLOW}▶️  Verificando script de Ações Musculares (IA)...${NC}"
if [ -f "medical/management/commands/seed_muscle_actions.py" ]; then
    run_step "seed_muscle_actions" "Populando Ações Musculares (Gerado por IA)"
else
    echo -e "${BLUE}ℹ️  Script 'seed_muscle_actions.py' não encontrado (Opcional)."
    echo -e "   Use o Google Colab ou rode 'python manage.py populate_muscle_actions_ai' depois para gerar.${NC}\n"
fi

# 10. Segurança Alimentar (Bônus)
run_step "seed_allergens" "Atualizando Tabela de Alérgenos (RDC 26/2015)"

# --- FIM ---
echo -e "${CYAN}========================================================${NC}"
echo -e "${GREEN}✅  RECARGA ANATÔMICA CONCLUÍDA COM SUCESSO!${NC}"
echo -e "${CYAN}========================================================${NC}"