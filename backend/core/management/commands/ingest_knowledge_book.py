# backend/core/management/commands/ingest_knowledge_book.py em 2025-12-14 11:48

import os
import hashlib
import json
import httpx
import time
import sys
import re
from datetime import datetime, timedelta, timezone
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from core.models import Organization, Document, DocumentChunk
from core.clients import ollama_client

# Dependências Críticas
try:
    from markdownify import markdownify as md
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Erro: Instale as libs: pip install markdownify langchain-text-splitters pypdf")
    sys.exit(1)

User = get_user_model()

class LogColors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class Command(BaseCommand):
    help = """
    Ferramenta de Ingestão de Conhecimento V4 (Vitalia Platform).
    
    Realiza o pipeline completo de ETL (Extract, Transform, Load) para documentos PDF médicos.
    Utiliza estratégias híbridas de OCR, Visão Computacional (Llama/LLaVA) e Chunking Semântico.
    
    Exemplos:
      # Produção (Salva no Banco):
      python manage.py ingest_knowledge_book anatomia.pdf --lang pt --vision-model llava
      
      # Simulação (Não salva, gera log detalhado):
      python manage.py ingest_knowledge_book anatomia.pdf --dry-run --pages "10-20" --log-file teste.log
    """

    def add_arguments(self, parser):
        # Arquivo e Idioma
        parser.add_argument(
            'filename', 
            type=str, 
            help='Nome do arquivo PDF localizado na pasta backend/docs_to_ingest/'
        )
        parser.add_argument(
            '--lang', 
            type=str, 
            default='en', 
            choices=['pt', 'en'],
            help='Idioma predominante do documento (pt/en). Define o modelo de OCR. Padrão: en'
        )
        
        # Configuração de Chunking
        parser.add_argument(
            '--max-chars', 
            type=int, 
            default=2000, 
            help='Tamanho máximo do bloco de texto (Chunk). Padrão: 2000 caracteres.'
        )
        parser.add_argument(
            '--overlap', 
            type=int, 
            default=300, 
            help='Sobreposição entre chunks para manter contexto. Padrão: 300 caracteres.'
        )
        
        # Estratégia de Processamento
        parser.add_argument(
            '--vision-model', 
            type=str, 
            default='llava', 
            help='Nome do modelo de visão no Ollama (ex: llava, llama3.2-vision). Padrão: llava'
        )
        parser.add_argument(
            '--text-only', 
            action='store_true', 
            help='Modo rápido: Ignora processamento visual de imagens e converte tabelas apenas para texto simples.'
        )
        parser.add_argument(
            '--skip-vision', 
            action='store_true', 
            help='Ignora apenas o processamento de imagens, mas mantém formatação de tabelas.'
        )
        
        # Controle de Execução e Debug
        parser.add_argument(
            '--timeout', 
            type=int, 
            default=1800, 
            help='Tempo limite (segundos) para a API Unstructured. Aumente para livros grandes. Padrão: 1800 (30min).'
        )
        parser.add_argument(
            '--gmt', 
            type=int, 
            default=-4, 
            help='Ajuste de fuso horário para os logs (Ex: -4 para GMT-4/Cuiabá). Padrão: -4.'
        )
        parser.add_argument(
            '--pages', 
            type=str, 
            help='Intervalo de páginas para processar (Ex: "1-10", "50,55,60"). Útil para testes rápidos.'
        )
        parser.add_argument(
            '--force', 
            action='store_true', 
            help='Força a re-ingestão mesmo se o documento já estiver marcado como CONCLUÍDO.'
        )
        parser.add_argument(
            '--dry-run', 
            action='store_true', 
            help='Modo Simulação: Executa extração, visão e chunking, grava no log, mas NÃO salva no banco nem gera embeddings.'
        )
        parser.add_argument(
            '--log-file', 
            type=str, 
            help='Caminho para salvar o log verboso em arquivo (ex: ingest.log).'
        )

    def log(self, message, level='INFO', to_file_only=False):
        """Logger customizado."""
        tz = timezone(timedelta(hours=self.gmt))
        now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        
        # 1. Output no Console (se não for exclusivo para arquivo)
        if not to_file_only:
            color_map = {
                'INFO': LogColors.BLUE, 'SUCCESS': LogColors.GREEN,
                'WARNING': LogColors.YELLOW, 'ERROR': LogColors.RED,
                'VISION': LogColors.CYAN, 'TABLE': LogColors.HEADER,
                'DRY-RUN': LogColors.HEADER
            }
            color = color_map.get(level, LogColors.RESET)
            console_msg = f"{LogColors.BOLD}[{now}]{LogColors.RESET} {color}[{level}]{LogColors.RESET} {message}"
            self.stdout.write(console_msg)

        # 2. Gravação em Arquivo (Verboso)
        if self.log_handle:
            clean_msg = f"[{now}] [{level}] {message}\n"
            self.log_handle.write(clean_msg)
            self.log_handle.flush()

    def handle(self, *args, **options):
        self.gmt = options['gmt']
        self.log_handle = None
        
        if options['log_file']:
            self.log_handle = open(options['log_file'], 'a', encoding='utf-8')
            self.log(f"Iniciando log em: {options['log_file']}", 'INFO')

        try:
            self._run_ingestion(options)
        except KeyboardInterrupt:
            self.log("Operação cancelada pelo usuário.", 'WARNING')
        except Exception as e:
            self.log(f"Erro Fatal não tratado: {e}", 'ERROR', exc_info=True)
        finally:
            if self.log_handle:
                self.log_handle.close()

    def _run_ingestion(self, options):
        filename = options['filename']
        file_path = os.path.join(settings.BASE_DIR, 'docs_to_ingest', filename)
        
        if not os.path.exists(file_path):
            self.log(f"Arquivo não encontrado: {file_path}", 'ERROR')
            return

        # 1. Slice de Páginas
        if options['pages']:
            self.log(f"Recortando páginas {options['pages']}...", 'INFO')
            file_path = self._slice_pdf(file_path, options['pages'])

        # 2. Registro no Banco (Apenas se não for Dry Run)
        doc = None
        if not options['dry_run']:
            doc = self._get_or_create_document(filename, file_path, options)
            if not doc: return # Já existe e não é force
        else:
            self.log("MODO DRY-RUN ATIVADO: Nenhuma alteração será feita no banco de dados.", 'DRY-RUN')

        # 3. FASE 1: Extração Atômica
        self.log(">>> FASE 1: Extração Estrutural (OCR/Layout) <<<", 'INFO')
        elements = self._extract_atomic_elements(file_path, options)
        
        if not elements:
            self.log("Nenhum elemento extraído. Abortando.", 'ERROR')
            return

        # 4. FASE 2: Enriquecimento (Visão e Tabelas)
        skip_vision = options['skip_vision'] or options['text_only']
        if not skip_vision:
            self.log(">>> FASE 2: Vision RAG (Análise de Imagens) <<<", 'VISION')
            elements = self._process_images_sequentially(elements, options['vision_model'])
        else:
            self.log("Pulando Fase Vision (Flag ativa).", 'WARNING')

        # 5. FASE 3: Processamento e Chunking Local
        self.log(">>> FASE 3: Refinamento e Chunking Local <<<", 'TABLE')
        final_chunks = self._enrich_and_chunk(elements, options)
        self.log(f"Total de Chunks Finais: {len(final_chunks)}", 'SUCCESS')

        # 6. FASE 4: Ação (Dry Run vs Produção)
        if options['dry_run']:
            self._execute_dry_run(final_chunks)
        else:
            self.log(">>> FASE 4: Vetorização e Persistência <<<", 'INFO')
            self._embed_and_save(doc, final_chunks)

        # Limpeza
        if options['pages'] and 'temp_slice' in file_path:
            os.remove(file_path)

    def _extract_atomic_elements(self, file_path, options):
        unstructured_url = settings.UNSTRUCTURED_API_URL or "http://localhost:8002/general/v0/general"
        ocr_lang = 'por' if options['lang'] == 'pt' else 'eng'
        
        # Configuração dinâmica baseada nas flags
        extract_types = ["Image", "Table"]
        if options['text_only']:
            # Se for texto puro, não gastamos tempo extraindo blocos de imagem/tabela
            extract_types = []
        elif options['skip_vision']:
            # Se pular visão, ainda queremos tabelas, mas não imagens
            extract_types = ["Table"]

        payload = {
            "strategy": "hi_res",
            "chunking_strategy": "by_title",
            "max_characters": options['max_chars'],
            "combine_under_n_chars": 500,
            "new_after_n_chars": int(options['max_chars'] * 1.2),
            "languages": [ocr_lang],
            "extract_image_block_types": extract_types,
            "extract_image_block_to_payload": True if extract_types else False,
            "coordinates": False,
        }

        self.log(f"Enviando para API (Lang: {ocr_lang} | TextOnly: {options['text_only']})...", 'INFO')
        try:
            with open(file_path, "rb") as f:
                files = {"files": (os.path.basename(file_path), f)}
                with httpx.Client(timeout=float(options['timeout'])) as client:
                    response = client.post(unstructured_url, files=files, data=payload)
                    response.raise_for_status()
                    return response.json()
        except Exception as e:
            self.log(f"Erro na extração: {e}", 'ERROR')
            return []

    def _process_images_sequentially(self, elements, model_name):
        image_elements = [el for el in elements if el.get('metadata', {}).get('image_base64')]
        total_imgs = len(image_elements)
        
        if total_imgs == 0:
            self.log("Nenhuma imagem extraída.", 'WARNING')
            return elements

        self.log(f"Iniciando inferência visual em {total_imgs} imagens...", 'VISION')
        start_global = time.time()

        for i, el in enumerate(image_elements):
            start_item = time.time()
            base64_img = el['metadata']['image_base64']
            el_type = el.get('type')
            page = el.get('metadata', {}).get('page_number', '?')
            
            prompt = (
                "Analise esta imagem médica técnica. Descreva detalhadamente as estruturas anatômicas, "
                "rótulos visíveis e relações espaciais. Seja técnico e preciso."
            )
            if el_type == "Table":
                prompt = (
                    "Transcreva esta tabela integralmente em formato Markdown. "
                    "Mantenha todas as linhas e colunas. NÃO resuma. "
                    "Se houver códigos (ex: CID, valores), copie exatamente."
                )

            try:
                response = ollama_client.generate(
                    model=model_name,
                    prompt=prompt,
                    images=[base64_img],
                    options={"temperature": 0.1}
                )
                
                description = response.get('response', '').strip()
                duration = time.time() - start_item
                
                if description:
                    el['text'] = f"[DESCRIÇÃO VISUAL IA]: {description}\n\n[CONTEÚDO OCR]: {el.get('text', '')}"
                    el['metadata']['vision_processed'] = True
                    
                    # Log verboso para análise de tempo (solicitado pelo usuário)
                    self.log(f"Img Pág {page} ({el_type}) processada em {duration:.2f}s", 'VISION', to_file_only=True)
                    
                    # Barra de progresso na tela
                    self._print_progress(i + 1, total_imgs, start_global, label="Visão Computacional")

            except Exception as e:
                self.log(f"Falha na imagem {i} (Pág {page}): {e}", 'ERROR')

        print("") # Quebra linha após a barra
        
        # Descarrega VRAM para liberar para o próximo modelo
        self.log("Descarregando modelo de visão...", 'INFO')
        self._unload_ollama_model(model_name)
        
        return elements

    def _enrich_and_chunk(self, elements, options):
        # 1. Enriquecimento e Consolidação
        full_text_stream = ""
        total_imgs = sum(1 for el in elements if el.get('type') == 'Image')
        img_processed = 0
        
        # Rastreia a página atual para injetar marcadores no texto narrativo
        current_processing_page = None

        for el in elements:
            el_type = el.get('type')
            text = el.get('text', '').strip()
            meta = el.get('metadata', {})
            # Garante que page seja um número ou None, nunca '?' para lógica
            page = meta.get('page_number') 
            
            # --- FILTROS DE EXCLUSÃO ---
            if el_type in ['Header', 'Footer']: continue
            if len(text) < 5 and el_type == "Uncategorized": continue

            # FLAG TEXT-ONLY ESTRICTA
            if options['text_only']:
                if el_type in ['Table', 'Image', 'FigureCaption']:
                    continue

            # --- INJEÇÃO DE MARCADOR DE PÁGINA ---
            # Se for um elemento PageBreak OU se o metadado de página mudou
            is_new_page = (el_type == "PageBreak") or (page is not None and page != current_processing_page)
            
            if is_new_page and page is not None:
                full_text_stream += f"\n\n=== PÁG {page} ===\n\n"
                current_processing_page = page
                if el_type == "PageBreak": continue # Não adiciona texto do pagebreak

            # --- TRATAMENTO DE IMAGEM ---
            if el_type == "Image" and not options['skip_vision']:
                base64_img = meta.get('image_base64')
                if base64_img:
                    prompt = "Analise esta imagem médica técnica..." # (Prompt abreviado para legibilidade)
                    desc = self._vision_inference(options['vision_model'], prompt, base64_img)
                    if desc:
                        full_text_stream += f"\n\n[DESCRIÇÃO VISUAL IA PÁG {page}]: {desc}\n\n"
                        img_processed += 1
                continue 

            # --- TRATAMENTO DE TABELA ---
            if el_type == "Table":
                html = meta.get('text_as_html')
                if html:
                    md_table = md(html)
                    full_text_stream += f"\n\n### TABELA PÁG {page}\n{md_table}\n\n"
                    if meta.get('vision_processed'):
                        vision_text = text.split('[DESCRIÇÃO VISUAL IA]:')[1].split('[CONTEÚDO OCR]:')[0]
                        full_text_stream += f"\n> Transcrição IA: {vision_text}\n\n"
                    continue

            # --- TEXTO NARRATIVO ---
            full_text_stream += f"{text}\n\n"

        # Limpeza de memória GPU
        if not options['skip_vision'] and not options['text_only'] and total_imgs > 0:
            self._unload_model(options['vision_model'])

        # 2. Chunking Local
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=options['max_chars'],
            chunk_overlap=options['overlap'],
            # Adicionei o marcador de página como separador prioritário
            separators=["=== PÁG", "\n\n### ", "\n\n", ". ", " ", ""],
            keep_separator=True
        )
        
        raw_chunks = splitter.split_text(full_text_stream)
        
        final_chunks = []
        # Memória do número da página para chunks que são continuação
        last_seen_page = None 

        for content in raw_chunks:
            # Tenta encontrar o marcador explícito
            # Regex busca 'PÁG 123' em qualquer formato (=== PÁG 123 === ou [DESCRIÇÃO... PÁG 123])
            page_match = re.search(r'PÁG (\d+)', content)
            
            if page_match:
                current_page_num = int(page_match.group(1))
                last_seen_page = current_page_num
            else:
                # Se não tem marcador, usa a última página vista (continuação do texto)
                current_page_num = last_seen_page
            
            meta = {
                "source": options['filename'],
                "generated_by": "Vitalia V4 Ingest",
                "is_table": "### TABELA" in content,
                "has_vision": "[DESCRIÇÃO VISUAL IA" in content,
                "ingestion_date": datetime.now().isoformat()
            }
            final_chunks.append({"content": content, "page": current_page_num, "metadata": meta})
            
        return final_chunks

    def _execute_dry_run(self, chunks):
        self.log("--- INÍCIO RELATÓRIO DRY-RUN ---", 'DRY-RUN')
        self.log(f"Total Chunks: {len(chunks)}", 'DRY-RUN')
        
        # Loga os chunks no arquivo
        if self.log_handle:
            for i, c in enumerate(chunks):
                self.log_handle.write(f"\n--- Chunk {i+1} (Pág {c['page']}) ---\n")
                self.log_handle.write(f"Flags: {c['metadata']}\n")
                self.log_handle.write(f"Conteúdo:\n{c['content']}\n")
                self.log_handle.write("-" * 40 + "\n")
        
        self.log("Conteúdo detalhado gravado no arquivo de log.", 'DRY-RUN')
        self.log("--- FIM DRY-RUN (Sem alterações no DB) ---", 'DRY-RUN')

    def _embed_and_save(self, doc, chunks):
        total = len(chunks)
        start_time = time.time()
        
        # Limpeza prévia
        doc.chunks.all().delete()
        
        db_objs = []
        for i, item in enumerate(chunks):
            try:
                emb = ollama_client.embed(settings.OLLAMA_EMBEDDING_MODEL, item['content'])
                
                db_objs.append(DocumentChunk(
                    document=doc,
                    content=item['content'],
                    embedding=emb['embedding'],
                    page_number=item['page'],
                    metadata=item['metadata']
                ))
                
                # Barra de progresso visual
                self._print_progress(i + 1, total, start_time, label="Vetorização")
                
                # Log de tempo individual (apenas arquivo)
                elapsed = time.time() - start_time
                avg = elapsed / (i + 1)
                self.log(f"Chunk {i+1}/{total} vetorizado. Méd: {avg:.2f}s/item", 'INFO', to_file_only=True)

            except Exception as e:
                self.log(f"Erro vetorizando chunk {i}: {e}", 'ERROR')

        print("") # Quebra linha
        
        if db_objs:
            # Batch Create seguro (500 por vez)
            batch_size = 500
            for i in range(0, len(db_objs), batch_size):
                DocumentChunk.objects.bulk_create(db_objs[i:i+batch_size])
            
            doc.status = Document.DocumentStatus.COMPLETED
            doc.save()
            self.log("Ingestão e Vetorização finalizadas.", 'SUCCESS')
            self._unload_ollama_model(settings.OLLAMA_EMBEDDING_MODEL)
        else:
            doc.status = Document.DocumentStatus.FAILED
            doc.save()

    def _print_progress(self, iteration, total, start_time, length=40, label="Progresso"):
        percent = ("{0:.1f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = '█' * filled_length + '-' * (length - filled_length)
        
        elapsed_time = time.time() - start_time
        if iteration > 0:
            avg_time_per_item = elapsed_time / iteration
            remaining_items = total - iteration
            eta_seconds = int(remaining_items * avg_time_per_item)
            eta_str = str(timedelta(seconds=eta_seconds))
        else:
            eta_str = "Calculando..."

        color_bar = f"{LogColors.GREEN}{bar}{LogColors.RESET}"
        output = f'\r  > {label}: |{color_bar}| {percent}% ({iteration}/{total}) [ETA: {eta_str}]'
        
        self.stdout.write(output, ending='')
        self.stdout.flush()
        
        # Grava o progresso final no arquivo apenas quando termina
        if iteration == total and self.log_handle:
            self.log_handle.write(f"\n[{label} Concluído] Total tempo: {str(timedelta(seconds=int(elapsed_time)))}\n")

    def _unload_ollama_model(self, model):
        try:
            ollama_client.generate(model, "", keep_alive=0)
            self.log(f"Modelo {model} descarregado da VRAM.", 'INFO')
        except: pass

    def _get_or_create_document(self, filename, path, options):
        org = Organization.objects.first() 
        with open(path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        
        doc, created = Document.objects.get_or_create(
            file_hash=h,
            defaults={
                'organization': org, 
                'file_name': filename,
                'file_size_bytes': os.path.getsize(path),
                'status': Document.DocumentStatus.PROCESSING
            }
        )
        if not created and not options['force'] and doc.status == Document.DocumentStatus.COMPLETED:
            self.log("Documento já existe. Use --force.", 'WARNING')
            return None
        
        doc.status = Document.DocumentStatus.PROCESSING
        doc.save()
        return doc

    def _slice_pdf(self, input_path, pages_arg):
        reader = PdfReader(input_path)
        writer = PdfWriter()
        if '-' in pages_arg:
            s, e = map(int, pages_arg.split('-'))
            for i in range(s-1, e):
                if i < len(reader.pages): writer.add_page(reader.pages[i])
        
        out = f"{input_path}.temp_slice.pdf"
        with open(out, "wb") as f: writer.write(f)
        return out