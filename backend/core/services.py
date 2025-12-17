# backend/core/services.py em 2025-12-14 11:48

import logging
from django.conf import settings
from django.db.models import F
from pgvector.django import CosineDistance
from core.models import DocumentChunk, Document
from core.clients import ollama_client
from .models import DocumentChunk, AuditLog
from pgvector.django import CosineDistance

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.embedding_model = settings.OLLAMA_EMBEDDING_MODEL
        self.generation_model = settings.OLLAMA_GENERATION_MODEL

    def get_query_embedding(self, text: str) -> list[float]:
        """Gera o embedding para a pergunta do usuário."""
        response = ollama_client.embed(self.embedding_model, text)
        return response.get("embedding", [])

    def search_relevant_chunks(self, query_text: str, limit: int = 5, similarity_threshold: float = 0.3) -> list[DocumentChunk]:
        """
        Busca semântica no banco de dados.
        Retorna os chunks mais próximos da pergunta.
        """
        if not query_text:
            return []

        embedding = self.get_query_embedding(query_text)
        
        # Busca vetorial usando Cosine Distance (menor distância = maior similaridade)
        # Filtra apenas documentos processados (COMPLETED)
        chunks = DocumentChunk.objects.filter(
            document__status=Document.DocumentStatus.COMPLETED
        ).annotate(
            distance=CosineDistance('embedding', embedding)
        ).order_by('distance')[:limit]

        # Opcional: Filtrar por threshold de qualidade se necessário
        # return [c for c in chunks if c.distance < similarity_threshold]
        
        return list(chunks)

    def build_context(self, chunks: list[DocumentChunk]) -> str:
        """Monta o texto de contexto para o prompt."""
        if not chunks:
            return ""
            
        context_parts = []
        for i, chunk in enumerate(chunks):
            source = f"Fonte {i+1} ({chunk.document.file_name}, pág {chunk.page_number or '?'}):"
            context_parts.append(f"{source}\n{chunk.content}")
            
        return "\n\n---\n\n".join(context_parts)

    def query_with_rag(self, user_question: str) -> dict:
        """
        Fluxo completo: Pergunta -> Busca -> Prompt -> Resposta.
        """
        # 1. Recuperação
        chunks = self.search_relevant_chunks(user_question)
        
        if not chunks:
            return {
                "answer": "Não encontrei informações relevantes na base de conhecimento para responder a essa pergunta.",
                "sources": []
            }

        # 2. Construção do Prompt
        context_str = self.build_context(chunks)
        system_prompt = (
            "Você é a IA da Vitalia, uma plataforma de saúde. "
            "Responda à pergunta do usuário baseando-se ESTRITAMENTE no contexto fornecido abaixo. "
            "Se a resposta não estiver no contexto, diga que não sabe. "
            "Cite as fontes quando possível."
        )
        
        full_prompt = f"{system_prompt}\n\nCONTEXTO:\n{context_str}\n\nPERGUNTA:\n{user_question}"

        # 3. Geração
        response = ollama_client.generate(self.generation_model, full_prompt)
        
        return {
            "answer": response.get("response", ""),
            "sources": [
                {
                    "file": c.document.file_name,
                    "page": c.page_number,
                    "preview": c.content[:100] + "..."
                } 
                for c in chunks
            ]
        }

    def search_for_audit(self, query_text: str, limit: int = 5) -> list[dict]:
        """
        Busca chunks relevantes para auditoria técnica.
        Retorna o conteúdo + metadados da fonte (Livro/Página).
        """
        embedding = self.get_query_embedding(query_text)
        
        # Busca sem filtros de permissão (o Auditor tem acesso total ao Knowledge Base)
        chunks = (
            DocumentChunk.objects
            .annotate(distance=CosineDistance("embedding", embedding))
            .select_related('document')
            .order_by("distance")[:limit]
        )

        results = []
        for c in chunks:
            # Formata a fonte para evidência
            source_info = f"{c.document.file_name} (Pág. {c.page_number or '?'})"
            results.append({
                "content": c.content,
                "source": source_info,
                "distance": c.distance
            })
        
        return results
