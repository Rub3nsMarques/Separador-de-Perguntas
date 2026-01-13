# Question Extractor Pipeline

Pipeline robusto para extração de questões e alternativas de arquivos DOCX (OOXML), com preservação de formatação, integração PostgreSQL e relatórios HTML interativos.

## Setup

1. **Requisitos**: Python 3.11+, PostgreSQL.
2. **Instalação**:
   ```bash
   pip install -e .
   ```
3. **Configuração**:
   Crie um arquivo `.env` na raiz (baseado no exemplo abaixo):

   ```env
   PG_HOST=localhost
   PG_PORT=5432
   PG_DB=mydatabase
   PG_USER=myuser
   PG_PASSWORD=mypassword

   FILES_BASE_PATH=/path/to/source/files
   OUTPUT_BASE_PATH=/path/to/output

   SAFE_MODE=true
   DOC_SOURCE_TABLE=texto
   DOC_ID_COLUMN=texto_id
   # DOC_PATH_COLUMN=   <-- Preencher após rodar schema-report
   DOC_TITLE_COLUMN=texto_titulo
   ```

## Uso

### 1. Migrations

Crie as tabelas necessárias no banco:

```bash
python -m question_extractor.cli.main migrate
```

### 2. Descoberta de Esquema

Descubra quais tabelas e colunas contêm os arquivos DOCX:

```bash
python -m question_extractor.cli.main schema-report
```

### 3. Extração (Modo Seguro)

Rode a extração para o primeiro documento encontrado (seguro para testes):

```bash
python -m question_extractor.cli.main extract-from-db --limit 1
```

O sistema irá:

1. Buscar o documento no banco.
2. Resolver o caminho do arquivo (absoluto, relativo ou fallback pelo título).
3. Segmentar questões e alternativas preservando tabelas e estilos.
4. Calcular confiança da extração.
5. Persistir metadados no Postgres.
6. Gerar `report.html`.

## Funcionalidades

- **Preservação OOXML**: Mantém tabelas (`w:tbl`), estilos e imagens.
- **Confiança**: Score baseada em heurísticas (número de alternativas, marcadores).
- **Relatório**: HTML com filtros interativos (Sucesso, Revisão, Erro).
- **Segurança**: `SAFE_MODE` impede processamento em massa acidental.
