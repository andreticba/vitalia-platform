# backend/core/utils.py em 2025-12-14 11:48


import hashlib
import hmac
import os
import uuid
import unicodedata
from django.conf import settings
from django.utils.encoding import force_bytes

# Lista básica de stopwords para nomes em PT-BR (Preposições e Artigos)
STOPWORDS = {
    'DA', 'DE', 'DO', 'DAS', 'DOS', 
    'E', 'A', 'O', 'EM', 'POR', 'PARA'
}

def normalize_text(text: str) -> str:
    """
    Normaliza o texto:
    1. Remove acentos (Decomposição NFKD + Encode ASCII).
    2. Converte para Maiúsculas.
    3. Remove espaços extras e invisíveis.
    
    Ex: "André   da  Silva" -> "ANDRE DA SILVA"
    """
    if not text:
        return ""
    
    # 1. Normalização Unicode (separa o acento da letra) e remove não-ASCII
    text_normalized = unicodedata.normalize('NFKD', text)
    text_ascii = text_normalized.encode('ASCII', 'ignore').decode('ASCII')
    
    # 2. Uppercase e 3. Remoção de espaços extras
    return " ".join(text_ascii.upper().split())

def generate_search_tokens(text: str) -> list[str]:
    """
    Gera tokens determinísticos (HMAC) para permitir busca exata 
    em campos criptografados (Blind Indexing) com normalização robusta.
    
    Fluxo:
    1. "André da Silva" -> Normaliza -> "ANDRE DA SILVA"
    2. Split -> ["ANDRE", "DA", "SILVA"]
    3. Filter Stopwords -> ["ANDRE", "SILVA"]
    4. Hash -> [HMAC("ANDRE"), HMAC("SILVA")]
    """
    if not text:
        return []

    # Aplica a normalização pesada
    clean_text = normalize_text(text)
    parts = clean_text.split()
    
    tokens = []
    
    # Usa a SECRET_KEY do Django como chave do HMAC para segurança
    # Isso impede que alguém com acesso apenas ao DB tente gerar Rainbow Tables
    key = force_bytes(settings.SECRET_KEY)

    for part in parts:
        # Filtra stopwords (ex: "DA", "DE") e partes muito curtas
        if part in STOPWORDS or len(part) < 2:
            continue
            
        # Gera o HMAC-SHA256 da parte do nome
        msg = force_bytes(part)
        token = hmac.new(key, msg, hashlib.sha256).hexdigest()
        
        # Trunca para 32 chars para economizar índice e armazenamento
        # (SHA256 hex tem 64 chars, 32 já garante colisão quase nula para este fim)
        tokens.append(token[:32])
        
    return tokens

def secure_file_upload_path(instance, filename):
    """
    Gera um caminho de arquivo anonimizado.
    Substitui o nome original do arquivo por um UUID para evitar
    vazamento de PII através do nome do arquivo (ex: 'exame_joao_silva.pdf').
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    
    # Determina o diretório com base no tipo do model
    # Isso evita "magic strings" e organiza o bucket S3/Media
    # Ex: secure_uploads/medicalexam/2024/05/uuid.pdf
    model_name = instance._meta.model_name.lower()
    
    # Adiciona particionamento por data para evitar diretórios gigantes
    from django.utils import timezone
    now = timezone.now()
    
    return os.path.join(f"secure_uploads/{model_name}/{now.year}/{now.month}", filename)
