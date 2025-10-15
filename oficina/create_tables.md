# Querys utilizadas para construção do banco de dados

Optei por realizar as querys diretamente na IDE `dbeaver`

## 1. cliente

Armazena informações sobre os clientes da oficina.

**SQL**

```sql
CREATE TABLE cliente (
    cliente_id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    telefone VARCHAR(20),
    endereco VARCHAR(255)
);
```

---

## 2. veiculo

Armazena informações sobre os veículos cadastrados e os associa aos seus respectivos clientes.

**SQL**

```sql
CREATE TABLE veiculo (
    veiculo_id INT AUTO_INCREMENT PRIMARY KEY,
    placa VARCHAR(15) UNIQUE NOT NULL,
    marca VARCHAR(50),
    modelo VARCHAR(50),
    ano VARCHAR(4),
    cliente_id INT NOT NULL,
    CONSTRAINT fk_veiculo_cliente
        FOREIGN KEY (cliente_id) REFERENCES cliente(cliente_id)
        ON DELETE RESTRICT
);
```

---

## 3. mecanico

Armazena informações sobre os mecânicos da equipe.

**SQL**

```sql
CREATE TABLE mecanico (
    mecanico_id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(10),
    nome VARCHAR(255),
    endereco VARCHAR(255),
    especialidade VARCHAR(100)
);
```

---

## 4. peca

Catálogo de peças utilizadas nos serviços.

**SQL**

```sql
CREATE TABLE peca (
    peca_id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255),
    descricao VARCHAR(255),
    valor_unitario FLOAT(10,2)
);
```

---

## 5. servico_referencia

Catálogo de serviços padronizados e seus valores de mão de obra.

**SQL**

```sql
CREATE TABLE servico_referencia (
    servico_id INT AUTO_INCREMENT PRIMARY KEY,
    descricao VARCHAR(255),
    valor_mao_de_obra FLOAT(10,2)
);
```

---

## 6. ordem_servico

Tabela principal para gerenciar cada Ordem de Serviço (OS).

**SQL**

```sql
CREATE TABLE ordem_servico (
    os_id INT AUTO_INCREMENT PRIMARY KEY,
    numero_os VARCHAR(20) UNIQUE NOT NULL,
    data_emissao DATETIME NOT NULL,
    data_conclusao_prevista DATETIME,
    status VARCHAR(30),
    valor_total FLOAT(10,2),
    aprovacao_cliente BOOLEAN,
    veiculo_id INT NOT NULL,
    CONSTRAINT fk_os_veiculo
        FOREIGN KEY (veiculo_id) REFERENCES veiculo(veiculo_id)
);
```

---

## 7. os_servico

Tabela que detalha quais serviços foram realizados em cada Ordem de Serviço (relacionamento N:N entre OS e Serviço).

**SQL**

```sql
CREATE TABLE os_servico (
    os_servico_id INT AUTO_INCREMENT PRIMARY KEY,
    os_id INT NOT NULL,
    servico_id INT NOT NULL,
    valor_servico FLOAT(10,2),
    data_inicio DATETIME,
    data_fim DATETIME,
    CONSTRAINT fk_os_servico_os
        FOREIGN KEY (os_id) REFERENCES ordem_servico(os_id),
    CONSTRAINT fk_os_servico_ref
        FOREIGN KEY (servico_id) REFERENCES servico_referencia(servico_id)
);
```

---

## 8. os_peca

Tabela que detalha quais peças foram utilizadas em cada Ordem de Serviço (relacionamento N:N entre OS e Peça).

**SQL**

```sql
CREATE TABLE os_peca (
    os_peca_id INT AUTO_INCREMENT PRIMARY KEY,
    os_id INT NOT NULL,
    peca_id INT NOT NULL,
    quantidade INT(10),
    valor_unitario_peca FLOAT(10,2),
    CONSTRAINT fk_os_peca_os
        FOREIGN KEY (os_id) REFERENCES ordem_servico(os_id),
    CONSTRAINT fk_os_peca_peca
        FOREIGN KEY (peca_id) REFERENCES peca(peca_id)
);
```

---

## 9. os_equipe

Tabela que associa os mecânicos à uma Ordem de Serviço (relacionamento N:N entre OS e Mecânico).

**SQL**

```sql
CREATE TABLE os_equipe (
    os_equipe_id INT AUTO_INCREMENT PRIMARY KEY,
    os_id INT NOT NULL,
    mecanico_id INT NOT NULL,
    papel_na_equipe VARCHAR(30),
    CONSTRAINT fk_os_equipe_os
        FOREIGN KEY (os_id) REFERENCES ordem_servico(os_id),
    CONSTRAINT fk_os_equipe_mecanico
        FOREIGN KEY (mecanico_id) REFERENCES mecanico(mecanico_id)
);
```
