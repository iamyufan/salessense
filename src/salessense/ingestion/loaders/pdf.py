"""Load PDF playbooks and markdown battlecards."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RawDocument:
    text: str
    source_id: str
    doc_type: str
    metadata: dict


def load_pdfs(data_dir: str | Path = "data/raw/playbooks") -> list[RawDocument]:
    """Extract text from PDF playbooks (MEDDIC, Challenger Sale, etc.)."""
    from pypdf import PdfReader

    data_path = Path(data_dir)
    docs: list[RawDocument] = []
    for pdf_path in sorted(data_path.glob("*.pdf")):
        reader = PdfReader(str(pdf_path))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            continue
        docs.append(
            RawDocument(
                text=text,
                source_id=pdf_path.stem,
                doc_type="playbook",
                metadata={"filename": pdf_path.name},
            )
        )
    return docs


def load_battlecards(data_dir: str | Path = "data/raw/battlecards") -> list[RawDocument]:
    """Load markdown battlecard files."""
    data_path = Path(data_dir)
    docs: list[RawDocument] = []
    for md_path in sorted(data_path.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        if not text.strip():
            continue
        docs.append(
            RawDocument(
                text=text,
                source_id=md_path.stem,
                doc_type="battlecard",
                metadata={"filename": md_path.name},
            )
        )
    return docs
