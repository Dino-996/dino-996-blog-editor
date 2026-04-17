from datetime import date
from typing import Optional
from sqlalchemy import create_engine, Text, Date
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column
from models.article import Article


# ─── Base SQLAlchemy ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─── Modello di persistenza ───────────────────────────────────────────────────
class ArticleRecord(Base):
    """
    Rappresenta una riga nella tabella 'articles' del database SQLite.

    È separato dalla dataclass Article di proposito:
      - Article  → modello di dominio, usato in tutta l'app
      - ArticleRecord → modello di persistenza, sa solo come stare nel DB

    Mapped[tipo] è la sintassi moderna di SQLAlchemy 2.0 —
    permette all'editor di conoscere il tipo di ogni colonna.
    """
    __tablename__ = "articles"

    id          : Mapped[int]           = mapped_column(primary_key=True, autoincrement=True)
    title       : Mapped[str]           = mapped_column(default="")
    description : Mapped[str]           = mapped_column(Text, default="")
    tags        : Mapped[str]           = mapped_column(default="")        # "python, pyqt6, blog"
    date        : Mapped[date]          = mapped_column(Date, default=date.today)
    excerpt     : Mapped[str]           = mapped_column(Text, default="")
    permalink   : Mapped[str]           = mapped_column(default="")
    image       : Mapped[str]           = mapped_column(default="")
    image_alt   : Mapped[str]           = mapped_column(default="")
    layout      : Mapped[str]           = mapped_column(default="layouts/post.njk")
    content     : Mapped[str]           = mapped_column(Text, default="")
    file_path   : Mapped[Optional[str]] = mapped_column(default=None)


# ─── Database manager ─────────────────────────────────────────────────────────
class Database:
    """
    Gestisce tutte le operazioni CRUD sul database SQLite.

    Il resto dell'app interagisce solo con questa classe —
    nessun altro file sa che esiste SQLAlchemy o SQLite.
    Questo pattern si chiama Repository.
    """

    def __init__(self, db_path: str = "blog.db"):
        """
        Crea il database se non esiste, si connette se esiste già.
        SQLite crea il file .db automaticamente al primo avvio.
        """
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)

        # create_all crea le tabelle mancanti — non tocca quelle esistenti
        Base.metadata.create_all(self._engine)

    # ─── CREATE / UPDATE ──────────────────────────────────────────────────────

    def save_article(self, article: Article) -> int:
        """
        Salva un articolo nel database.
        - Se article.id è None  → INSERT (nuovo articolo)
        - Se article.id è un int → UPDATE (articolo esistente)
        Restituisce l'id dell'articolo salvato o aggiornato.
        """
        with Session(self._engine) as session:
            if article.id is not None:
                # Aggiornamento: cerca il record esistente per id
                record = session.get(ArticleRecord, article.id)
                if record is None:
                    # Id non trovato nel DB — crea comunque
                    record = ArticleRecord()
                    session.add(record)
            else:
                # Inserimento: crea un nuovo record
                record = ArticleRecord()
                session.add(record)

            # Copia tutti i campi da Article (dominio) ad ArticleRecord (DB)
            record.title       = article.title
            record.description = article.description
            record.tags        = ", ".join(article.tags)   # ["python", "pyqt6"] → "python, pyqt6"
            record.date        = article.date
            record.excerpt     = article.excerpt
            record.permalink   = article.permalink
            record.image       = article.image
            record.image_alt   = article.image_alt
            record.layout      = article.layout
            record.content     = article.content
            record.file_path   = article.file_path

            session.commit()

            # refresh() aggiorna l'oggetto con i dati dal DB
            # necessario per leggere l'id generato dopo un INSERT
            session.refresh(record)
            return record.id

    # ─── READ ─────────────────────────────────────────────────────────────────

    def get_all_articles(self) -> list[Article]:
        """
        Restituisce tutti gli articoli ordinati per data decrescente
        (il più recente prima).
        """
        with Session(self._engine) as session:
            records = (
                session.query(ArticleRecord)
                .order_by(ArticleRecord.date.desc())
                .all()
            )
            return [self._to_article(r) for r in records]

    def get_article(self, article_id: int) -> Optional[Article]:
        """
        Restituisce un singolo articolo per id.
        Restituisce None se l'id non esiste.
        """
        with Session(self._engine) as session:
            record = session.get(ArticleRecord, article_id)
            if record is None:
                return None
            return self._to_article(record)

    # ─── DELETE ───────────────────────────────────────────────────────────────

    def delete_article(self, article_id: int) -> bool:
        """
        Elimina un articolo per id.
        Restituisce True se eliminato, False se l'id non esisteva.
        """
        with Session(self._engine) as session:
            record = session.get(ArticleRecord, article_id)
            if record is None:
                return False
            session.delete(record)
            session.commit()
            return True

    # ─── Conversione privata ──────────────────────────────────────────────────

    def _to_article(self, record: ArticleRecord) -> Article:
        """
        Converte un ArticleRecord (SQLAlchemy) in Article (dataclass).
        Metodo privato — usato solo internamente da get_article e get_all_articles.
        """
        return Article(
            id          = record.id,
            title       = record.title,
            description = record.description,
            tags        = [t.strip() for t in record.tags.split(",") if t.strip()],
            date        = record.date,
            excerpt     = record.excerpt,
            permalink   = record.permalink,
            image       = record.image,
            image_alt   = record.image_alt,
            layout      = record.layout,
            content     = record.content,
            file_path   = record.file_path,
        )