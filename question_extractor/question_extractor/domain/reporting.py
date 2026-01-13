import logging
import jinja2
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from question_extractor.infra.files import file_manager

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(Path(__file__).parent.parent / "templates")),
            autoescape=True
        )
    
    def generate_html(self, report_data: Dict[str, Any], output_filename: str = "report.html") -> Path:
        """
        Generates report.html in the doc output directory.
        """
        template = self.env.get_template("report.html.j2")
        
        # Enrich data
        report_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_data["throughput"] = "N/A" # Calculate if duration is available
        
        # Convert absolute paths to relative for the report links
        # The report is inside "Questoes e respostas separadas/<doc_id>/"
        # The files are inside "Questoes e respostas separadas/<doc_id>/<q_id>/"
        # So links should be "./<q_id>/pergunta.docx"
        
        doc_id = report_data["doc_source_id"]
        # Find the root output dir for this doc
        # We need a way to get the root dir for this DOC from file_manager or derive it.
        # Ideally, we pass the output_dir to this function.
        
        # Hacky reconstruction of base path to calculate relative
        
        questions_formatted = []
        for q in report_data["questions"]:
            q_clean = q.copy()
            new_files = {}
            for k, abs_path in q["files"].items():
                # Make relative to report location
                # Expected report location: OUTPUT / doc_id / report.html
                # File location: OUTPUT / doc_id / q_id / file.docx
                # Relative: ./q_id/file.docx
                
                p = Path(abs_path)
                q_id_dir = p.parent.name # q_001
                fname = p.name
                new_files[k] = f"./{q_id_dir}/{fname}"
            
            q_clean["files"] = new_files
            questions_formatted.append(q_clean)
            
        report_data["questions"] = questions_formatted
        
        rendered = template.render(**report_data)
        
        # Save
        # Assume output is at OUTPUT_BASE / doc_id
        # We need to construct this path manually or use file_manager
        base = file_manager.output_path / doc_id
        base.mkdir(parents=True, exist_ok=True)
        
        out_path = base / output_filename
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(rendered)
            
        logger.info(f"Report generated: {out_path}")
        return out_path
