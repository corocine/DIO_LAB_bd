from faker import Faker
import mysql.connector
import random
from datetime import datetime, timedelta

# ----------------------------------------------------
# 1. CONFIGURAÇÃO DE CONEXÃO E VARIÁVEIS
# ----------------------------------------------------

DB_CONFIG = {
    'user': 'root',
    'password': 'admin123',
    'host': '127.0.0.1', 
    'port': 3308,         
    'database': 'oficina_db'
}

fake = Faker('pt_BR')
Faker.seed(4321)

NUM_MULTIPLIER = 3 
NUM_CLIENTES = 20 * NUM_MULTIPLIER # 60
NUM_MECANICOS = 5 * NUM_MULTIPLIER # 15
NUM_PECAS = 8 
NUM_SERVICOS_REF = 6
NUM_VEICULOS = 24 * NUM_MULTIPLIER # 72
NUM_OS = 33 * NUM_MULTIPLIER # 99 Ordens de Serviço

STATUS_OS = ['Emissao', 'Aguardando Aprovação', 'Em Execução', 'Concluída', 'Cancelada']

cliente_ids = list(range(1, NUM_CLIENTES + 1))
mecanico_ids = list(range(1, NUM_MECANICOS + 1))
peca_ids = list(range(1, NUM_PECAS + 1))
servico_ids = list(range(1, NUM_SERVICOS_REF + 1))
veiculo_ids = list(range(1, NUM_VEICULOS + 1))
os_ids = list(range(1, NUM_OS + 1))

dados_os_detalhe = {
    'servicos': [],
    'pecas': [],
    'equipe': []
}

# ----------------------------------------------------
# 2. FUNÇÃO DE INSERÇÃO E POPULAÇÃO
# ----------------------------------------------------

def execute_insert(cursor, sql, data=None):
    """Executa o comando SQL e lida com a inserção."""
    try:
        if data:
            cursor.execute(sql, data)
        else:
            cursor.execute(sql)
    except mysql.connector.Error as err:
        print(f"❌ Erro ao executar SQL: {err}")
        return False
    return True

