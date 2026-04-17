import os
from slugify import slugify
from models.article import Article
from models.database import Database
from views.main_window import MainWindow


class EditorController:
    """
    Collega view e model — gestisce tutta la logica dell'applicazione.

    Responsabilità:
    - Ascolta i segnali della view
    - Legge e scrive sul database tramite Database
    - Aggiorna la view con i dati aggiornati

    Non sa nulla di come appare la UI — usa solo i metodi pubblici della view.
    Non sa nulla di SQL — usa solo i metodi pubblici di Database.
    """

    def __init__(self, view: MainWindow, db: Database):
        self._view = view
        self._db   = db

        # Articolo attualmente aperto nell'editor
        # None = nessun articolo aperto
        self._current_article: Article | None = None

        self._connect_signals()
        self._load_article_list()

    def _connect_signals(self):
        """Connette tutti i segnali della view ai metodi di questo controller."""
        self._view.new_requested.connect(self._on_new)
        self._view.save_requested.connect(self._on_save)
        self._view.export_requested.connect(self._on_export)
        self._view.article_selected.connect(self._on_article_selected)
        self._view.delete_requested.connect(self._on_delete)

    # ─── Caricamento lista ────────────────────────────────────────────────────

    def _load_article_list(self):
        """
        Carica tutti gli articoli dal DB e popola la lista.
        Chiamato all'avvio e dopo ogni salvataggio o eliminazione.
        """
        articles = self._db.get_all_articles()
        self._view.article_list.populate(articles)
        self._view.show_status(f"{len(articles)} articoli nel database")

    # ─── Nuovo articolo ───────────────────────────────────────────────────────

    def _on_new(self):
        """
        Crea un nuovo articolo vuoto.
        Chiede conferma se ci sono modifiche non salvate.
        """
        # Programmazione difensiva — chiedi conferma prima di perdere modifiche
        if not self._view.confirm_discard():
            return

        # Crea un articolo vuoto con i valori di default
        self._current_article = Article()

        # Aggiorna tutti i pannelli della view
        self._view.editor_panel.clear()
        self._view.metadata_panel.clear()
        self._view.article_list.clear_selection()
        self._view.set_current_title("Nuovo articolo")
        self._view.show_status("Nuovo articolo creato")

    # ─── Selezione articolo ───────────────────────────────────────────────────

    def _on_article_selected(self, article_id: int):
        """
        Carica un articolo dal DB e lo mostra nell'editor.
        Chiamato quando l'utente clicca un articolo nella lista.
        """
        # Programmazione difensiva — chiedi conferma se ci sono modifiche
        if not self._view.confirm_discard():
            # Ripristina la selezione precedente nella lista
            if self._current_article is not None and self._current_article.id is not None:
                self._view.article_list.select_article(self._current_article.id)
            return

        article = self._db.get_article(article_id)
        if article is None:
            self._view.show_status("Errore: articolo non trovato")
            return

        self._current_article = article

        # Carica i dati nei pannelli
        self._view.editor_panel.set_content(article.content)
        self._view.metadata_panel.load_article(article)
        self._view.article_list.select_article(article_id)
        self._view.set_current_title(article.title)
        self._view.show_status(f"Articolo caricato: {article.title}")

    # ─── Salvataggio ──────────────────────────────────────────────────────────

    def _on_save(self):
        """
        Salva l'articolo corrente nel database.
        Legge i dati da tutti i pannelli, li assembla e li persiste.
        """
        # Programmazione difensiva — non salvare se non c'è nulla di aperto
        if self._current_article is None:
            self._view.show_status("Nessun articolo da salvare")
            return

        # Legge i metadati dal pannello metadati
        metadata = self._view.metadata_panel.get_metadata()

        # Programmazione difensiva — il titolo è obbligatorio
        if not metadata["title"].strip():
            self._view.show_status("Il titolo è obbligatorio per salvare")
            return

        # Legge il contenuto dall'editor
        content = self._view.editor_panel.get_content()

        # Aggiorna l'articolo corrente con i nuovi dati
        self._current_article.title       = metadata["title"]
        self._current_article.description = metadata["description"]
        self._current_article.tags        = metadata["tags"]
        self._current_article.date        = metadata["date"]
        self._current_article.excerpt     = metadata["excerpt"]
        self._current_article.image       = metadata["image"]
        self._current_article.image_alt   = metadata["image_alt"]
        self._current_article.content     = content

        # Genera il permalink dallo slug del titolo
        # slugify("Guida a PyQt6") → "guida-a-pyqt6"
        self._current_article.permalink = slugify(metadata["title"])

        # Salva nel DB — save_article gestisce INSERT o UPDATE automaticamente
        saved_id = self._db.save_article(self._current_article)
        self._current_article.id = saved_id

        # Aggiorna la view
        self._view.mark_saved()
        self._view.set_current_title(self._current_article.title)
        self._load_article_list()
        self._view.article_list.select_article(saved_id)
        self._view.show_status(f"Salvato: {self._current_article.title}") # type: ignore[]

    # ─── Esportazione .md ─────────────────────────────────────────────────────

    def _on_export(self):
        """
        Esporta l'articolo corrente come file .md con frontmatter Eleventy.
        Apre un dialogo per scegliere dove salvare il file.
        """
        # Programmazione difensiva
        if self._current_article is None:
            self._view.show_status("Nessun articolo da esportare")
            return

        # Salva prima di esportare — così il file .md è aggiornato
        self._on_save()

        if self._current_article is None:
            return

        # Suggerisce un nome file basato sul permalink
        slug = self._current_article.permalink or "articolo"
        suggested_name = f"{slug}.md"

        # Apre il dialogo di salvataggio
        path = self._view.ask_export_path(suggested_name)

        # Programmazione difensiva — l'utente ha annullato il dialogo
        if not path:
            return

        # Scrive il file .md con frontmatter YAML
        try:
            content = self._current_article.to_markdown()
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            # Aggiorna il percorso file nell'articolo e risalva nel DB
            self._current_article.file_path = path
            self._db.save_article(self._current_article)

            self._view.show_status(f"Esportato in: {path}")

        except OSError as e:
            # OSError copre tutti gli errori di I/O: permessi, disco pieno, ecc.
            self._view.show_status(f"Errore durante l'esportazione: {e}")

    # ─── Eliminazione ─────────────────────────────────────────────────────────

    def _on_delete(self, article_id: int):
        """
        Elimina un articolo dal database dopo conferma.
        Non elimina il file .md — solo il record nel DB.
        """
        article = self._db.get_article(article_id)
        if article is None:
            return

        # Programmazione difensiva — chiedi sempre conferma prima di eliminare
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self._view,
            "Elimina articolo",
            f"Vuoi eliminare '{article.title}'?\nQuesta operazione non può essere annullata.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No    # Default su No — più sicuro
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        deleted = self._db.delete_article(article_id)

        if deleted:
            # Se l'articolo eliminato era quello aperto, svuota l'editor
            if (self._current_article is not None and
                    self._current_article.id == article_id):
                self._current_article = None
                self._view.editor_panel.clear()
                self._view.metadata_panel.clear()
                self._view.set_current_title("")

            self._load_article_list()
            self._view.show_status("Articolo eliminato")
        else:
            self._view.show_status("Errore durante l'eliminazione")