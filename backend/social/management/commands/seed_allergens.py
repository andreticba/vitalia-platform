# backend/social/management/commands/seed_allergens.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from social.models import Allergen
from django.db import transaction

class Command(BaseCommand):
    help = 'Popula a tabela de Alérgenos conforme a RDC 26/2015 da ANVISA.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando seed de Alérgenos (RDC 26/2015)...'))

        # Lista Oficial RDC 26/2015
        allergens_data = [
            # Glúten e Cereais
            ('Trigo', 'Inclui centeio, cevada, aveia e suas estirpes hibridizadas.', 'HIGH'),
            ('Centeio', 'Cereal contendo glúten.', 'HIGH'),
            ('Cevada', 'Cereal contendo glúten.', 'HIGH'),
            ('Aveia', 'Frequentemente contaminada por glúten.', 'MEDIUM'),
            
            # Proteínas Animais
            ('Leite de Vaca', 'Inclui derivados (lactose, caseína).', 'HIGH'),
            ('Ovos', 'Clara e gema.', 'HIGH'),
            ('Peixes', 'Todas as espécies.', 'HIGH'),
            ('Crustáceos', 'Camarão, lagosta, caranguejo, etc.', 'HIGH'),
            ('Moluscos', 'Lula, polvo, mariscos (Embora RDC foque em crustáceos, é boa prática incluir).', 'HIGH'),
            
            # Oleaginosas e Grãos
            ('Amendoim', 'Leguminosa de alto risco anafilático.', 'HIGH'),
            ('Soja', 'Inclui derivados.', 'HIGH'),
            ('Amêndoa', 'Oleaginosa.', 'HIGH'),
            ('Avelãs', 'Oleaginosa.', 'HIGH'),
            ('Castanha-de-caju', 'Oleaginosa.', 'HIGH'),
            ('Castanha-do-brasil', 'Castanha-do-pará.', 'HIGH'),
            ('Macadâmias', 'Oleaginosa.', 'HIGH'),
            ('Nozes', 'Oleaginosa.', 'HIGH'),
            ('Pecãs', 'Oleaginosa.', 'HIGH'),
            ('Pistaches', 'Oleaginosa.', 'HIGH'),
            ('Pinoli', 'Oleaginosa.', 'HIGH'),
            ('Castanhas', 'Categoria geral para outras castanhas.', 'HIGH'),
            
            # Outros
            ('Látex Natural', 'Risco de reação cruzada com frutas (Síndrome Látex-Fruta).', 'HIGH'),
            ('Sulfitos', 'Dióxido de enxofre e sulfitos (em concentrações >= 10mg/kg).', 'MEDIUM'),
        ]

        created_count = 0
        
        with transaction.atomic():
            for name, desc, severity in allergens_data:
                obj, created = Allergen.objects.get_or_create(
                    name=name,
                    defaults={
                        'description': desc,
                        'severity_level': severity
                    }
                )
                if created:
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(f'{created_count} novos alérgenos criados.'))
        self.stdout.write(self.style.SUCCESS('Seed de Alérgenos (RDC 26/2015) finalizado.'))