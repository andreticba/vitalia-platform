# backend/core/apps.py em 2025-12-14 11:48
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        try:
            import core.signals
        except ImportError:
            pass

        # --- FIX DEFINITIVO: Psycopg2 Memoryview -> Bytes ---
        try:
            import psycopg2
            from psycopg2.extensions import new_type, register_type

            # OID 17 é o identificador do tipo BYTEA no PostgreSQL
            BYTEA_OID = 17

            def cast_bytea_to_bytes(value, cur):
                """
                Converte o valor BYTEA bruto (string hex) em bytes puros.
                
                Fluxo:
                1. Recebe 'value' como string (ex: '\\xdeadbeef').
                2. Codifica para bytes (ex: b'\\xdeadbeef') para o parser C aceitar.
                3. Usa psycopg2.BINARY para parsear o Hex/Escape e gerar um buffer.
                4. Converte o buffer final para 'bytes' do Python (pickleable).
                """
                if value is None:
                    return None
                
                # Passo 1: O driver entrega string, mas a função C interna pode exigir bytes.
                # A sugestão da solução foi codificar antes.
                if isinstance(value, str):
                    value = value.encode('utf-8')
                
                # Passo 2: Usa o parser padrão do Psycopg2 para decodificar o Hex do Postgres
                # Isso retorna um buffer/memoryview
                buffer_val = psycopg2.BINARY(value, cur)
                
                # Passo 3: Converte o buffer para bytes imutáveis (serializáveis)
                if buffer_val is not None:
                    return bytes(buffer_val)
                
                return None

            # Registra o novo conversor
            BYTEA_BYTES = new_type((BYTEA_OID,), "BYTEA_BYTES", cast_bytea_to_bytes)
            register_type(BYTEA_BYTES)
            
            logger.info("Patch Psycopg2 (Safe Bytes Cast) aplicado com sucesso.")
            
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Erro ao aplicar patch do Psycopg2: {e}")
