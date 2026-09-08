-- Controle de Entrega de EPI — esquema do banco (SQLite)
PRAGMA foreign_keys = ON;

-- Configuração da empresa (linha única, id = 1)
CREATE TABLE IF NOT EXISTS empresa (
    id             INTEGER PRIMARY KEY CHECK (id = 1),
    nome           TEXT    NOT NULL DEFAULT '',
    cnpj           TEXT    NOT NULL DEFAULT '',
    logo           BLOB,
    logo_mime      TEXT,
    atualizado_em  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Assinaturas capturadas no canvas, guardadas como PNG (blob)
CREATE TABLE IF NOT EXISTS assinaturas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    imagem      BLOB NOT NULL,
    mime        TEXT NOT NULL DEFAULT 'image/png',
    criado_em   TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS funcionarios (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                    TEXT NOT NULL,
    registro                TEXT NOT NULL DEFAULT '',
    cargo                   TEXT NOT NULL DEFAULT '',
    setor                   TEXT NOT NULL DEFAULT '',
    ciente_data             TEXT,          -- data do "Ciente em ___/___/___"
    assinatura_admissao_id  INTEGER REFERENCES assinaturas(id) ON DELETE SET NULL,
    criado_em               TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Lista mestre de EPI / uniformes
CREATE TABLE IF NOT EXISTS epi_master (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL UNIQUE,
    ca          TEXT NOT NULL DEFAULT '',
    tem_tamanho INTEGER NOT NULL DEFAULT 0,   -- 1 = pede tamanho (P/M/G/GG/EXG ou numérico)
    ativo       INTEGER NOT NULL DEFAULT 1,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Ficha de entrega (um registro por entrega)
CREATE TABLE IF NOT EXISTS entregas (
    id                      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    funcionario_id          INTEGER NOT NULL REFERENCES funcionarios(id) ON DELETE CASCADE,
    data_inicio             TEXT,          -- data de início do preenchimento da ficha
    data_entrega            TEXT NOT NULL,
    assinatura_id           INTEGER REFERENCES assinaturas(id) ON DELETE SET NULL,
    data_devolucao          TEXT,
    assinatura_devolucao_id INTEGER REFERENCES assinaturas(id) ON DELETE SET NULL,
    observacoes             TEXT NOT NULL DEFAULT '',
    criado_em               TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS entrega_itens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entrega_id  INTEGER NOT NULL REFERENCES entregas(id) ON DELETE CASCADE,
    epi_id      INTEGER REFERENCES epi_master(id) ON DELETE SET NULL,
    nome        TEXT NOT NULL,             -- nome gravado na ficha (histórico não muda se a lista mestre mudar)
    ca          TEXT NOT NULL DEFAULT '',
    quantidade  REAL NOT NULL DEFAULT 1,
    tamanho     TEXT NOT NULL DEFAULT '',
    ordem       INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_entregas_funcionario ON entregas(funcionario_id, data_entrega);
CREATE INDEX IF NOT EXISTS idx_itens_entrega        ON entrega_itens(entrega_id, ordem);
