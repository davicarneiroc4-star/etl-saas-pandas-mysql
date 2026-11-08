-- Schema do banco saas (8 tabelas)
CREATE DATABASE IF NOT EXISTS saas;
USE saas;

CREATE TABLE clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nome_empresa VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    segmento VARCHAR(50),
    tamanho_empresa VARCHAR(20),
    estado VARCHAR(2),
    data_cadastro DATE NOT NULL,
    status VARCHAR(20) NOT NULL
);

CREATE TABLE planos (
    id_plano INT AUTO_INCREMENT PRIMARY KEY,
    nome_plano VARCHAR(50) NOT NULL,
    periodicidade VARCHAR(10) NOT NULL,
    preco DECIMAL(10,2) NOT NULL,
    limite_usuarios INT
);

CREATE TABLE assinaturas (
    id_assinatura INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_plano INT NOT NULL,
    valor_assinatura DECIMAL(10,2) NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE,
    status VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_plano) REFERENCES planos(id_plano)
);

CREATE TABLE historico_planos (
    id_historico INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_plano_anterior INT NOT NULL,
    id_plano_novo INT NOT NULL,
    data_alteracao DATE NOT NULL,
    tipo_alteracao VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_plano_anterior) REFERENCES planos(id_plano),
    FOREIGN KEY (id_plano_novo) REFERENCES planos(id_plano)
);

CREATE TABLE faturas (
    id_fatura INT AUTO_INCREMENT PRIMARY KEY,
    id_assinatura INT NOT NULL,
    valor_fatura DECIMAL(10,2) NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    status_pagamento VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_assinatura) REFERENCES assinaturas(id_assinatura)
);

CREATE TABLE pagamentos (
    id_pagamento INT AUTO_INCREMENT PRIMARY KEY,
    id_fatura INT NOT NULL,
    metodo_pagamento VARCHAR(20) NOT NULL,
    data_tentativa DATE NOT NULL,
    status_tentativa VARCHAR(20) NOT NULL,
    motivo_falha VARCHAR(100),
    FOREIGN KEY (id_fatura) REFERENCES faturas(id_fatura)
);

CREATE TABLE cancelamentos (
    id_cancelamento INT AUTO_INCREMENT PRIMARY KEY,
    id_assinatura INT NOT NULL,
    data_cancelamento DATE NOT NULL,
    motivo_cancelamento VARCHAR(100),
    tipo_cancelamento VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_assinatura) REFERENCES assinaturas(id_assinatura)
);

CREATE TABLE eventos_uso (
    id_evento INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    tipo_evento VARCHAR(50) NOT NULL,
    data_evento DATETIME NOT NULL,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
);