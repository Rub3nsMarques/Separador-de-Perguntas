import typer
import structlog
import logging
from question_extractor.infra.settings import settings
from question_extractor.infra.db import db

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = structlog.get_logger()

app = typer.Typer(
    name="extractor",
    help="DOCX Question Extractor Pipeline"
)

@app.command()
def schema_report() -> None:
    """
    Generates a report of the database schema to help identify relevant tables.
    """
    logger.info("Starting schema discovery...")
    try:
        tables = db.inspect_tables()
        print(f"Found {len(tables)} tables in public schema:")
        
        candidates = []
        for table in tables:
            print(f"- {table}")
            if any(k in table.lower() for k in ['quest', 'pergunta', 'file', 'arquivo', 'doc', 'blob']):
                candidates.append(table)
        
        print("\n--- Candidate Tables (Detailed) ---")
        for table in candidates:
            columns = db.inspect_columns(table)
            print(f"\nTable: {table}")
            for col in columns:
                print(f"  - {col['column_name']} ({col['data_type']})")
                
    except Exception as e:
        logger.error("Schema report failed", error=str(e))
        raise typer.Exit(code=1)

@app.command()
def scan_from_db(limit: int = 1) -> None:
    """
    Scans the first N DOCX files found in the DB.
    """
    from question_extractor.infra.files import file_manager
    from question_extractor.ooxml.reader import DocxReader
    from question_extractor.ooxml.scanner import DocxScanner
    
    logger.info(f"Scanning from DB with limit={limit}")
    
    if settings.SAFE_MODE:
        if limit > 1:
            logger.warning(f"SAFE_MODE is on. Forcing limit=1 (requested {limit}).")
            limit = 1
    
    query = "SELECT texto_id, texto_titulo FROM texto ORDER BY texto_id ASC LIMIT %s"
    textos = db.fetch_all(query, (limit,))
    
    for t in textos:
        titulo = t['texto_titulo']
        filename = f"{titulo}.docx"
        file_path = file_manager.resolve_path(filename)
        
        if not file_path.exists():
            logger.error(f"File missing: {file_path}")
            continue
            
        try:
            with DocxReader(file_path) as reader:
                scanner = DocxScanner(reader)
                stats = scanner.scan()
                print(f"\n--- Scan Report for {filename} ---")
                print(f"Questions: {stats['questions_detected']}, Alts: {stats['alternatives_detected']}")
        except Exception as e:
            logger.error(f"Failed to scan {filename}", error=str(e))

@app.command()
def extract_from_db(limit: int = 1) -> None:
    """
    Extracts from DB texts.
    """
    from question_extractor.infra.files import file_manager
    from question_extractor.domain.extraction import ExtractionService
    from question_extractor.domain.reporting import ReportGenerator
    
    if settings.SAFE_MODE:
        if limit > 1:
            logger.warning(f"SAFE_MODE is on. Forcing limit=1 (requested {limit}).")
            limit = 1

    query = "SELECT texto_id, texto_titulo FROM texto ORDER BY texto_id ASC LIMIT %s"
    textos = db.fetch_all(query, (limit,))
    
    for t in textos:
        titulo = t['texto_titulo']
        filename = f"{titulo}.docx"
        file_path = file_manager.resolve_path(filename)
        
        if not file_path.exists():
            logger.error(f"File missing: {file_path}")
            # In production, we might want to continue or log
            continue
            
        logger.info(f"Extracting {filename}...")
        service = ExtractionService(file_path)
        # We use a sanitized name or ID for the output folder
        safe_name = "".join(c for c in titulo if c.isalnum() or c in ('-', '_'))
        
        try:
            report_data = service.extract_all(safe_name)
            
            # Generate HTML Report
            generator = ReportGenerator()
            generator.generate_html(report_data)
            
        except Exception as e:
            logger.error(f"Failed extraction/reporting for {filename}", error=str(e))


@app.command()
def extract_single(doc_source_id: str) -> None:
    """
    Extracts a specific DOCX by ID (filename).
    """
    from question_extractor.infra.files import file_manager
    from question_extractor.domain.extraction import ExtractionService
    
    filename = f"{doc_source_id}.docx"
    file_path = file_manager.resolve_path(filename)
    
    if not file_path.exists():
        logger.error(f"File missing: {file_path}")
        return

    service = ExtractionService(file_path)
    service.extract_all(doc_source_id)


@app.command()
def inspect_table(table_name: str, limit: int = 5) -> None:
    """
    Dumps the first N rows of a table.
    """
    try:
        rows = db.fetch_all(f"SELECT * FROM {table_name} LIMIT %s", (limit,))
        print(f"--- Data from {table_name} (Limit {limit}) ---")
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {row}")
    except Exception as e:
        logger.error(f"Failed to inspect {table_name}", error=str(e))


@app.command()
def migrate() -> None:
    """
    Runs the database migrations.
    """
    from pathlib import Path
    logger.info("Running migrations...")
    try:
        # Resolve path relative to this file or package structure
        # We know it is in ../infra/migrations/001_init.sql relative to cli/main.py
        # Or easier: assume we are at package root.
        # Better: use __file__
        base_dir = Path(__file__).resolve().parent.parent 
        migration_file = base_dir / "infra" / "migrations" / "001_init.sql"
        
        if not migration_file.exists():
             raise FileNotFoundError(f"Migration file not found at {migration_file}")

        db.execute_script(str(migration_file))
        logger.info("Migration 001_init.sql executed successfully.")
    except Exception as e:
        logger.error("Migration failed", error=str(e))
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()

