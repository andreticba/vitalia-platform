# backend/medical/management/commands/update_bone_metadata_granular.py em 2025-12-14 11:48

from django.core.management.base import BaseCommand
from django.db import transaction
from medical.models import Bone

class Command(BaseCommand):
    help = 'Atualiza metadados ósseos com granularidade máxima (C1-C7, T1-T12, L1-L5, Costelas individuais).'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando carga de Inteligência Clínica Granular...'))

        # Lista extraída do OCR (Mapeada para os nomes do nosso DB)
        # Formato: (Nome_No_DB, Descrição, Nota_Clínica)
        granular_data = [
            # ================= COLUNA CERVICAL =================
            (
                "Atlas (C1)",
                "Primeira vértebra cervical. Não possui corpo e nem espinho. Consiste em arcos anterior e posterior, e duas massas laterais.",
                "A Luxação atlantoaxial por ruptura do ligamento cruciforme pode levar à compressão da medula."
            ),
            (
                "Áxis (C2)",
                "Segunda vértebra cervical. Caracterizada pelo dens (processo odontoide) que projeta superiormente para articulação com o atlas, permitindo rotação.",
                "Fratura de Hangman (pedículos do áxis) pode esmagar a medula espinhal, sendo uma lesão grave."
            ),
            (
                "Vértebra Cervical C3",
                "Vértebra cervical típica. Possui corpo curto e processo espinhoso bífido. As vértebras cervicais são caracterizadas pela presença de forames transversários.",
                "Lesões acima de C5 podem paralisar o diafragma."
            ),
            (
                "Vértebra Cervical C4",
                "Vértebra cervical típica. Seus processos transversos contêm forames para a artéria e veias vertebrais.",
                "Não encontrado."
            ),
            (
                "Vértebra Cervical C5",
                "Vértebra cervical típica. Os nervos espinhais C5 a C8 formam o plexo braquial que inerva o membro superior.",
                "Não encontrado."
            ),
            (
                "Vértebra Cervical C6",
                "Vértebra cervical típica. Articulações uncovertebrais podem ocorrer lateralmente e causar patologias.",
                "Não encontrado."
            ),
            (
                "Vértebra Cervical C7",
                "A vértebra proeminente, possui processo espinhoso longo, horizontal e não bífido.",
                "Não encontrado."
            ),

            # ================= COLUNA TORÁCICA =================
            (
                "Vértebra Torácica T1",
                "A vértebra torácica. O corpo possui uma faceta costal completa superiormente para a cabeça da Costela I, e uma inferior para a Costela II.",
                "Não encontrado."
            ),
            (
                "Vértebra Torácica T2",
                "Vértebra torácica típica, com corpo em forma de coração e forame vertebral circular. Articula com costelas II.",
                "Não encontrado."
            ),
            (
                "Vértebra Torácica T3",
                "Vértebra torácica típica. A articulação do processo transverso com o tubérculo da costela é importante para o movimento respiratório.",
                "Não encontrado."
            ),
            (
                "Vértebra Torácica T4",
                "Vértebra torácica. O nível TIV/V (ângulo esternal) é um marco chave onde a traqueia se bifurca e a aorta muda de curso.",
                "Lesão do disco TIV/V pode impulsionar material para o canal vertebral."
            ),
            (
                "Vértebra Torácica T5",
                "Vértebra torácica típica. As facetas articulares são orientadas verticalmente, o que facilita a rotação.",
                "A cifose (curvatura torácica anormal) é comum na região."
            ),
            (
                "Vértebra Torácica T6",
                "Vértebra torácica típica. Articulações com as costelas TII a TXII. São cruciais para a expansão e retração do tórax durante a respiração.",
                "Não encontrado."
            ),
            # T7 a T9 assumem descrição genérica se não houver específica, mas o OCR menciona T7-T11
            (
                "Vértebra Torácica T7",
                "Vértebra torácica típica. Os nervos torácicos (intercostais) T7 a T11 inervam a parede torácica e abdominal.",
                "Não encontrado."
            ),
            (
                "Vértebra Torácica T8",
                "Vértebra torácica típica. O hiato da veia cava no diafragma está aproximadamente no nível TVIII.",
                "Não encontrado."
            ),
            (
                "Vértebra Torácica T9",
                "Vértebra torácica, parte da coluna. A coluna torácica tem estabilidade relativa maior que a cervical e lombar.",
                "Não encontrado."
            ),
            (
                "Vértebra Torácica T10",
                "Vértebra torácica. Articula apenas com a décima costela. O hiato esofágico está aproximadamente no nível TX. O diafragma se insere nas vértebras lombares (L1-L3) e na TXII.",
                "Não encontrado."
            ),
            (
                "Vértebra Torácica T11",
                "Vértebra torácica atípica. Articula apenas com a cabeça de sua própria costela e não tem facetas transversais.",
                "Não encontrado."
            ),
            (
                "Vértebra Torácica T12",
                "Vértebra torácica atípica. Articula apenas com a cabeça de sua própria costela. O hiato aórtico passa abaixo dela.",
                "O nervo subcostal (T12) supre a parede abdominal e pode ser lesionado em cirurgias abdominais."
            ),

            # ================= COLUNA LOMBAR =================
            (
                "Vértebra Lombar L1",
                "Vértebra lombar. Marca o nível aproximado de origem do tronco celíaco e artéria mesentérica superior.",
                "Hérnia de disco lombar (como L1-L2) pode comprimir raízes nervosas e causar dor."
            ),
            (
                "Vértebra Lombar L2",
                "Vértebra lombar. O forame vertebral é triangular. A medula espinhal termina aproximadamente no nível L1/L2.",
                "Uma punção lombar é realizada abaixo de LII para coletar LCR sem lesionar a medula."
            ),
            (
                "Vértebra Lombar L3",
                "Vértebra lombar. O umbigo normalmente está no nível LIII/LIV. É o nível de origem do nervo obturador.",
                "Não encontrado."
            ),
            (
                "Vértebra Lombar L4",
                "Vértebra lombar. O plano supracristal (topo das cristas ilíacas) passa pelo corpo da L4.",
                "O deslizamento anterior de uma vértebra sobre a outra (espondilolistese) ocorre comumente em L4-L5."
            ),
            (
                "Vértebra Lombar L5",
                "A vértebra lombar. É a vértebra de maior corpo. O disco L5/S1 é o mais espesso anteriormente, devido à curvatura sacral.",
                "Uma protrusão do disco L4/L5 pode afetar a raiz nervosa L5."
            ),

            # ================= CAIXA TORÁCICA (COSTELAS) =================
            (
                "Costela 1",
                "A Costela I é a mais larga e curta. É flutuante no plano horizontal, possui tubérculo escaleno e sulcos para A. e V. subclávia.",
                "Fratura da Costela I é grave e pode lesionar o plexo braquial e vasos subclávios."
            ),
            (
                "Costela 2",
                "Costela típica. Articula com o esterno no ângulo esternal (TIV/V).",
                "Costelas médias são mais vulneráveis à fratura."
            ),
            # Costelas 3 a 7 (Verdadeiras)
            (
                "Costela 3", "Costela típica. É uma costela verdadeira (true rib) pois articula diretamente com o esterno.", "Não encontrado."
            ),
            (
                "Costela 4", "Costela típica. Costelas I a VII são verdadeiras.", "Não encontrado."
            ),
            (
                "Costela 5", "Costela típica. A artéria intercostal posterior e o nervo passam no sulco costal (VAN).", "Não encontrado."
            ),
            (
                "Costela 6", "Costela típica. A base do pulmão se estende até a Costela VI na linha hemiclavicular.", "Não encontrado."
            ),
            (
                "Costela 7", "A última costela verdadeira (true rib), ligada diretamente ao esterno.", "Não encontrado."
            ),
            # Falsas
            (
                "Costela 8", "Costela falsa (false rib), ligada à costela acima.", "Não encontrado."
            ),
            (
                "Costela 9", "Costela falsa, parte da margem costal.", "Não encontrado."
            ),
            (
                "Costela 10", "Costela falsa, parte da margem costal.", "Não encontrado."
            ),
            # Flutuantes
            (
                "Costela 11", "Costela flutuante, não tem conexão anterior.", "Fraturas das costelas inferiores podem rasgar o diafragma, resultando em hérnia diafragmática."
            ),
            (
                "Costela 12", "Costela flutuante, não tem conexão anterior.", "Fraturas das costelas inferiores podem rasgar o diafragma."
            ),

            # ================= MÃO (METACARPOS) =================
            (
                "Metacarpo I",
                "Metacarpo do polegar. É o mais curto e o mais móvel. Sua articulação é do tipo selar.",
                "Fratura de Bennett (base do metacarpo do polegar)."
            ),
            (
                "Metacarpo II",
                "Metacarpo. O mais longo. A cabeça forma os nós do punho. É unido ao metacarpo III pelo ligamento transverso.",
                "Fratura de Boxer (pescoços do 2º e 3º metacarpos)."
            ),
            (
                "Metacarpo III",
                "Metacarpo. Articula com o capitato. É unido aos outros por ligamentos transversos.",
                "Fratura de Boxer (pescoços do 2º e 3º metacarpos)."
            ),
            (
                "Metacarpo IV",
                "Metacarpo. Articula com o hamato.",
                "Não encontrado."
            ),
            (
                "Metacarpo V",
                "Metacarpo do dedo mínimo. O movimento metacarpofalângico é biaxial.",
                "Fratura de Boxer (comum no 5º em boxeadores não treinados)."
            ),

            # ================= PÉ (METATARSOS) =================
            (
                "Metatarso I",
                "Metatarsal associado ao hálux. É o mais curto e mais grosso. Possui sesamoides proeminentes na face plantar.",
                "Fratura de Marcha (stress fracture)."
            ),
            (
                "Metatarso II",
                "Metatarsal. O mais longo. A base articula com o cuneiforme.",
                "Fratura de Marcha (stress fracture)."
            ),
            (
                "Metatarso III",
                "Metatarsal. As cabeças são unidas pelo ligamento transverso metatarsal.",
                "Fratura de Marcha (stress fracture)."
            ),
            (
                "Metatarso IV",
                "Metatarsal. As cabeças são unidas pelo ligamento transverso metatarsal.",
                "Fratura de Marcha (stress fracture)."
            ),
            (
                "Metatarso V",
                "Metatarsal. A base tem uma tuberosidade para inserção do fibular breve.",
                "Fratura de Marcha (stress fracture)."
            ),
            
            # ================= CLAVÍCULA E ESCÁPULA (Detalhes) =================
            (
                "Clavícula",
                "Osso longo em forma de S. É o único osso longo a se ossificar por via intramembranosa. Articula com esterno e acrômio.",
                "Fratura no terço médio é a mais comum, deslocando o fragmento proximal para cima pelo esternocleidomastoideo."
            ),
            (
                "Escápula",
                "Osso triangular que forma a cintura escapular. Possui espinha, acrômio, e cavidade glenoidal, a qual é aprofundada pelo lábio glenoidal.",
                "A calcificação do ligamento transverso superior escapular pode comprimir o nervo supraescapular, afetando o supra e o infraespinhal."
            ),
            
            # ================= MEMBRO INFERIOR (Detalhes) =================
            (
                "Fêmur",
                "Osso mais longo e forte. Colo forma um ângulo de 125º com a diáfise. O trocânter maior insere o glúteo médio/mínimo.",
                "Fratura do colo tem risco de necrose isquêmica da cabeça (devido à interrupção da A. circunflexa femoral medial)."
            ),
            (
                "Tíbia",
                "Osso medial e de sustentação de peso na perna. Os côndilos articulam com o fêmur. A tuberosidade tibial insere o ligamento patelar.",
                "Fratura de Bumper (côndilo tibial) pode estar associada a lesão do nervo fibular comum."
            ),
            (
                "Fíbula",
                "Osso lateral da perna. Pouca função na sustentação de peso. O maléolo lateral articula com o tálus. O colo é vulnerável à lesão do nervo fibular.",
                "Fratura do colo pode lesionar o nervo fibular comum, causando pé caído (dorsiflexão perdida)."
            ),
            (
                "Patela",
                "O maior sesamoide. Está dentro do tendão do quadríceps. Aumenta a alavancagem na extensão do joelho e estabiliza a articulação.",
                "Fratura transversa resulta de um golpe ou contração súbita do quadríceps, sendo comum."
            ),
            (
                "Tálus",
                "Osso superior proximal do tarso. Transmite o peso do corpo e é o único tarsal sem fixação muscular. A cabeça é a chave do arco longitudinal medial.",
                "Fratura do colo do tálus pode interromper o suprimento sanguíneo, causando osteonecrose."
            ),
            (
                "Calcâneo",
                "O maior e mais forte osso do pé. Forma o calcanhar e insere o tendão de Aquiles. O sustentáculo do tálus suporta a cabeça do tálus.",
                "A ruptura do tendão de Aquiles incapacita o tríceps sural e a flexão plantar."
            ),
            (
                "Cuboide",
                "O tarsal mais lateral e posterior. Serve como chave do arco longitudinal lateral. Possui um sulco para o tendão do fibular longo.",
                "Não encontrado."
            )
        ]

        updated_count = 0
        not_found_count = 0

        with transaction.atomic():
            for name, desc, notes in granular_data:
                # Busca Exata (Pois agora temos os nomes corretos do DB)
                try:
                    bone = Bone.objects.get(name__iexact=name)
                    bone.description = desc
                    bone.clinical_notes = notes
                    bone.save()
                    updated_count += 1
                    # self.stdout.write(f"Atualizado: {name}") # Verbose opcional
                except Bone.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Osso não encontrado no DB: {name}"))
                    not_found_count += 1

        self.stdout.write(self.style.SUCCESS(f'--------------------------------------'))
        self.stdout.write(self.style.SUCCESS(f'Atualização Granular Concluída: {updated_count} ossos enriquecidos.'))
        if not_found_count > 0:
            self.stdout.write(self.style.WARNING(f'Não encontrados: {not_found_count} (Verifique se o seed granular rodou).'))