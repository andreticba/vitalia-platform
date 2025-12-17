# Vitalia Platform

## 1. Missão do Projeto

Construir um ecossistema de saúde e bem-estar **B2B2C** de alto risco, focado na mudança comportamental sustentável. A Vitalia opera sob uma arquitetura de **Data Vault** (Cofre de Dados), onde a soberania dos dados pertence ao participante, e a inteligência artificial atua sob estrita supervisão humana (**HITL** - Human-in-the-Loop).

### Pilares de Design e Governança:

-   **Data Vault & Soberania:** Os dados sensíveis (prontuários, exames) pertencem ao usuário (`Participant`), não à organização. O acesso é concedido temporariamente a profissionais via `DataAccessGrant`.
-   **High-Risk AI (IA de Alto Risco):** A geração de planos de bem-estar utiliza cadeias de raciocínio auditáveis (*Chain of Thought*) e exige aprovação explícita de um profissional de saúde antes de chegar ao usuário.
-   **RBAC Dinâmico e B2B:** Sistema de permissões granular armazenado em banco de dados, permitindo a criação de papéis personalizados para clínicas e hospitais.
-   **Segurança em Camadas:**
    -   **Criptografia em Repouso:** Dados PII (CPF, Telefone, Nome) criptografados no banco (`django-crypto-fields`).
    -   **Blind Indexing:** Capacidade de buscar dados criptografados sem descriptografar a base inteira.
    -   **Auditoria Imutável:** `AuditLog` registra acessos, decisões da IA e revisões humanas.
-   **Engajamento Afetivo:** Hub de Receitas Familiares com análise de segurança alimentar (Alérgenos - RDC 26/2015) via IA.
-   **Gamificação Econômica:** Pontos de engajamento (*Vitalia Coins*) conversíveis em benefícios reais no Marketplace.

---

## 2. Pilha Tecnológica

### Backend (API & Inteligência)
-   **Core:** Python 3.11+, Django 5, Django Rest Framework (DRF).
-   **Async & Real-time:** Daphne (ASGI), Django Channels, Celery 5.4, Redis.
-   **Banco de Dados:** PostgreSQL 16 com extensão `pgvector` (RAG e Busca Semântica).
-   **Segurança:** `django-crypto-fields`, `djangorestframework-simplejwt`.
-   **IA Local:** Ollama (Llama 3), httpx.

### Frontend (Experiência do Usuário)
-   **Framework:** Next.js 14+ (App Router).
-   **Linguagem:** TypeScript.
-   **Estado:** Redux Toolkit (Global/Auth) + TanStack Query (Server State).
-   **UI:** Tailwind CSS v4, shadcn/ui, Lucide Icons.

### Infraestrutura & DevOps
-   **Containerização:** Docker e Docker Compose.
-   **Automação:** Scripts Bash (`.sh`) para Boot, Backup, Restore e Snapshot.

---

## 3. Constituição do Arquiteto (Princípios de Desenvolvimento)

Estas são as **21 diretrizes invioláveis** que governam todo o desenvolvimento, garantindo que a Vitalia seja segura, escalável e auditável.

### I. Metodologia e Governança
-   **(P1) Decomposição Atômica:** Transformar épicos em tarefas granulares, sequenciais e testáveis. Nunca commitar código que quebre o build.
-   **(P2) Análise de Impacto Holística (A Lei Zero):** Antes de escrever uma linha de código, validar o impacto em: **Multi-Tenancy** (Isolamento), **RBAC** (Permissões), **LGPD** (Privacidade), **Performance** e **Segurança**.
-   **(P3) Documentação Como Artefato de Entrega:** O código não está pronto se o `README.md` e o `.env.example` não refletirem as mudanças. A documentação é viva e contínua.
-   **(P4) Entrega de Código Completo:** Ao modificar arquivos, entregar o conteúdo completo para substituição, garantindo integridade e evitando erros de "colagem".
-   **(P5) Automação como Guardiã:** Utilizar scripts (`.sh`) para tarefas repetitivas (backup, restore, setup). Se o processo é manual, ele é falho.

### II. Segurança e Dados (Data Vault)
-   **(P6) Gerenciamento Estrito de Segredos:** Segredos nunca entram no Git. `.env` é exclusivo para desenvolvimento local; Produção usa injeção de variáveis seguras.
-   **(P7) Soberania do Dado (Data Vault):** O dado de saúde pertence ao **Participante**, não à Organização. O acesso é concedido temporariamente via `DataAccessGrant`. Nenhuma query deve ignorar essa verificação.
-   **(P8) Migrações Defensivas:** Alterações no banco de dados devem ser não-destrutivas e idempotentes. Dados sensíveis exigem migrações de dados separadas das de schema.

