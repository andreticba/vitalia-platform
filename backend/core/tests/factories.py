# backend/core/tests/factories.py

import factory
from django.contrib.auth.models import User
from core.models import (
    UserProfile, Organization, Role, Permission, 
    ParticipantProfile, ProfessionalProfile, DataAccessGrant, ConsentLog
)
from faker import Faker

fake = Faker('pt_BR')

class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Faker('company')
    org_type = Organization.OrgType.CLINIC

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')

class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'Role {n}')

class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    full_name = factory.Faker('name')
    cpf = factory.Faker('cpf')
    
    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for role in extracted:
                self.roles.add(role)

class ParticipantProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ParticipantProfile

    profile = factory.SubFactory(UserProfileFactory)
    autonomy_level = ParticipantProfile.AutonomyLevel.LEVEL_1_DEPENDENT

class ProfessionalProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProfessionalProfile

    profile = factory.SubFactory(UserProfileFactory)
    professional_level = ProfessionalProfile.ProfessionalLevel.SPECIALIST

class ConsentLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConsentLog

    user = factory.SubFactory(UserFactory)
    consent_type = ConsentLog.ConsentType.DATA_SHARING
    granted = True
    version = "1.0"

class DataAccessGrantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DataAccessGrant

    owner = factory.SubFactory(UserFactory)
    grantor = factory.LazyAttribute(lambda o: o.owner)
    consent_log = factory.SubFactory(ConsentLogFactory)
