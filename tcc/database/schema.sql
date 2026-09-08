-- JOAO CARMELO - TCC
-- Sistema de Vistoria, Garantias e Manutencao de Residencias
-- Esquema SQLite. Escrito em SQL portavel para permitir migracao futura
-- para PostgreSQL (sem tipos exclusivos do SQLite, datas em TEXT ISO-8601).

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario       TEXT NOT NULL UNIQUE,
    senha_hash    TEXT NOT NULL,
    salt          TEXT NOT NULL,
    nome          TEXT,
    perfil        TEXT NOT NULL DEFAULT 'admin',
    criado_em     TEXT NOT NULL
);

-- ------------------------------------------------------------- residencias
CREATE TABLE IF NOT EXISTS residencias (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo                TEXT UNIQUE,            -- RESIDENCIA 001
    nome                  TEXT NOT NULL,
    proprietario          TEXT,
    endereco              TEXT,
    bairro                TEXT,
    cidade                TEXT,
    uf                    TEXT,
    cep                   TEXT,
    telefone              TEXT,
    email                 TEXT,
    area_construida       REAL,
    pavimentos            INTEGER,
    tipo_construcao       TEXT,
    sistema_construtivo   TEXT,
    construtora           TEXT,
    responsavel_tecnico   TEXT,
    data_habite_se        TEXT,                   -- ISO 'YYYY-MM-DD'
    data_protocolo        TEXT,
    data_entrega          TEXT,
    manual_proprietario   INTEGER DEFAULT 0,      -- 0/1
    plano_manutencao      INTEGER DEFAULT 0,
    houve_reforma         INTEGER DEFAULT 0,
    observacoes           TEXT,
    criado_em             TEXT NOT NULL,
    atualizado_em         TEXT
);
CREATE INDEX IF NOT EXISTS ix_residencias_nome ON residencias (nome);

-- ---------------------------------------------------------------- sistemas
-- Sistemas construtivos usados em toda a plataforma (estrutura, hidraulica...).
CREATE TABLE IF NOT EXISTS sistemas (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo   TEXT NOT NULL UNIQUE,
    nome     TEXT NOT NULL,
    ordem    INTEGER DEFAULT 0
);

-- ---------------------------------------------------------------- ambientes
CREATE TABLE IF NOT EXISTS ambientes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    residencia_id  INTEGER NOT NULL REFERENCES residencias (id) ON DELETE CASCADE,
    nome           TEXT NOT NULL,
    localizacao    TEXT,
    piso           TEXT,
    paredes        TEXT,
    teto           TEXT,
    esquadrias     TEXT,
    instalacoes    TEXT,
    observacoes    TEXT,
    ordem          INTEGER DEFAULT 0,
    criado_em      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ambientes_residencia ON ambientes (residencia_id);

