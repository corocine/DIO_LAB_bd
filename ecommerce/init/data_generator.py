import mysql.connector
from faker import Faker
import random
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DB_CONFIG = {
    'host': '127.0.0.1', 
    'port': 3307,       
    'user': 'root',
    'password': 'admin123',
    'database': 'ecommercedb',
}

# --- PARÂMETROS DE GERAÇÃO ---
NUM_CLIENTS = 50
NUM_ORDERS = 130
NUM_STOCK_LOCATIONS = 3
NUM_SUPPLIERS = 10
NUM_SELLERS = 10

# Inicializa o Faker
fake = Faker('pt_BR') 

# --- FUNÇÕES DE INSERÇÃO ---

def generate_clients(cursor):
    """Gera 50 clientes (PF e PJ) e insere no DB."""
    print(f"Gerando {NUM_CLIENTS} clientes...")
    
    # Lista para evitar duplicação de CNPJ/CPF em um script de inserção
    documentos_usados = set() 

    for i in range(NUM_CLIENTS):
        is_pj = random.choice([True, False, False])
        
        # Gera documento único
        while True:
            doc = fake.cnpj() if is_pj else fake.cpf()
            if doc not in documentos_usados:
                documentos_usados.add(doc)
                break
        
        if is_pj:
            name = fake.company()
            client_type = 'PJ'
            first_name = name.split()[0]
            last_name = ' '.join(name.split()[1:])
        else:
            first_name = fake.first_name()
            last_name = fake.last_name()
            client_type = 'PF'

        email = fake.email()
        address = fake.address().replace('\n', ', ')
        phone = fake.phone_number()
        
        sql = """
            INSERT INTO clients (first_name, last_name, client_type, document_number, address, email, phone_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(sql, (first_name, last_name, client_type, doc, address, email, phone))
        except mysql.connector.Error as err:
             # Se o e-mail ou documento for duplicado por acaso (raro com Faker, mas possível), ignoramos
            if err.errno != 1062: # 1062 = Duplicate entry
                 print(f"Erro ao inserir cliente: {err}")


def generate_products(cursor):
    """Gera uma lista base de produtos para referências futuras."""
    print("Gerando produtos base...")
    products_data = [
        ('Notebook Pro X', 'Alto desempenho', 'Eletrônicos', 7500.00),
        ('Smartphone Z1', 'Câmera profissional', 'Eletrônicos', 4200.00),
        ('Cadeira Gamer Max', 'Ergonomia total', 'Mobiliário', 1500.00),
        ('Mesa Escritório Aço', 'Design moderno', 'Mobiliário', 850.00),
        ('Webcam Full HD', 'Vídeo conferência', 'Acessórios', 250.00),
        ('Headset Bluetooth', 'Áudio de alta fidelidade', 'Acessórios', 600.00),
    ]
    
    for name, desc, cat, price in products_data:
        sql = """
            INSERT INTO products (name, description, category, base_price)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (name, desc, cat, price))

def generate_suppliers_sellers_stock(cursor):
    """Gera fornecedores, vendedores e locais de estoque."""
    print(f"Gerando {NUM_SUPPLIERS} fornecedores, {NUM_SELLERS} vendedores e {NUM_STOCK_LOCATIONS} estoques...")
    
    for _ in range(NUM_SUPPLIERS):
        cursor.execute("INSERT INTO suppliers (name, cnpj, contact_email, phone) VALUES (%s, %s, %s, %s)", 
                       (fake.company(), fake.cnpj(), fake.company_email(), fake.phone_number()))

    for _ in range(NUM_SELLERS):
        cursor.execute("INSERT INTO third_party_sellers (name, cnpj, rating, contact_email, phone) VALUES (%s, %s, %s, %s, %s)", 
                       (fake.company(), fake.cnpj(), round(random.uniform(3.5, 5.0), 1), fake.company_email(), fake.phone_number()))

    for i in range(NUM_STOCK_LOCATIONS):
        cursor.execute("INSERT INTO stock_locations (location_name, address) VALUES (%s, %s)", 
                       (f"Armazém {i+1} - {fake.city()}", fake.address().replace('\n', ', ')))