### III. Inteligência Artificial e Ética
-   **(P9) Friction for Safety (Atrito de Segurança):** Em fluxos de **Alto Risco** (ex: aprovação de plano de saúde), a UX deve impedir a "aprovação cega". Exigir ação explícita do profissional (HITL - Human-in-the-Loop).
-   **(P10) Rastreabilidade de Evidência:** Toda decisão sugerida pela IA deve ter seu "raciocínio" (Chain of Thought) registrado no `AuditLog` para explicabilidade jurídica e clínica.

### IV. Arquitetura de Software
-   **(P11) Desacoplamento Limpo:**
    -   *Services:* Lógica de Negócio Pura.
    -   *Clients:* Comunicação Externa (Ollama, APIs).
    -   *Views/Tasks:* Orquestração.
-   **(P12) API-First:** O contrato (DRF Serializers) é a fonte da verdade. O Frontend e o Backend se alinham através dele antes da implementação.
-   **(P13) Serializers Dedicados:** Separar explicitamente `ReadSerializer` (com dados aninhados para exibição) de `WriteSerializer` (com validação estrita para entrada).

### V. Qualidade e Testes
-   **(P14) Testes como Contrato da Realidade:** Nenhuma funcionalidade crítica (especialmente as médicas e de segurança) é considerada pronta sem testes de unidade e integração (Pytest + FactoryBoy).
-   **(P15) Dependências Estritas:** Versionamento de bibliotecas travado (`requirements.txt`, `package.json`) para garantir builds reprodutíveis e auditáveis.
-   **(P16) Validação Externa Ativa:** Não confiar cegamente em documentação de terceiros; validar o comportamento real das APIs e bibliotecas antes da implementação.

### VI. Performance e Frontend
-   **(P17) Otimização Proativa (Anti-N+1):** O uso de `select_related` e `prefetch_related` é obrigatório em queries relacionais. Processamento pesado vai para filas dedicadas (`ai_reasoning`).
-   **(P18) Ambiente Local-First:** O ambiente de desenvolvimento (Docker) deve ser um espelho fiel da produção para evitar o "funciona na minha máquina".
-   **(P19) Autonomia de Ferramentas:** Preferir soluções conteinerizadas e agnósticas a serviços proprietários de nuvem ("Vendor Lock-in").
-   **(P20) Gestão de Estado Estratégica:**
    -   *Server State:* TanStack Query (Cache e Sincronização).
    -   *Client State:* Redux Toolkit (Sessão, UI Global).
-   **(P21) Lançamentos Graduais:** Funcionalidades complexas devem ser desenvolvidas atrás de *Feature Flags* para permitir deploy contínuo sem quebrar a produção.

---

## 4. Guia de Instalação e Execução

### 4.1. Pré-requisitos
-   Docker e Docker Compose.
-   Python 3.11+ (para ferramentas locais).
-   Node.js 20+ (para desenvolvimento frontend local).

### 4.2. Setup Inicial

1.  **Clone o repositório e configure as variáveis:**
    ```bash
    git clone <url-repo> vitalia-platform
    cd vitalia-platform
    
    # Configure o ambiente do Backend
    cp backend/.env.example backend/.env
    # EDITE backend/.env com suas configurações locais
    
    # Configure o ambiente do Frontend
    cp frontend/.env.local.example frontend/.env.local
    ```

2.  **Suba a Infraestrutura (Banco, Redis, Ollama):**
    ```bash
    docker compose up -d
    
    # Baixa o modelo de linguagem principal definido no .env e o modelo de visão computacional
    docker compose exec ollama ollama pull $(grep OLLAMA_GENERATION_MODEL .env | cut -d '=' -f2)
    docker compose exec ollama ollama pull llava
    ```

3.  **Inicialize o Backend (Migrações e Chaves):**
    ```bash
    # O script cuida de venv, chaves de criptografia e migrações
    cd backend
    chmod +x run_server.sh
    ./run_server.sh
    ```