def populate_database():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Conexão estabelecida com o MySQL.")

        # Limpar tabelas (TRUNCATE) - Em ordem de dependência
        print(f"Limpando {NUM_OS} Ordens de Serviço antigas e tabelas, respeitando as FKs...")
        limpeza = [
            "SET FOREIGN_KEY_CHECKS = 0", 
            "TRUNCATE TABLE os_equipe", "TRUNCATE TABLE os_peca", "TRUNCATE TABLE os_servico",
            "TRUNCATE TABLE ordem_servico", "TRUNCATE TABLE veiculo", 
            "TRUNCATE TABLE cliente", "TRUNCATE TABLE mecanico", 
            "TRUNCATE TABLE peca", "TRUNCATE TABLE servico_referencia",
            "SET FOREIGN_KEY_CHECKS = 1"
        ]
        for cmd in limpeza:
            execute_insert(cursor, cmd)

        # INSERÇÃO DAS TABELAS BASE (Pais)
        print("Inserindo Clientes, Mecânicos, Peças e Serviços de Referência...")

        sql_cliente = "INSERT INTO cliente (nome, telefone, endereco) VALUES (%s, %s, %s)"
        for _ in range(NUM_CLIENTES):
            data = (fake.name(), fake.phone_number()[:20], fake.address().replace('\n', ', '))
            execute_insert(cursor, sql_cliente, data)

        sql_mecanico = "INSERT INTO mecanico (codigo, nome, endereco, especialidade) VALUES (%s, %s, %s, %s)"
        especialidades = ['Motor', 'Elétrica', 'Suspensão', 'Freios', 'Funilaria']
        for mecanico_id in mecanico_ids:
            data = (f"MEC{mecanico_id:03}", fake.name(), fake.street_address(), random.choice(especialidades))
            execute_insert(cursor, sql_mecanico, data)

        sql_peca = "INSERT INTO peca (nome, descricao, valor_unitario) VALUES (%s, %s, %s)"
        nomes_pecas = ['Filtro de Óleo', 'Pastilha de Freio', 'Correia Dentada', 'Vela de Ignição', 'Bateria 60Ah', 'Amortecedor', 'Óleo Sintético', 'Lâmpada Farol']
        for nome_peca in nomes_pecas:
            data = (nome_peca, f"Descrição da peça: {nome_peca}", round(random.uniform(20.0, 500.0), 2))
            execute_insert(cursor, sql_peca, data)

        sql_servico_ref = "INSERT INTO servico_referencia (descricao, valor_mao_de_obra) VALUES (%s, %s)"
        servicos_ref_list = [
            ('Troca de Óleo e Filtro', 60.00), ('Revisão Básica', 150.00),
            ('Troca de Pastilhas', 90.00), ('Alinhamento e Balanceamento', 120.00),
            ('Diagnóstico Elétrico', 180.00), ('Reparo no Motor', 450.00)
        ]
        for descricao, valor in servicos_ref_list:
            execute_insert(cursor, sql_servico_ref, (descricao, valor))
            
        sql_veiculo = "INSERT INTO veiculo (placa, marca, modelo, ano, cliente_id) VALUES (%s, %s, %s, %s, %s)"
        marcas = ['Fiat', 'Ford', 'VW', 'GM', 'Honda', 'Toyota']
        modelos = ['Palio', 'Focus', 'Gol', 'Onix', 'Civic', 'Corolla', 'Polo', 'Ka']
        for _ in range(NUM_VEICULOS):
            data = (fake.license_plate(), random.choice(marcas), random.choice(modelos), random.randint(2000, 2024), random.choice(cliente_ids))
            execute_insert(cursor, sql_veiculo, data)

        # PRÉ-CÁLCULO E GERAÇÃO DA OS CENTRAL
        print(f"Gerando {NUM_OS} Ordens de Serviço e seus detalhes em memória...")
        
        papeis = ['Líder', 'Auxiliar', 'Estagiário'] 
        
        for os_id_fk in os_ids:
            custo_interno_total = 0
            
            status = random.choice(STATUS_OS)
            
            # LÓGICA DE INTEGRIDADE DE DADOS:
            min_servicos = 0
            min_pecas = 0
            
            if status in ['Concluída', 'Em Execução']:
                # 1. Garante DATA DE CONCLUSÃO PREVISTA
                data_conclusao_prevista = fake.date_time_between(start_date='now', end_date='+10d') 
                
                # 2. Garante PEÇAS OU SERVIÇOS (Regra de Negócio)
                if random.choice([True, False]):
                    min_servicos = 1
                else:
                    min_pecas = 1
            else:
                # Permite que a data prevista seja NULL para OS em status inicial
                data_conclusao_prevista = None
            
            # A) OS_SERVICO
            num_servicos_a_gerar = random.randint(min_servicos, 3) 
            servicos_usados = set()
            for _ in range(num_servicos_a_gerar):
                servico_id_fk = random.choice(servico_ids)
                if servico_id_fk not in servicos_usados:
                    servicos_usados.add(servico_id_fk)
                    valor = round(random.uniform(50.0, 500.0), 2)
                    custo_interno_total += valor
                    dados_os_detalhe['servicos'].append((os_id_fk, servico_id_fk, valor))
                    
            # B) OS_PECA
            num_pecas_a_gerar = random.randint(min_pecas, 2) 
            pecas_usadas = set()
            for _ in range(num_pecas_a_gerar):
                peca_id_fk = random.choice(peca_ids)
                if peca_id_fk not in pecas_usadas:
                    pecas_usadas.add(peca_id_fk)
                    qtd = random.randint(1, 4)
                    valor_unitario = round(random.uniform(10.0, 300.0), 2)
                    custo_interno_total += (qtd * valor_unitario)
                    dados_os_detalhe['pecas'].append((os_id_fk, peca_id_fk, qtd, valor_unitario))

            # C) OS_EQUIPE
            mecanicos_alocados = set()
            for i in range(random.randint(1, 2)):
                mecanico_id_fk = random.choice(mecanico_ids)
                if mecanico_id_fk not in mecanicos_alocados:
                    mecanicos_alocados.add(mecanico_id_fk)
                    papel = papeis[i] if i < len(papeis) else random.choice(papeis)
                    dados_os_detalhe['equipe'].append((os_id_fk, mecanico_id_fk, papel))
            
            # CALCULA O VALOR COBRADO (Valor total da OS)
            if custo_interno_total == 0:
                 valor_cobrado = round(random.uniform(50.0, 150.0), 2)
            else:
                 valor_cobrado = round(custo_interno_total * random.uniform(1.15, 1.30), 2)
            
            # INSERÇÃO DA ORDEM_SERVICO
            data_emissao = fake.date_time_between(start_date='-3y', end_date='now')
            aprovacao = True if status not in ['Emissao', 'Aguardando Aprovação', 'Cancelada'] else random.choice([True, False])
            
            sql_os = "INSERT INTO ordem_servico (os_id, numero_os, data_emissao, data_conclusao_prevista, status, valor_total, aprovacao_cliente, veiculo_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            data = (os_id_fk, f"OS{os_id_fk:05}", data_emissao, data_conclusao_prevista, status, valor_cobrado, aprovacao, random.choice(veiculo_ids))
            execute_insert(cursor, sql_os, data)


        # INSERÇÃO DOS DETALHES (Tabelas N:M)
        print("Inserindo Detalhes da OS (Serviços, Peças e Equipes)...")
        sql_os_servico = "INSERT INTO os_servico (os_id, servico_id, valor_servico) VALUES (%s, %s, %s)"
        for item in dados_os_detalhe['servicos']:
            execute_insert(cursor, sql_os_servico, item)
            
        sql_os_peca = "INSERT INTO os_peca (os_id, peca_id, quantidade, valor_unitario_peca) VALUES (%s, %s, %s, %s)"
        for item in dados_os_detalhe['pecas']:
            execute_insert(cursor, sql_os_peca, item)

        sql_os_equipe = "INSERT INTO os_equipe (os_id, mecanico_id, papel_na_equipe) VALUES (%s, %s, %s)"
        for item in dados_os_detalhe['equipe']:
            execute_insert(cursor, sql_os_equipe, item)

        conn.commit()
        print(f"\n✅ Banco de dados populado com sucesso (total de {NUM_OS} OS's).")

    except mysql.connector.Error as err:
        print(f"\n❌ ERRO FATAL de Conexão ou SQL: {err}")
        
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    populate_database()