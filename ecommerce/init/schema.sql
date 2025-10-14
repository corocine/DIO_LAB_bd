
-- I. Módulo de Clientes e Pagamento
CREATE TABLE clients (
    client_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    client_type ENUM('PF', 'PJ') NOT NULL, 
    document_number VARCHAR(18) UNIQUE NOT NULL, 
    address VARCHAR(255),
    email VARCHAR(150) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_document_type CHECK (
        (client_type = 'PF' AND LENGTH(document_number) BETWEEN 11 AND 14) OR 
        (client_type = 'PJ' AND LENGTH(document_number) BETWEEN 14 AND 18)    
    )
);

CREATE TABLE client_payment_methods (
    payment_method_id INT PRIMARY KEY AUTO_INCREMENT,
    client_id INT NOT NULL,
    payment_type ENUM('Credit Card', 'Debit Card', 'Bank Transfer', 'Boleto', 'Pix') NOT NULL,
    details_encrypted VARCHAR(255) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);

-- II. Módulo de Produtos e Cadeia de Suprimentos
CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    base_price DECIMAL(10, 2) NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE suppliers (
    supplier_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    cnpj VARCHAR(18) UNIQUE NOT NULL,
    contact_email VARCHAR(150),
    phone VARCHAR(20)
);

CREATE TABLE third_party_sellers (
    seller_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    cnpj VARCHAR(18) UNIQUE NOT NULL,
    rating DECIMAL(2, 1) DEFAULT 5.0,
    contact_email VARCHAR(150),
    phone VARCHAR(20)
);

CREATE TABLE stock_locations (
    stock_id INT PRIMARY KEY AUTO_INCREMENT,
    location_name VARCHAR(100) UNIQUE NOT NULL,
    address VARCHAR(255) NOT NULL
);

-- Tabelas de Associação N:M
CREATE TABLE product_supplier (
    product_id INT NOT NULL,
    supplier_id INT NOT NULL,
    cost_price DECIMAL(10, 2),
    PRIMARY KEY (product_id, supplier_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE CASCADE
);

CREATE TABLE product_seller (
    product_id INT NOT NULL,
    seller_id INT NOT NULL,
    selling_price DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (product_id, seller_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES third_party_sellers(seller_id) ON DELETE CASCADE
);

CREATE TABLE product_stock (
    product_id INT NOT NULL,
    stock_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    PRIMARY KEY (product_id, stock_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (stock_id) REFERENCES stock_locations(stock_id) ON DELETE CASCADE
);


-- III. Módulo de Vendas e Logística
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    client_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    order_status ENUM('Processing', 'Confirmed', 'In Transit', 'Delivered', 'Cancelled') NOT NULL DEFAULT 'Processing',
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_method_used VARCHAR(50) NOT NULL,
    shipping_cost DECIMAL(10, 2) DEFAULT 0.00,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
);

CREATE TABLE delivery (
    delivery_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT UNIQUE NOT NULL, 
    tracking_code VARCHAR(100) UNIQUE NOT NULL,
    delivery_status ENUM('Preparation', 'Shipped', 'Out for Delivery', 'Delivered', 'Failed') NOT NULL DEFAULT 'Preparation',
    shipping_date DATE,
    estimated_delivery_date DATE,
    actual_delivery_date DATE,
    delivery_address VARCHAR(255) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);

CREATE TABLE order_products (
    order_product_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE RESTRICT,
    UNIQUE KEY (order_id, product_id)
);