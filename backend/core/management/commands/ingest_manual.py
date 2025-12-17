# backend/core/management/commands/ingest_manual.py em 2025-12-14 11:48

import os
import hashlib
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from core.models import Organization, Document, DocumentChunk, UserProfile
from core.clients import unstructured_client, ollama_client

User = get_user_model()

class Command(BaseCommand):
    help = 'Ingere manualmente um documento PDF local para o Knowledge Base.'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str, help='Nome do arquivo dentro de backend/docs_to_ingest/')

    def handle(self, *args, **options):
        filename = options['filename']
        file_path = os.path.join(settings.BASE_DIR, 'docs_to_ingest', filename)

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {file_path}'))
            return

        self.stdout.write(self.style.WARNING(f'Iniciando ingestão de: {filename}'))

        # 1. Identificar Dono (Admin/Platform)
        try:
            # Pega a organização da plataforma criada no seed_system_init
            org = Organization.objects.get(org_type=Organization.OrgType.PLATFORM)
            # Pega um usuário admin (fallback para o primeiro superusuário)
            user = User.objects.filter(is_superuser=True).first()
        except Organization.DoesNotExist:
            self.stdout.write(self.style.ERROR('Organização Vitalia Platform não encontrada. Rode seed_system_init.'))
            return

        # 2. Calcular Hash (Evitar duplicatas)
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
            file_size = os.path.getsize(file_path)

        # 3. Criar Registro do Documento
        doc, created = Document.objects.get_or_create(
            organization=org,
            file_hash=file_hash,
            defaults={
                'file_name': filename,
                'file_size_bytes': file_size,
                'uploaded_by_user': user,
                'status': Document.DocumentStatus.PROCESSING
            }
        )

        if not created and doc.status == Document.DocumentStatus.COMPLETED:
            self.stdout.write(self.style.SUCCESS('Este documento já foi processado anteriormente.'))
            return
        
        # Se já existia mas falhou, reseta
        doc.status = Document.DocumentStatus.PROCESSING
        doc.save()

        try:
            # 4. Extração de Texto (Unstructured)
            self.stdout.write('Extraindo texto via Unstructured API...')
            chunks_data = unstructured_client.partition_file(
                document_id=str(doc.id),
                file_path=file_path,
                file_name=filename,
                file_size_bytes=file_size
            )
            
            if not chunks_data:
                self.stdout.write(self.style.ERROR('Nenhum texto extraído. O PDF pode ser imagem pura?'))
                doc.status = Document.DocumentStatus.FAILED
                doc.save()
                return

            self.stdout.write(f'Texto extraído. {len(chunks_data)} segmentos encontrados.')

            # 5. Vetorização (Ollama)
            self.stdout.write('Gerando Embeddings via Ollama (Llama 3)...')
            doc.status = Document.DocumentStatus.EMBEDDING
            doc.save()

            # Limpa chunks antigos se for reprocessamento
            doc.chunks.all().delete()

            chunks_to_create = []
            
            for i, chunk in enumerate(chunks_data):
                content = chunk.get("text", "").strip()
                if not content or len(content) < 10: # Ignora ruído muito curto
                    continue

                # Gera o vetor
                embedding_response = ollama_client.embed(
                    settings.OLLAMA_EMBEDDING_MODEL, 
                    content
                )
                
                chunks_to_create.append(
                    DocumentChunk(
                        document=doc,
                        content=content,
                        embedding=embedding_response["embedding"],
                        page_number=chunk.get("metadata", {}).get("page_number"),
                        metadata=chunk.get("metadata", {})
                    )
                )
                
                if i % 10 == 0:
                    self.stdout.write(f"  > Processados {i}/{len(chunks_data)}...")

            # 6. Salvar no Banco
            self.stdout.write('Salvando no Banco de Dados...')
            DocumentChunk.objects.bulk_create(chunks_to_create)

            doc.status = Document.DocumentStatus.COMPLETED
            doc.save()

            self.stdout.write(self.style.SUCCESS(f'SUCESSO! Documento ingerido. {len(chunks_to_create)} vetores criados.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro fatal na ingestão: {e}'))
            doc.status = Document.DocumentStatus.FAILED
            doc.save()