---

### **Instruções para Limpeza do Ambiente**

**Atenção:** Os comandos a seguir são destrutivos e irão apagar seu banco de dados local. Prossiga apenas se não houver dados locais que precisem ser preservados.

Execute os seguintes comandos no terminal, na raiz do projeto (`vitalia-platform`):

1.  **Apague o container e o volume do banco de dados:**
    ```bash
    docker compose down -v --remove-orphans
	```

2. **Remova caches locais**
    ```bash
	find . -type d -name "__pycache__" -exec rm -r {} +
	cd backend
	find . -type d -name "__pycache__" -exec rm -r {} +
	cd ..
    ```

3.  **Apague o ambiente virtual e as pastas de migrações antiga:**
    ```bash
    rm -rf .venv
    rm -rf backend/core/migrations
    rm -rf backend/gamification/migrations
    rm -rf backend/medical/migrations
    rm -rf backend/social/migrations
    ```

4.  **Recrie o ambiente virtual e a estrutura de migrações:**
    ```bash
	python3 -m venv .venv --prompt=Vitalia
	mkdir backend/core/migrations
	mkdir backend/gamification/migrations
	mkdir backend/medical/migrations
	mkdir backend/social/migrations
	touch backend/core/migrations/__init__.py
	touch backend/gamification/migrations/__init__.py
	touch backend/medical/migrations/__init__.py
	touch backend/social/migrations/__init__.py
    ```


5.  **Recrie o ambiente virtual e o banco de dados do zero():**
    ```bash
    # Inicie os serviços novamente
    docker compose up -d
	
	# Exporta as variáveis de ambiente do .env para a sessão atual
	set -o allexport
	source backend/.env
	set +o allexport

    # Inicia o ambiente virtual e instala as bibliotecas
	source .venv/bin/activate
	pip install -r backend/requirements.txt

    # Habilite a extensão pgvector (necessário para o novo DB)
	cd backend
    docker compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "CREATE EXTENSION IF NOT EXISTS vector;"

    # Baixa o modelo de linguagem principal definido no .env e o modelo de visão computacional
    docker compose exec ollama ollama pull $(grep OLLAMA_GENERATION_MODEL .env | cut -d '=' -f2)
    docker compose exec ollama ollama pull llava

	# Recria e executa as migrações
	python manage.py makemigrations
	python manage.py migrate
	
	# Executar o Seed de Roles
	python manage.py seed_roles
	
	# Popular Alérgenos
	python manage.py seed_allergens
	
	# Recria o Superuser do Django
	python manage.py createsuperuser
	cd ..
    ```

Seu ambiente de backend agora está limpo.

No frontend, a limpeza principal é a remoção de dependências ou arquivos de cache desnecessários que não são rastreados pelo Git.

---

### **Instrução de Limpeza Final do Frontend**

Execute os seguintes comandos **dentro do diretório `ai-control/ai-frontend`** para garantir que apenas o código rastreado e o arquivo de lock de dependência limpo sejam enviados:

1.  **Parar Todos os Processos e Limpar Cache:** (Já instruído, mas reforçando)
    *   Garanta que o servidor Next.js (`npm run dev`) esteja parado.
    *   ```bash
        npm cache clean --force
        ```

2.  **Limpar Artefatos de Build/Cache:**
    *   Este comando remove as pastas de cache do Next.js e de logs temporários.
    ```bash
    rm -rf .next out node_modules package-lock.json
    ```


    *   Isso recria o `package-lock.json` e a pasta `node_modules` de forma limpa.
    ```bash
	npm install
	npx shadcn init
	npx shadcn@latest add button card form input label
    ```
---
