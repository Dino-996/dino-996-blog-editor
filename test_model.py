from models.article import Article
from models.database import Database
from datetime import date

# ── Test Article ──────────────────────────────────────────────────────────────
article = Article(
    title       = "Guida a PyQt6",
    description = "Come costruire app desktop con Python",
    tags        = ["python", "pyqt6", "desktop"],
    date        = date.today(),
    excerpt     = "Una guida completa a PyQt6",
    permalink   = "guida-pyqt6",
    image       = "/img/pyqt6.jpg",
    image_alt   = "Logo PyQt6",
    content     = "## Introduzione\n\nPyQt6 è un framework...",
)

# Verifica se va bene il frontmatter generato
print("=== Frontmatter generato ===")
print(article.to_markdown())

# ── Test Database ─────────────────────────────────────────────────────────────
db = Database("test.db")

# Salva
article_id = db.save_article(article)
print(f"\n=== Articolo salvato con id: {article_id} ===")

# Recupera
saved = db.get_article(article_id)
if saved is not None:
    print(f"Titolo recuperato: {saved.title}")
    print(f"Tags recuperati:   {saved.tags}")

# Lista tutti
articles = db.get_all_articles()
print(f"\nArticoli nel DB: {len(articles)}")

# Pulizia
import os
os.remove("test.db")
print("\nTest completato!")