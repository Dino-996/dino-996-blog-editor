from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Article:
    """
    Rappresenta un articolo del blog.
    @dataclass genera automaticamente __init__, __repr__ e __eq__
    basandosi sui campi definiti — equivalente a un record in Java 16+.

    Questi campi corrispondono esattamente al frontmatter Eleventy:
    ---
    layout: layouts/post.njk
    title: Il mio articolo
    description: Una breve descrizione
    tags: [python, pyqt6]
    date: 2024-01-15
    excerpt: Estratto breve
    permalink: /blog/il-mio-articolo/
    image: /img/articolo.jpg
    imageAlt: Descrizione immagine
    ---
    """

    # Metadati Eleventy — corrispondono 1:1 al frontmatter
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=lambda: [])  # list mutabile — non usare [] come default
    date: date = field(default_factory=date.today)
    excerpt: str = ""
    permalink: str = ""
    image: str = ""
    image_alt: str = ""
    layout: str = "layouts/post.njk"  # Default Eleventy — raramente cambia

    # Contenuto dell'articolo (il corpo dopo il frontmatter)
    content: str = ""

    # Metadati interni — non finiscono nel frontmatter
    id: Optional[int] = None          # ID nel database SQLite
    file_path: Optional[str] = None   # Percorso del file .md salvato

    def to_markdown(self) -> str:
        """
        Serializza l'articolo in formato .md con frontmatter YAML.
        Questo è il formato esatto che Eleventy si aspetta.
        """
        # 'post' è sempre il primo tag — obbligatorio per Eleventy
        # Aggiunge 'post' solo se non è già presente per evitare duplicati
        all_tags = ["post"] + [t for t in self.tags if t != "post"]

        # Formato lista YAML con trattini
        tags_lines = "\n".join(f"  - {tag}" for tag in all_tags)

        # Costruisce il frontmatter riga per riga — nessuna indentazione spuria
        # textwrap.dedent() è un'alternativa, ma costruire esplicitamente è più chiaro
        lines = [
            "---",
            f"layout: {self.layout}",
            f"title: {self.title}",
            f"description: {self.description}",
            f"tags:",
            tags_lines,
            f"date: {self.date.isoformat()}",
            f"excerpt: {self.excerpt}",
            "permalink: /blog/{{ title | slug }}/",
            f"image: {self.image}",
            f"imageAlt: {self.image_alt}",
            "---",
            "",
            self.content,
        ]

        return "\n".join(lines)

    @classmethod
    def from_markdown(cls, text: str) -> "Article":
        """
        Deserializza un file .md con frontmatter YAML in un Article.
        @classmethod è un metodo di classe — come un factory method statico in Java.
        Riceve 'cls' (la classe) invece di 'self' (l'istanza).
        """
        article = cls()

        # Separa frontmatter dal contenuto
        # Un file .md valido inizia con --- e ha un secondo ---
        if not text.startswith("---"):
            article.content = text
            return article

        parts = text.split("---", 2)
        if len(parts) < 3:
            article.content = text
            return article

        frontmatter_text = parts[1].strip()
        article.content = parts[2].strip()

        # Parsing manuale del YAML riga per riga
        # (evitiamo la dipendenza da PyYAML per semplicità)
        for line in frontmatter_text.splitlines():
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            if key == "title":
                article.title = value
            elif key == "description":
                article.description = value
            elif key == "tags":
                # Parsing "[python, pyqt6]" → ["python", "pyqt6"]
                value = value.strip("[]")
                article.tags = [t.strip() for t in value.split(",") if t.strip()]
            elif key == "date":
                try:
                    article.date = date.fromisoformat(value)
                except ValueError:
                    article.date = date.today()
            elif key == "excerpt":
                article.excerpt = value
            elif key == "permalink":
                # Rimuove /blog/ e gli slash per estrarre solo lo slug
                article.permalink = value.strip("/").replace("blog/", "")
            elif key == "image":
                article.image = value
            elif key == "imageAlt":
                article.image_alt = value
            elif key == "layout":
                article.layout = value

        return article
