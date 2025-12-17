# backend/core/clients.py em 2025-12-14 11:48

import httpx
import json
import logging
import os
from typing import Any, Dict
from django.conf import settings

logger = logging.getLogger(__name__)

class APIClientError(Exception):
    pass

class OllamaServiceError(APIClientError):
    pass

class UnstructuredServiceError(APIClientError):
    pass

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.timeout = httpx.Timeout(1200.0) 

    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Ollama Error: {e}")
            raise OllamaServiceError(str(e))

    def embed(self, model: str, prompt: str) -> Dict[str, Any]:
        return self._make_request("/api/embeddings", {"model": model, "prompt": prompt})

    def generate(self, model: str, prompt: str, is_json: bool = False, options: Dict = None, images: list = None, keep_alive: int = None) -> Dict[str, Any]:
        """
        Gera completude de texto ou visão.
        :param images: Lista de strings base64 para modelos de visão (LLaVA).
        :param keep_alive: Tempo em segundos para manter na VRAM (0 = unload imediato).
        """
        payload = {
            "model": model, 
            "prompt": prompt, 
            "stream": False, 
            "options": options or {}
        }
        
        if is_json: 
            payload["format"] = "json"
        
        if images:
            payload["images"] = images
            
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive # ex: 0 ou "5m"

        return self._make_request("/api/generate", payload)

class UnstructuredClient:
    def __init__(self):
        self.api_url = os.getenv("UNSTRUCTURED_API_URL", "http://localhost:8002/general/v0/general")
        self.base_timeout = 180 # Começa com 3 minutos
        self.seconds_per_mb = 1200 # 1 minuto por MB (Conservador para PDFs densos)

    def _calculate_timeout(self, file_size_bytes: int) -> float:
        size_mb = file_size_bytes / (1024 * 1024)
        # Timeout mínimo de 10 minutos, máximo de 60 minutos
        timeout = self.base_timeout + (size_mb * self.seconds_per_mb)
        return max(600.0, min(timeout, 6000.0))

    def partition_file(self, document_id: str, file_path: str, file_name: str, file_size_bytes: int) -> list:
        timeout = self._calculate_timeout(file_size_bytes)
        logger.info(f"[{document_id}] Timeout definido para: {timeout:.1f}s")
        
        try:
            with open(file_path, "rb") as f:
                files = {"files": (file_name, f)}
                # Strategy 'auto' ou 'hi_res'
                # 'hi_res' usa OCR e detecta tabelas melhor, mas é MUITO lento e exige container pesado.
                # Vamos tentar 'fast' ou 'auto' primeiro. Se falhar tabelas, mudamos a estratégia.
                data = {
                    "strategy": "auto", 
                    "chunking_strategy": "by_title",
                    "combine_text_under_n_chars": 200, # Combina legendas pequenas
                    "max_characters": 2000 # Chunks de tamanho razoável
                }
                
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(self.api_url, files=files, data=data)
                    response.raise_for_status()
                    return response.json()
                    
        except Exception as e:
            logger.error(f"[{document_id}] Unstructured Error: {e}")
            raise UnstructuredServiceError(str(e))

ollama_client = OllamaClient()
unstructured_client = UnstructuredClient()