-- --------------------------------------------------------------- vistorias
CREATE TABLE IF NOT EXISTS vistorias (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    residencia_id  INTEGER NOT NULL REFERENCES residencias (id) ON DELETE CASCADE,
    data_vistoria  TEXT NOT NULL,
    responsavel    TEXT,
    tipo           TEXT,                          -- inicial / reinspecao
    condicoes      TEXT,                          -- clima, acesso, etc.
    observacoes    TEXT,
    origem         TEXT DEFAULT 'plataforma',     -- 'plataforma' ou 'app-campo'
    criado_em      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_vistorias_residencia ON vistorias (residencia_id);

-- ---------------------------------------------------------- itens_catalogo
-- Catalogo de itens verificaveis (vem do Excel): sistema > elemento > item.
CREATE TABLE IF NOT EXISTS itens_catalogo (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sistema_id   INTEGER REFERENCES sistemas (id),
    elemento     TEXT,
    item         TEXT NOT NULL,
    descricao    TEXT,
    fonte        TEXT,                            -- de onde veio (aba do Excel/NBR)
    ativo        INTEGER DEFAULT 1
);

-- ------------------------------------------------------------- ocorrencias
-- Manifestacoes patologicas.
CREATE TABLE IF NOT EXISTS ocorrencias (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo            TEXT UNIQUE,                -- OCO-0001
    residencia_id     INTEGER NOT NULL REFERENCES residencias (id) ON DELETE CASCADE,
    ambiente_id       INTEGER REFERENCES ambientes (id) ON DELETE SET NULL,
    vistoria_id       INTEGER REFERENCES vistorias (id) ON DELETE SET NULL,
    sistema_id        INTEGER REFERENCES sistemas (id),
    item_catalogo_id  INTEGER REFERENCES itens_catalogo (id),
    elemento          TEXT,
    resultado         TEXT NOT NULL DEFAULT 'Nao Conforme',
        -- Conforme / Nao Conforme / Nao Aplicavel / Nao Verificado
    data_constatacao  TEXT,
    tipo_manifestacao TEXT,
    descricao         TEXT,
    localizacao       TEXT,
    possiveis_causas  TEXT,                       -- texto livre do engenheiro
    origem_anomalia   TEXT,                       -- JSON: lista de origens (multipla)
    extensao          TEXT,
    intensidade       TEXT,
    medicao           TEXT,
    abertura_mm       REAL,                       -- fissura/trinca, quando aplicavel
    observacoes       TEXT,
    uuid_campo        TEXT UNIQUE,                -- id gerado no app de campo (import idempotente)
    criado_em         TEXT NOT NULL,
    atualizado_em     TEXT
);
CREATE INDEX IF NOT EXISTS ix_ocorrencias_residencia ON ocorrencias (residencia_id);
CREATE INDEX IF NOT EXISTS ix_ocorrencias_sistema    ON ocorrencias (sistema_id);

-- ------------------------------------------------------ classificacoes_gut
CREATE TABLE IF NOT EXISTS classificacoes_gut (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ocorrencia_id  INTEGER NOT NULL REFERENCES ocorrencias (id) ON DELETE CASCADE,
    gravidade      INTEGER NOT NULL,              -- 10 8 6 3 1
    urgencia       INTEGER NOT NULL,
    tendencia      INTEGER NOT NULL,
    gut            INTEGER NOT NULL,              -- G x U x T (gravado para consulta)
    prioridade     INTEGER NOT NULL,              -- 1 2 3
    justificativa  TEXT,
    confirmada_por TEXT,                          -- o engenheiro confirma/altera
    criado_em      TEXT NOT NULL,
    atualizado_em  TEXT
);
CREATE INDEX IF NOT EXISTS ix_gut_ocorrencia ON classificacoes_gut (ocorrencia_id);

-- ------------------------------------------------------------------- fotos
-- O arquivo fica em disco (uploads/fotos/<residencia>/); o banco guarda o caminho.
CREATE TABLE IF NOT EXISTS fotos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo         TEXT UNIQUE,                   -- FOTO-001
    residencia_id  INTEGER NOT NULL REFERENCES residencias (id) ON DELETE CASCADE,
    ambiente_id    INTEGER REFERENCES ambientes (id) ON DELETE SET NULL,
    ocorrencia_id  INTEGER REFERENCES ocorrencias (id) ON DELETE SET NULL,
    vistoria_id    INTEGER REFERENCES vistorias (id) ON DELETE SET NULL,
    sistema_id     INTEGER REFERENCES sistemas (id),
    arquivo        TEXT NOT NULL,                 -- caminho relativo
    legenda        TEXT,
    momento        TEXT DEFAULT 'antes',          -- antes / depois
    data_foto      TEXT,
    sha256         TEXT,                          -- deduplicacao na importacao
    uuid_campo     TEXT UNIQUE,
    criado_em      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_fotos_residencia ON fotos (residencia_id);
CREATE INDEX IF NOT EXISTS ix_fotos_ocorrencia ON fotos (ocorrencia_id);

-- -------------------------------------------------------- regras_garantia
-- Catalogo de prazos (NBR 17170 / Excel). Nao e a garantia de uma casa:
-- e a REGRA a partir da qual a garantia de cada casa e calculada.
CREATE TABLE IF NOT EXISTS regras_garantia (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sistema_id    INTEGER REFERENCES sistemas (id),
    componente    TEXT NOT NULL,
    tipo_falha    TEXT,
    prazo_anos    REAL,                           -- NULL = sem prazo tipificado
    fonte         TEXT,                           -- 'NBR 17170:2022', 'Excel', 'Contrato'
    conferido     INTEGER NOT NULL DEFAULT 0,     -- 0 ate o engenheiro conferir na norma
    observacao    TEXT
);

-- --------------------------------------------------------------- garantias
-- Garantia calculada para uma residencia (regra + data-base).
CREATE TABLE IF NOT EXISTS garantias (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    residencia_id   INTEGER NOT NULL REFERENCES residencias (id) ON DELETE CASCADE,
    regra_id        INTEGER REFERENCES regras_garantia (id),
    sistema_id      INTEGER REFERENCES sistemas (id),
    componente      TEXT NOT NULL,
    tipo_falha      TEXT,
    prazo_anos      REAL,
    data_inicial    TEXT,                         -- normalmente o Habite-se
    data_vencimento TEXT,                         -- calculada
    situacao        TEXT,                         -- calculada (cache)
    observacao      TEXT,
    criado_em       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_garantias_residencia ON garantias (residencia_id);

-- -------------------------------------------------------------- manutencoes
CREATE TABLE IF NOT EXISTS manutencoes (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    residencia_id     INTEGER NOT NULL REFERENCES residencias (id) ON DELETE CASCADE,
    sistema_id        INTEGER REFERENCES sistemas (id),
    atividade         TEXT NOT NULL,
    periodicidade_meses INTEGER,
    ultima_manutencao TEXT,
    proxima_manutencao TEXT,
    responsavel       TEXT,
    comprovante       TEXT,                       -- caminho de arquivo
    situacao          TEXT,                       -- realizada/programada/proxima/atrasada
    observacao        TEXT,
    criado_em         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_manutencoes_residencia ON manutencoes (residencia_id);

-- --------------------------------------------------------------- protocolos
CREATE TABLE IF NOT EXISTS protocolos (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    residencia_id      INTEGER NOT NULL REFERENCES residencias (id) ON DELETE CASCADE,
    ocorrencia_id      INTEGER REFERENCES ocorrencias (id) ON DELETE SET NULL,
    construtora        TEXT,
    data_contato       TEXT,
    numero_protocolo   TEXT,
    responsavel_atend  TEXT,
    situacao           TEXT,                      -- nao acionada ... encerrado
    resposta           TEXT,
    data_prevista_visita TEXT,
    servico_executado  TEXT,
    resultado          TEXT,
    criado_em          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_protocolos_residencia ON protocolos (residencia_id);

-- --------------------------------------------------------------- documentos
CREATE TABLE IF NOT EXISTS documentos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    residencia_id  INTEGER NOT NULL REFERENCES residencias (id) ON DELETE CASCADE,
    protocolo_id   INTEGER REFERENCES protocolos (id) ON DELETE SET NULL,
    categoria      TEXT,                          -- Habite-se, ART/RRT, Manual...
    titulo         TEXT NOT NULL,
    arquivo        TEXT NOT NULL,
    data_documento TEXT,
    observacao     TEXT,
    criado_em      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_documentos_residencia ON documentos (residencia_id);

-- ---------------------------------------------------------------- historico
-- Prontuario digital da residencia + trilha de alteracoes.
CREATE TABLE IF NOT EXISTS historico (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    residencia_id  INTEGER NOT NULL REFERENCES residencias (id) ON DELETE CASCADE,
    data_evento    TEXT NOT NULL,
    tipo           TEXT NOT NULL,                 -- habite-se, vistoria, ocorrencia...
    titulo         TEXT NOT NULL,
    detalhe        TEXT,
    entidade       TEXT,                          -- tabela de origem
    entidade_id    INTEGER,
    usuario        TEXT,
    criado_em      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_historico_residencia ON historico (residencia_id, data_evento);
