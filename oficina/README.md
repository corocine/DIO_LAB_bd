# Sistema de Controle e Gerenciamento de Oficina Mecânica (Projeto BD Relacional)

Este projeto foi desenvolvido como parte do desafio de modelagem e implementação de banco de dados, focado em criar e popular um esquema relacional para gerenciar as operações de uma oficina mecânica.

## ⚙️ Tecnologias Utilizadas

* **Banco de Dados:** MySQL 8.0
* **Contêiner:** Docker e Docker Compose (para ambiente isolado)
* **Linguagem de Ingestão:** Python (com a biblioteca Faker para dados realistas)
* **SQL:** DDL (Data Definition Language) e DML (Data Manipulation Language)

## 1. Descrição do Esquema Lógico

O modelo relacional foi desenhado para rastrear todo o fluxo de trabalho de uma Ordem de Serviço (OS), desde a entrada do veículo até o cálculo do custo final.

### Entidades e Relacionamentos Chave:

| Tabela                      | Chave Primária (PK) | Chaves Estrangeiras (FK)   | Descrição                                                   |
| :-------------------------- | :------------------- | :------------------------- | :------------------------------------------------------------ |
| `cliente`                 | `cliente_id`       | N/A                        | Informações do proprietário.                               |
| `veiculo`                 | `veiculo_id`       | `cliente_id`             | Relacionamento**1:N** com `cliente`.                  |
| `mecanico`                | `mecanico_id`      | N/A                        | Cadastro dos colaboradores.                                   |
| `peca`                    | `peca_id`          | N/A                        | Catálogo de peças.                                          |
| `servico_referencia`      | `servico_id`       | N/A                        | Catálogo de serviços/mão de obra.                          |
| **`ordem_servico`** | `os_id`            | `veiculo_id`             | Tabela central (Relacionamento**1:N** com `veiculo`). |
| `os_equipe`               | `os_equipe_id`     | `os_id`, `mecanico_id` | Detalha os mecânicos alocados a uma OS (**N:M**).      |
| `os_servico`              | `os_servico_id`    | `os_id`, `servico_id`  | Detalha os serviços aplicados a uma OS (**N:M**).      |
| `os_peca`                 | `os_peca_id`       | `os_id`, `peca_id`     | Detalha as peças utilizadas em uma OS (**N:M**).       |

### Regra de Negócio Implementada na Ingestão:

Para garantir a integridade dos dados, o script de ingestão Python força que toda `ordem_servico` com `status` **'Concluída'** ou **'Em Execução'** tenha **pelo menos um serviço OU uma peça** associada, prevenindo `NULL`s em cálculos de custo.

## 2. Configuração e Execução do Ambiente

O banco de dados é inicializado via Docker e populado via script Python.

### Requisitos:

* Docker e Docker Compose instalados.
* Python 3.x e as bibliotecas `Faker` e `mysql-connector-python`.

### Passos de Inicialização:

1. **Construir e Subir o Container:**

   ```bash
   docker-compose up -d
   ```

   *Obs: As tabelas devem ser criadas via DBeaver ou script, se não estiverem no volume inicial do Docker.*
2. **Popular o Banco de Dados (Ingestão de 3x Mais Dados):**

   ```bash
   python generate_data.py
   ```

   Este script se conecta ao MySQL na porta `3308`, limpa as tabelas (respeitando as FKs) e insere as 99 Ordens de Serviço com o `valor_total` pré-calculado. Utilizei a IA como apoio para realizar esse script

## 3. Consultas SQL (Queries)

As consultas abaixo demonstram a capacidade analítica do esquema, cobrindo todos os requisitos do desafio (SELECT, WHERE, ORDER BY, Atributo Derivado, HAVING, e JOINs).

### 3.1. Recuperações Simples e Filtros (`SELECT` e `WHERE`)

Consultas para recuperar dados de forma direta ou com filtros básicos:

```sql
SELECT * FROM ordem_servico;

-- Filtro e seleção de colunas específicas
SELECT numero_os, status, valor_total FROM ordem_servico;
SELECT numero_os, status, valor_total FROM ordem_servico WHERE valor_total > 1000;
SELECT numero_os, status, valor_total FROM ordem_servico WHERE valor_total < 1000;
SELECT numero_os, status, valor_total FROM ordem_servico WHERE status = 'Concluída';

SELECT
    COUNT(*) AS OS_total_nao_concluida
FROM
    ordem_servico
WHERE  status != 'Concluída';
```

### 3.2. Atributos Derivados e Ordenação (`DATEDIFF`, `ORDER BY`)

**Pergunta:** Qual é o tempo de espera estimado para as OS concluídas?

```sql
SELECT
    numero_os,
    status,
    data_emissao,
    data_conclusao_prevista,
    DATEDIFF(data_conclusao_prevista, data_emissao) AS tempo_espera_dias
FROM
    ordem_servico
WHERE
    data_conclusao_prevista IS NOT NULL
    AND status = 'Concluída'
ORDER BY
    tempo_espera_dias DESC;
```

### 3.3. Agregação e Análise por Grupo (`GROUP BY`)

**Pergunta:** Qual a média de tempo de serviço e o total de OS para cada status?

```sql

SELECT
    status,
    COUNT(numero_os) AS total_os,
    AVG(DATEDIFF(data_conclusao_prevista, data_emissao)) AS media_tempo_espera_dias 
FROM
    ordem_servico
GROUP BY 
    status;
```

### 3.4. Junções Complexas e Agregação (`JOIN`, `SUM`, `ORDER BY`)

**Pergunta:** Qual é a peça mais vendida em quantidade total?

```sql
SELECT
    P.nome AS nome_peca,
    SUM(OP.quantidade) AS quantidade_total_utilizada
FROM
    peca AS P
INNER JOIN
    os_peca AS OP ON P.peca_id = OP.peca_id
GROUP BY
    P.peca_id, P.nome
ORDER BY
    quantidade_total_utilizada DESC;
```
