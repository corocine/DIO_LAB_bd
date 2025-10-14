-- Quantos pedidos foram feitos por cada cliente?
SELECT
    c.client_id,
    c.first_name,
    COUNT(o.order_id) AS 'Total de Pedidos'
FROM
    orders o
INNER JOIN
    clients c ON o.client_id = c.client_id
GROUP BY
    c.client_id, c.first_name
ORDER BY
    3 DESC;


-- Algum vendedor também é fornecedor?
SELECT
    s.name AS nome_como_fornecedor,
    tps.name AS nome_como_vendedor,
    s.cnpj
FROM
    suppliers s
INNER JOIN
    third_party_sellers tps ON s.cnpj = tps.cnpj;


-- Relação de produtos, fornecedores e estoques.
SELECT
    p.name AS product_name,
    s.name AS supplier_name,
    sl.location_name AS stock_location,
    ps.quantity AS available_quantity
FROM
    products p
INNER JOIN
    product_supplier psup ON p.product_id = psup.product_id
INNER JOIN
    suppliers s ON psup.supplier_id = s.supplier_id
INNER JOIN
    product_stock ps ON p.product_id = ps.product_id
INNER JOIN
    stock_locations sl ON ps.stock_id = sl.stock_id
ORDER BY
    product_name, stock_location;

-- Relação de nomes dos fornecedores e nomes dos produtos;
SELECT
    s.name AS supplier_name,
    p.name AS product_name,  
    psup.cost_price          
FROM
    suppliers s
INNER JOIN
    product_supplier psup ON s.supplier_id = psup.supplier_id
INNER JOIN
    products p ON psup.product_id = p.product_id
ORDER BY
    supplier_name, product_name;

 -- Valor total que o vendedor movimentou
SELECT
    tps.name AS seller_name,
    SUM(o.total_amount) AS total_valor_vendido,
    COUNT(o.order_id) AS total_pedidos_vendidos,
    SUM(CASE WHEN d.delivery_status = 'Delivered' THEN 1 ELSE 0 END) AS total_entregues
FROM
    third_party_sellers tps
INNER JOIN
    product_seller pseller ON tps.seller_id = pseller.seller_id
INNER JOIN
    order_products op ON pseller.product_id = op.product_id
INNER JOIN
    orders o ON op.order_id = o.order_id
INNER JOIN
    delivery d ON o.order_id = d.order_id
GROUP BY
    tps.seller_id, tps.name
ORDER BY
    total_valor_vendido DESC;