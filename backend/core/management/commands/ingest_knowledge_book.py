# backend/core/management/commands/ingest_knowledge_book.py em 2025-12-14 11:48

import os
import hashlib
import json
import httpx
import time
import sys
import re
import traceback
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
    Ferramenta de Ingestão de Conhecimento V7 (Vitalia Platform).
    
    Realiza o pipeline completo de ETL (Extract, Transform, Load) para documentos PDF médicos.
    
    Funcionalidades Principais:
    1. Extração Atômica: Preserva a paginação exata removendo a estratégia de chunking da API.
    2. Vision RAG: Analisa imagens médicas usando modelos LLaVA/Llama-Vision locais.
    3. Tratamento de Tabelas: Converte tabelas HTML complexas em Markdown estruturado.
    4. Sanitização de Texto: Corrige hifenização fantasma (ex: "múscu- los") em todo o conteúdo.
    5. Gestão de Memória: Carrega e descarrega modelos da GPU sequencialmente (ideal para VRAM limitada).
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
            help='Idioma predominante do documento (pt/en). Define o modelo de OCR e metadados. Padrão: en'
        )
        
        # Configuração de Chunking e Texto
        parser.add_argument(
            '--max-chars', 
            type=int, 
            default=2000, 
            help='Tamanho máximo do bloco de texto (Chunk). Recomendado: 2000-4000 para Llama3. Padrão: 2000.'
        )
        parser.add_argument(
            '--overlap', 
            type=int, 
            default=300, 
            help='Sobreposição entre chunks para manter contexto entre quebras. Padrão: 300 caracteres.'
        )
        parser.add_argument(
            '--fix-hyphens',
            action='store_true',
            help='ATIVAR PARA TEXTOS JUSTIFICADOS. Corrige hifenização fantasma (ex: "múscu- los" -> "músculos") em texto narrativo, tabelas e descrições de IA.'
        )
        
        # Estratégia de Processamento Visual
        parser.add_argument(
            '--vision-model', 
            type=str, 
            default='llava', 
            help='Nome do modelo de visão no Ollama (ex: llava, llama3.2-vision). Padrão: llava'
        )
        parser.add_argument(
            '--text-only', 
            action='store_true', 
            help='Modo Texto Puro: Ignora completamente imagens e tabelas na extração. Útil para livros narrativos simples.'
        )
        parser.add_argument(
            '--skip-vision', 
            action='store_true', 
            help='Ignora apenas o processamento de imagens (Vision RAG), mas mantém e processa tabelas.'
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
            help='Intervalo de páginas para processar (Ex: "1-10", "50,55,60"). Útil para testes rápidos de ingestão.'
        )
        parser.add_argument(
            '--force', 
            action='store_true', 
            help='Força a re-ingestão mesmo se o documento já estiver marcado como CONCLUÍDO no banco de dados.'
        )
        parser.add_argument(
            '--dry-run', 
            action='store_true', 
            help='Modo Simulação: Executa todo o pipeline (Extração, Visão, Chunking), grava o resultado no log, mas NÃO salva no banco nem gera embeddings.'
        )
        parser.add_argument(
            '--log-file', 
            type=str, 
            help='Caminho para salvar o log verboso em arquivo (ex: ingest_debug.log).'
        )

    def log(self, message, level='INFO', to_file_only=False):
        """Logger customizado híbrido (Console Colorido + Arquivo Texto)."""
        tz = timezone(timedelta(hours=self.gmt))
        now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        
        # Output Console
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

        # Output Arquivo
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
            tb = traceback.format_exc()
            self.log(f"Erro Fatal não tratado: {e}\n{tb}", 'ERROR')
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

        # 2. Registro no Banco
        doc = None
        if not options['dry_run']:
            doc = self._get_or_create_document(filename, file_path, options)
            if not doc: return 
        else:
            self.log("MODO DRY-RUN ATIVADO: Nenhuma alteração será feita no banco.", 'DRY-RUN')

        # 3. FASE 1: Extração Atômica
        self.log(">>> FASE 1: Extração Estrutural (OCR/Layout) <<<", 'INFO')
        elements = self._extract_atomic_elements(file_path, options)
        
        if not elements:
            self.log("Nenhum elemento extraído. Abortando.", 'ERROR')
            return

        # 4. FASE 2: Enriquecimento (Visão)
        # Se --text-only ou --skip-vision estiverem ativos, pula esta fase
        if not (options['skip_vision'] or options['text_only']):
            self.log(">>> FASE 2: Vision RAG (Análise de Imagens) <<<", 'VISION')
            elements = self._process_images_sequentially(elements, options['vision_model'])
        else:
            self.log("Pulando Fase Vision (Flag ativa).", 'WARNING')

        # 5. FASE 3: Processamento e Chunking Local
        self.log(">>> FASE 3: Refinamento e Chunking Local <<<", 'TABLE')
        final_chunks = self._enrich_and_chunk(elements, options)
        self.log(f"Total de Chunks Finais: {len(final_chunks)}", 'SUCCESS')

        # 6. FASE 4: Ação
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
            extract_types = []
        elif options['skip_vision']:
            extract_types = ["Table"]

        payload = {
            "strategy": "hi_res",
            "languages": [ocr_lang],
            
            # Tipos de blocos a extrair como imagem (base64)
            "extract_image_block_types": extract_types,
            "extract_image_block_to_payload": True if extract_types else False,
            
            # Parâmetros auxiliares
            "include_page_breaks": True, 
            "coordinates": False,
            "xml_keep_tags": False,
        }

        self.log(f"Enviando para API (Lang: {ocr_lang} | Atomic Elements)...", 'INFO')
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
        """Processa imagens uma a uma com filtro de qualidade e sanitização."""
        image_elements = [el for el in elements if el.get('metadata', {}).get('image_base64')]
        total_imgs = len(image_elements)
        
        if total_imgs == 0:
            self.log("Nenhuma imagem extraída.", 'WARNING')
            return elements

        self.log(f"Iniciando inferência visual em {total_imgs} imagens...", 'VISION')
        start_global = time.time()
        skipped_imgs = 0

        for i, el in enumerate(image_elements):
            start_item = time.time()
            base64_img = el['metadata']['image_base64']
            el_type = el.get('type')
            page = el.get('metadata', {}).get('page_number', '?')
            
            # FILTRO 1: Tamanho mínimo (~3KB)
            if len(base64_img) < 4000:
                skipped_imgs += 1
                continue

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
                
                # FILTRO 2: Sanitização de caracteres de controle
                description = response.get('response', '').strip()
                description = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', description)
                
                # FILTRO 3: Qualidade mínima (evitar alucinações de ruído)
                if len(description) < 10 or not any(c.isalpha() for c in description):
                    skipped_imgs += 1
                    continue
                
                el['text'] = f"[DESCRIÇÃO VISUAL IA]: {description}\n\n[CONTEÚDO OCR]: {el.get('text', '')}"
                el['metadata']['vision_processed'] = True
                
                self.log(f"Img Pág {page} ({el_type}) processada em {time.time() - start_item:.2f}s", 'VISION', to_file_only=True)
                self._print_progress(i + 1, total_imgs, start_global, label="Visão Computacional")

            except Exception as e:
                self.log(f"Falha na imagem {i} (Pág {page}): {e}", 'ERROR')

        print("") 
        if skipped_imgs > 0:
            self.log(f"Imagens ignoradas (pequenas ou inválidas): {skipped_imgs}", 'WARNING')
        
        self.log("Descarregando modelo de visão...", 'INFO')
        self._unload_model(model_name)
        
        return elements

    def _enrich_and_chunk(self, elements, options):
        full_text_stream = ""
        
        # Rastreia a página atual para injetar marcadores
        current_processing_page = None

        for el in elements:
            el_type = el.get('type')
            text = el.get('text', '').strip()
            meta = el.get('metadata', {})
            page = meta.get('page_number') 
            
            # --- FILTROS DE EXCLUSÃO ---
            if el_type in ['Header', 'Footer']: continue
            if len(text) < 5 and el_type == "Uncategorized": continue

            if options['text_only']:
                if el_type in ['Table', 'Image', 'FigureCaption']:
                    continue

            # --- CORREÇÃO DE HIFENIZAÇÃO (TEXTO NARRATIVO) ---
            if options['fix_hyphens'] and text:
                text = self._fix_hyphenation(text)

            # --- INJEÇÃO DE MARCADOR DE PÁGINA ---
            is_new_page = (el_type == "PageBreak") or (page is not None and page != current_processing_page)
            
            if is_new_page and page is not None:
                full_text_stream += f"\n\n=== PÁG {page} ===\n\n"
                current_processing_page = page
                if el_type == "PageBreak": continue 

            # --- TRATAMENTO DE TABELA ---
            if el_type == "Table":
                html = meta.get('text_as_html')
                if html:
                    md_table = md(html)
                    
                    # CORREÇÃO: Aplica fix-hyphens também na Tabela Markdown
                    if options['fix_hyphens']:
                        md_table = self._fix_hyphenation(md_table)
                    
                    full_text_stream += f"\n\n### TABELA PÁG {page}\n{md_table}\n\n"
                    
                    if meta.get('vision_processed') and '[DESCRIÇÃO VISUAL IA]:' in text:
                        try:
                            vision_part = text.split('[DESCRIÇÃO VISUAL IA]:')[1].split('[CONTEÚDO OCR]:')[0]
                            # CORREÇÃO: Aplica fix-hyphens na Visão
                            if options['fix_hyphens']:
                                vision_part = self._fix_hyphenation(vision_part)
                            full_text_stream += f"\n> Transcrição IA: {vision_part.strip()}\n\n"
                        except IndexError:
                            pass
                    continue

            # --- TRATAMENTO DE IMAGEM/TEXTO ---
            # Se for imagem processada, 'text' já contém a descrição visual.
            # Se a flag fix-hyphens estiver ativa, já foi aplicada no início do loop.
            full_text_stream += f"{text}\n\n"

        # Limpeza extra de memória
        if not options['skip_vision'] and not options['text_only']:
            # Chamada de segurança caso algo tenha ficado na memória
            self._unload_model(options['vision_model'])

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=options['max_chars'],
            chunk_overlap=options['overlap'],
            separators=["=== PÁG", "\n\n### ", "\n\n", ". ", " ", ""],
            keep_separator=True
        )
        
        raw_chunks = splitter.split_text(full_text_stream)
        
        final_chunks = []
        last_seen_page = None 

        for content in raw_chunks:
            page_match = re.search(r'PÁG (\d+)', content)
            
            if page_match:
                current_page_num = int(page_match.group(1))
                last_seen_page = current_page_num
            else:
                current_page_num = last_seen_page
            
            meta = {
                "source": options['filename'],
                "generated_by": "Vitalia V7 Ingest",
                "is_table": "### TABELA" in content,
                "has_vision": "[DESCRIÇÃO VISUAL IA" in content,
                "ingestion_date": datetime.now().isoformat()
            }
            final_chunks.append({"content": content, "page": current_page_num, "metadata": meta})
            
        return final_chunks

    def _fix_hyphenation(self, text):
        """
        Corrige hifenização fantasma causada por justificação de texto em PDFs.
        Ex: "múscu- los" -> "músculos"
        """
        pattern = r'([a-zA-Zà-úÀ-ÚçÇ])-[\s\n]+([a-zà-úç])'
        return re.sub(pattern, r'\1\2', text)

    def _execute_dry_run(self, chunks):
        self.log("--- INÍCIO RELATÓRIO DRY-RUN ---", 'DRY-RUN')
        self.log(f"Total Chunks: {len(chunks)}", 'DRY-RUN')
        
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
                
                self._print_progress(i + 1, total, start_time, label="Vetorização")
                
                elapsed = time.time() - start_time
                avg = elapsed / (i + 1)
                self.log(f"Chunk {i+1}/{total} vetorizado. Méd: {avg:.2f}s/item", 'INFO', to_file_only=True)

            except Exception as e:
                self.log(f"Erro vetorizando chunk {i}: {e}", 'ERROR')

        print("") 
        
        if db_objs:
            batch_size = 500
            for i in range(0, len(db_objs), batch_size):
                DocumentChunk.objects.bulk_create(db_objs[i:i+batch_size])
            
            doc.status = Document.DocumentStatus.COMPLETED
            doc.save()
            self.log("Ingestão e Vetorização finalizadas.", 'SUCCESS')
            self._unload_model(settings.OLLAMA_EMBEDDING_MODEL)
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
        
        if iteration == total and self.log_handle:
            self.log_handle.write(f"\n[{label} Concluído] Total tempo: {str(timedelta(seconds=int(elapsed_time)))}\n")

    def _vision_inference(self, model, prompt, image_b64):
        try:
            resp = ollama_client.generate(
                model=model, 
                prompt=prompt, 
                images=[image_b64], 
                options={"temperature": 0.1}
            )
            return resp.get('response', '').strip()
        except Exception as e:
            self.log(f"Erro Vision: {e}", 'ERROR')
            return None

    def _unload_model(self, model):
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