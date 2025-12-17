# backend/core/tasks.py em 2025-12-14 11:48

import os
from celery import shared_task
from django.conf import settings
from django.db import transaction
from core.models import Document, DocumentChunk
from core.clients import unstructured_client, ollama_client, UnstructuredServiceError

import logging
logger = logging.getLogger(__name__)

@shared_task(queue='heavy_ingestion')
def process_document_ingestion(document_id: str):
    """
    Task Celery para processar um documento:
    1. Envia para Unstructured (OCR/Parse)
    2. Recebe chunks de texto
    3. Envia para Ollama (Embedding)
    4. Salva no banco
    """
    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.error(f"Task falhou: Documento {document_id} não encontrado.")
        return

    # Atualiza status
    doc.status = Document.DocumentStatus.PROCESSING
    doc.save(update_fields=['status'])

    # Caminho do arquivo (supondo armazenamento local em media/)
    # Se estiver usando S3, a lógica de obter o arquivo muda um pouco
    file_path = doc.file.path if doc.file else None
    
    if not file_path or not os.path.exists(file_path):
        # Fallback para ingestão manual onde o arquivo pode não estar no Field File
        # mas sim numa pasta temporária referenciada logicamente
        # (Para o MVP, assumimos que está no media root)
        logger.error(f"Arquivo físico não encontrado para Doc {doc.id}")
        doc.status = Document.DocumentStatus.FAILED
        doc.save()
        return

    try:
        # 1. Extração
        chunks_data = unstructured_client.partition_file(
            document_id=str(doc.id),
            file_path=file_path,
            file_name=doc.file_name,
            file_size_bytes=doc.file_size_bytes
        )

        doc.status = Document.DocumentStatus.EMBEDDING
        doc.save(update_fields=['status'])

        # 2. Vetorização
        chunks_to_create = []
        for item in chunks_data:
            text = item.get('text', '').strip()
            if len(text) < 10: continue

            embedding_resp = ollama_client.embed(settings.OLLAMA_EMBEDDING_MODEL, text)
            
            chunks_to_create.append(
                DocumentChunk(
                    document=doc,
                    content=text,
                    embedding=embedding_resp['embedding'],
                    page_number=item.get('metadata', {}).get('page_number'),
                    metadata=item.get('metadata', {})
                )
            )

        # 3. Persistência
        with transaction.atomic():
            # Limpa anteriores se houver (reprocessamento)
            doc.chunks.all().delete()
            DocumentChunk.objects.bulk_create(chunks_to_create)
            
            doc.status = Document.DocumentStatus.COMPLETED
            doc.save(update_fields=['status'])
            
        logger.info(f"Documento {doc.id} processado com sucesso. {len(chunks_to_create)} chunks.")

    except Exception as e:
        logger.error(f"Erro processando documento {doc.id}: {e}", exc_info=True)
        doc.status = Document.DocumentStatus.FAILED
        doc.save(update_fields=['status'])