#!/bin/bash
# vitalia-platform/reset_and_seed.sh  em 2025-12-14 11:48
# -----------------------------------------------------------------------------
# Objetivo: Resetar a inteligência da Vitalia (Versão Granular/Explosão Óssea).
# 1. Recria o banco legado a partir do arquivo SQL.
# 2. Executa o pipeline de ETL na ordem estrita de dependência.
# -----------------------------------------------------------------------------

set -e

# Configurações
CONTAINER_DB="vitalia_db"
DB_USER="vitalia_user"
LEGACY_DB="wellness_legacy"
SQL_FILE="backend/docs_to_ingest/wellness_legacy.sql"

echo "🚀 INICIANDO PROCESSO DE CARGA TOTAL DA VITALIA (GRANULAR)..."

# ---------------------------------------------------------
# FASE 1: PREPARAÇÃO DO BANCO LEGADO
# ---------------------------------------------------------
echo ""
echo "--- [1/3] Restaurando Banco Legado ($LEGACY_DB) ---"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Erro: Arquivo $SQL_FILE não encontrado."
    exit 1
fi

# Drop e Create Database (Garante estado limpo)
docker compose exec -T db psql -U $DB_USER -d vitalia_db -c "DROP DATABASE IF EXISTS $LEGACY_DB;"
docker compose exec -T db psql -U $DB_USER -d vitalia_db -c "CREATE DATABASE $LEGACY_DB;"

# Importar o SQL
cat "$SQL_FILE" | docker compose exec -T db psql -U $DB_USER -d $LEGACY_DB > /dev/null
echo "✅ Banco legado restaurado com sucesso."

# ---------------------------------------------------------
# FASE 2: PIPELINE DE ETL (PYTHON/DJANGO)
# ---------------------------------------------------------
echo ""
echo "--- [2/3] Executando Pipeline de ETL e Enriquecimento ---"

cd backend

# Verifica Venv
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [ -d "../.venv" ]; then
        source "../.venv/bin/activate"
    elif [ -d ".venv" ]; then
        source ".venv/bin/activate"
    else
        echo "⚠️ Aviso: Virtualenv não detectado. Tentando rodar com python do sistema..."
    fi
fi

# 1. Migrar do Legado (Músculos/Exercícios Brutos)
echo "▶️ [1/10] Importando dados brutos do legado..."
python manage.py import_wellness_legacy

# 2. Anatomia Granular (Criação de ~206 Ossos)
echo "▶️ [2/10] Realizando Carga do Esqueleto Humano..."
python manage.py seed_bones_authoritative

# 3. Articulações
echo "▶️ [3/10] Enriquecendo Articulações..."
python manage.py enrich_joints

# 4. Landmarks Básicos
echo "▶️ [4/10] Mapeando Acidentes Ósseos (Landmarks)..."
python manage.py enrich_landmarks

# 5. REPARO GRANULAR (Passo Crítico para a Explosão funcionar)
echo "▶️ [5/10] Propagando Landmarks para Ossos Granulares..."
python manage.py repair_granular_landmarks

# 6. Relacionamentos (Grafo)
echo "▶️ [6/10] Conectando Ossos e Articulações..."
python manage.py enrich_relationships

# 7. Cinesiologia
echo "▶️ [7/10] Definindo Biomecânica de Movimento..."
python manage.py enrich_movements

# 8. Estruturas de Suporte
echo "▶️ [8/10] Criando Estruturas (Ligamentos/Discos/Bursas)..."
python manage.py enrich_structures

# 9. Músculos (Full - V5)
echo "▶️ [9/10] Mapeando Origens e Inserções Musculares (Lógica V5)..."
python manage.py seed_muscle_attachments_full

# 10. Segurança Alimentar
echo "▶️ [10/10] Populando Alérgenos (RDC 26/2015)..."
python manage.py seed_allergens

# ---------------------------------------------------------
# FASE 3: INICIALIZAÇÃO DO SISTEMA
# ---------------------------------------------------------
echo ""
echo "--- [3/3] Inicializando Sistema B2B e Identidade ---"

# 1. Roles e Permissões
echo "▶️ Criando Roles e Permissões..."
python manage.py seed_roles

# 2. Organização e Perfis
echo "▶️ Inicializando Organização Vitalia e Perfis..."
python manage.py seed_system_init

echo ""
echo "✨ SUCESSO! A Plataforma Vitalia está totalmente carregada e sanitizada."