4.  **Popule o Banco de Dados (Seeds Obrigatórios):**
    Em outro terminal, execute os comandos de carga inicial:
    ```bash
    cd backend
    source .venv/bin/activate
    
    # 1. Criar Papéis e Permissões (RBAC)
    python manage.py seed_roles
    
    # 2. Carregar Alérgenos Oficiais (RDC 26/2015)
    python manage.py seed_allergens
    
    # 3. Carregar Knowledge Hub (Músculos e Exercícios)
    # Certifique-se de que o arquivo medical/fixtures/source_muscles.py está populado
    python manage.py load_muscles
    ```

5.  **Inicie o Frontend:**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

Acesse:
-   **Frontend:** `http://localhost:3000`
-   **API:** `http://localhost:8000/api/v1/`
-   **Admin:** `http://localhost:8000/admin/`

---

## 5. Governança Operacional (Scripts de Automação)

A plataforma possui 4 scripts críticos na raiz do projeto para garantir a continuidade do negócio e a portabilidade do código.

### 5.1. Preparação

Antes de utilizar qualquer script, você deve conceder permissão de execução a eles no ambiente Linux/Unix:

```bash
# Na raiz do projeto vitalia-platform
chmod +x *.sh backend/run_server.sh
```

### 5.2. Scripts de Dados (Backup & Restore)

Estes scripts lidam com o **ESTADO** do sistema: Banco de Dados, Arquivos de Mídia e, crucialmente, as Chaves de Criptografia.

#### **`backup.sh` (Backup Completo)**
Gera um arquivo `.tar.gz` contendo tudo que é necessário para recuperar a plataforma em caso de desastre total.
-   **O que salva:** Dump do PostgreSQL, pasta `backend/media`, pasta `encryption_keys` e arquivos `.env`.
-   **Como usar:**
    ```bash
    ./backup.sh
    ```
-   **Saída:** Cria um arquivo em `backups/vitalia_backup_TIMESTAMP.tar.gz`.

#### **`restore.sh` (Restauração de Desastre)**
Recupera o sistema a partir de um backup gerado pelo `backup.sh`.
-   **Atenção:** Esta é uma operação destrutiva. Ela apaga o banco de dados atual e sobrescreve as chaves de criptografia.
-   **Como usar:**
    ```bash
    ./restore.sh ./backups/vitalia_backup_2025-10-25_14-00.tar.gz
    ```

### 5.3. Scripts de Código (Snapshot & Setup)

Estes scripts lidam com a **LÓGICA** do sistema: Código-fonte limpo e configuração de ambiente de desenvolvimento.

#### **`app_snapshot.sh` (Backup de Código Limpo)**
Cria um pacote portátil do código-fonte, ideal para auditorias ou transferência de servidor.
-   **O que faz:** Compacta todo o projeto ignorando "lixo" como `node_modules`, `.venv`, `__pycache__`, `git` e arquivos de build.
-   **Como usar:**
    ```bash
    ./app_snapshot.sh
    ```
-   **Saída:** Cria um arquivo em `backups/source_code/vitalia_source_v1_TIMESTAMP.tar.gz`.

#### **`app_restore.sh` (Setup Automático de Ambiente)**
Pega um snapshot de código limpo e reconstrói todo o ambiente de desenvolvimento "fábrica de software".
-   **O que faz:** Descompacta o código, cria o `virtualenv` do Python, instala dependências `pip`, e instala dependências `npm` do frontend.
-   **Como usar:**
    ```bash
    ./app_restore.sh ./backups/source_code/vitalia_source_v1_TIMESTAMP.tar.gz
    ```

---

## 6. Arquitetura de Dados Resumida

-   **`core`**: Identidade (`UserProfile`), Organizações (`Organization`) e o Cofre de Dados (`DataAccessGrant`, `ConsentLog`).
-   **`medical`**:
    -   **Knowledge Hub (Global):** `Muscle`, `Exercise` (Dados científicos imutáveis).
    -   **Prontuário (Privado):** `MedicalExam`, `PhysicalEvaluation` (Pertencem ao Participante).
    -   **Jornada:** `WellnessPlan` (Planos gerados por IA e aprovados por Humanos).
-   **`social`**: `FamilyRecipe` (Receitas afetivas com validação de segurança alimentar).
-   **`gamification`**: (Em breve) Leaderboards e Carteira de Pontos ($VIT).

---

## 7. Desenvolvimento e Testes

Para rodar a suíte de testes (com Pytest e FactoryBoy):

```bash
cd backend
pytest
```

---

**Vitalia Platform** - *Tecnologia a serviço da vida.*