def generate_orders(cursor, product_ids, client_ids):
    """Gera 130 pedidos e seus itens."""
    print(f"Gerando {NUM_ORDERS} pedidos com itens e entregas...")
    
    payment_methods = ['Credit Card (Final XXXX)', 'Pix', 'Boleto', 'Bank Transfer']
    statuses = ['Confirmed', 'In Transit', 'Delivered', 'Cancelled']
    
    for order_num in range(1, NUM_ORDERS + 1):
        client_id = random.choice(client_ids)
        shipping_cost = round(random.uniform(5.00, 50.00), 2)
        payment_method = random.choice(payment_methods)
        status = random.choice(statuses)
        order_date = fake.date_time_between(start_date=datetime(2024, 1, 1), end_date=datetime.now())
        
        # 1. Inserir Pedido (Total será atualizado)
        sql_order = """
            INSERT INTO orders (client_id, total_amount, payment_method_used, shipping_cost, order_status, order_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_order, (client_id, 0.00, payment_method, shipping_cost, status, order_date))
        order_id = cursor.lastrowid
        
        total_amount = 0
        num_items = random.randint(1, 4)
        selected_products = random.sample(product_ids, k=min(num_items, len(product_ids)))
        
        # 2. Inserir Itens do Pedido
        for product_id in selected_products:
            quantity = random.randint(1, 5)
            
            cursor.execute("SELECT base_price FROM products WHERE product_id = %s", (product_id,))
            base_price = cursor.fetchone()[0]
            
            # CORREÇÃO: Converte Decimal para float antes de multiplicar
            base_price_f = float(base_price) 
            unit_price = round(base_price_f * random.uniform(1.05, 1.20), 2)
            
            total_amount += unit_price * quantity
            
            sql_items = """
                INSERT INTO order_products (order_id, product_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_items, (order_id, product_id, quantity, unit_price))

        # 3. Atualizar o Total do Pedido
        total_amount += shipping_cost
        sql_update = "UPDATE orders SET total_amount = %s WHERE order_id = %s"
        cursor.execute(sql_update, (total_amount, order_id))

        # 4. Inserir Entrega 
        if status in ['Confirmed', 'In Transit', 'Delivered']:
            
            # --- CORREÇÃO CRÍTICA APLICADA AQUI: Mapeamento de Status ---
            delivery_status = status
            if delivery_status == 'Confirmed':
                # Mapeia o status do pedido 'Confirmed' para o status de entrega 'Preparation'
                delivery_status = 'Preparation'
            elif delivery_status == 'In Transit':
                 delivery_status = 'Shipped' # Mapeamento mais lógico
            
            # O status 'Delivered' já existe em ambos os ENUMs
            # ----------------------------------------------------------------
            
            delivery_address = fake.address().replace('\n', ', ')
            shipping_date = order_date + timedelta(days=random.randint(1, 3))
            estimated_delivery = shipping_date + timedelta(days=random.randint(5, 15))
            actual_delivery = estimated_delivery if delivery_status == 'Delivered' else None
            
            sql_delivery = """
                INSERT INTO delivery (order_id, tracking_code, delivery_status, shipping_date, estimated_delivery_date, actual_delivery_date, delivery_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            # Use a nova variável delivery_status corrigida!
            cursor.execute(sql_delivery, (order_id, fake.bothify(text='BR######??'), delivery_status, shipping_date, estimated_delivery, actual_delivery, delivery_address))

def populate_associations(cursor, product_ids, supplier_ids, seller_ids, stock_ids):
    """Cria associações N:M (Fornecimento, Venda Terceirizada, Estoque)."""
    print("Preenchendo associações N:M e estoque...")
    
    # 1. Product_Supplier 
    for product_id in product_ids:
        supplier_id = random.choice(supplier_ids)
        cursor.execute("SELECT base_price FROM products WHERE product_id = %s", (product_id,))
        base_price = cursor.fetchone()[0]
        
        # CORREÇÃO: Converte Decimal para float
        base_price_f = float(base_price)
        cost_price = round(base_price_f * random.uniform(0.60, 0.80), 2)
        
        cursor.execute("INSERT INTO product_supplier (product_id, supplier_id, cost_price) VALUES (%s, %s, %s)", 
                       (product_id, supplier_id, cost_price))

    # 2. Product_Seller 
    for product_id in random.sample(product_ids, k=len(product_ids)//2):
        seller_id = random.choice(seller_ids)
        cursor.execute("SELECT base_price FROM products WHERE product_id = %s", (product_id,))
        base_price = cursor.fetchone()[0]
        
        # CORREÇÃO: Converte Decimal para float
        base_price_f = float(base_price)
        selling_price = round(base_price_f * random.uniform(1.10, 1.30), 2)

        cursor.execute("INSERT INTO product_seller (product_id, seller_id, selling_price) VALUES (%s, %s, %s)", 
                       (product_id, seller_id, selling_price))

    # 3. Product_Stock 
    for product_id in product_ids:
        stock_id = random.choice(stock_ids)
        quantity = random.randint(10, 200)
        cursor.execute("INSERT INTO product_stock (product_id, stock_id, quantity) VALUES (%s, %s, %s)", 
                       (product_id, stock_id, quantity))


# --- FUNÇÃO PRINCIPAL ---

def main():
    try:
        # 1. Conexão
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Conexão estabelecida com sucesso.")
        
        # 2. Limpar todas as tabelas 
        print("Limpando tabelas existentes...")
        tables = ['delivery', 'order_products', 'orders', 'client_payment_methods', 'product_supplier', 'product_seller', 
                  'product_stock', 'products', 'suppliers', 'third_party_sellers', 'stock_locations', 'clients']
        
        # Desabilitar a verificação de chaves estrangeiras para permitir o TRUNCATE
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in tables:
             # TRUNCATE é melhor para resetar PKs, mas exige FK_CHECKS desabilitado
             cursor.execute(f"TRUNCATE TABLE {table}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
        
        # 3. Geração de Dados
        generate_clients(cursor)
        generate_products(cursor)
        generate_suppliers_sellers_stock(cursor)
        conn.commit()

        # 4. Obter IDs para Associações
        cursor.execute("SELECT client_id FROM clients")
        client_ids = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT product_id FROM products")
        product_ids = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT supplier_id FROM suppliers")
        supplier_ids = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT seller_id FROM third_party_sellers")
        seller_ids = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT stock_id FROM stock_locations")
        stock_ids = [row[0] for row in cursor.fetchall()]

        # 5. Popular Associações e Pedidos
        populate_associations(cursor, product_ids, supplier_ids, seller_ids, stock_ids)
        generate_orders(cursor, product_ids, client_ids)
        
        # 6. Finalizar
        conn.commit()
        print("\n--- GERAÇÃO DE DADOS CONCLUÍDA ---")
        print(f"Total de Clientes inseridos: {NUM_CLIENTS}")
        print(f"Total de Pedidos inseridos: {NUM_ORDERS}")
        
    except mysql.connector.Error as err:
        print(f"\nErro de Banco de Dados: {err}")
        print("\nVerifique se o seu container Docker está UP na porta 3307 e se a senha está correta.")
    except Exception as e:
        print(f"\nOcorreu um erro: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()