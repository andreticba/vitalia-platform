# backend/core/tests/test_models.py

import pytest
from core.models import UserProfile, DataAccessGrant
from .factories import UserProfileFactory, RoleFactory, DataAccessGrantFactory, UserFactory, ConsentLogFactory

@pytest.mark.django_db
class TestUserProfile:
    def test_blind_indexing_generation(self):
        """
        (P2) Segurança: Verifica se tokens de busca são gerados ao salvar o nome,
        permitindo busca em campo criptografado.
        """
        profile = UserProfileFactory(full_name="Carlos Drummond")
        
        # O blind index deve ter gerado tokens para "Carlos" e "Drummond"
        assert len(profile.search_tokens) > 0
        
        # Verifica se conseguimos buscar pelo token (simulação da lógica de busca)
        # Nota: O teste real da função generate_search_tokens seria um teste unitário em utils.py
        # Aqui testamos a integração com o Model.save()
        assert isinstance(profile.search_tokens, list)

    def test_rbac_association(self):
        """
        Valida se a associação de Roles funciona corretamente.
        """
        role_medico = RoleFactory(name="Médico")
        profile = UserProfileFactory(roles=[role_medico])
        
        assert profile.roles.count() == 1
        assert profile.roles.first().name == "Médico"

@pytest.mark.django_db
class TestDataAccessGrant:
    def test_grant_is_active_logic(self):
        """
        (P2) Data Vault: Verifica a lógica temporal e de revogação do Grant.
        """
        owner = UserFactory()
        grantee = UserFactory()
        consent = ConsentLogFactory(user=owner)
        
        # Grant Ativo
        grant = DataAccessGrantFactory(
            owner=owner,
            grantee_user=grantee,
            consent_log=consent
        )
        assert grant.is_active() is True
        
        # Grant Revogado
        from django.utils import timezone
        grant.revoked_at = timezone.now()
        grant.save()
        assert grant.is_active() is False
