from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QDateEdit, QScrollArea, QPushButton
)
from PyQt6.QtCore import Qt, QDate
from models.article import Article


class MetadataPanel(QWidget):
    """
    Pannello inferiore — form con tutti i metadati del frontmatter Eleventy.
    Mostra e permette di modificare tutti i campi tranne il contenuto.
    """

    def __init__(self):
        super().__init__()
        self.setMaximumHeight(200)

        # Dichiarazione esplicita dei widget — l'editor li conosce
        self.field_title       = QLineEdit()
        self.field_description = QLineEdit()
        self.field_tags        = QLineEdit()
        self.field_excerpt     = QLineEdit()
        self.field_permalink   = QLineEdit()
        self.field_image       = QLineEdit()
        self.field_image_alt   = QLineEdit()
        self.date_edit         = QDateEdit()

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header della sezione
        header = QWidget()
        header.setStyleSheet("background: #F1F5F9; border-top: 1px solid #E2E8F0;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(16, 8, 16, 8)
        lbl = QLabel("Metadati articolo")
        lbl.setStyleSheet("font-size: 10pt; font-weight: bold; color: #64748B;")
        header_layout.addWidget(lbl)
        header_layout.addStretch()
        header.setLayout(header_layout)

        # Area scrollabile per il form — i campi sono molti
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        form_widget = QWidget()
        grid = QGridLayout()
        grid.setContentsMargins(16, 12, 16, 12)
        grid.setVerticalSpacing(8)
        grid.setHorizontalSpacing(12)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        # ── Configurazione campi ──────────────────────────────────────────────
        # Placeholder descrittivi — l'utente capisce cosa inserire
        self.field_title.setPlaceholderText("Titolo dell'articolo")
        self.field_description.setPlaceholderText("Breve descrizione per SEO")
        self.field_tags.setPlaceholderText("python, pyqt6, tutorial  (separati da virgola)")
        self.field_excerpt.setPlaceholderText("Estratto breve mostrato in lista")
        self.field_permalink.setPlaceholderText("Generato automaticamente dal titolo")
        self.field_permalink.setReadOnly(True)   # Solo lettura — generato da Eleventy
        self.field_permalink.setStyleSheet("background: #F8FAFC; color: #94A3B8;")
        self.field_image.setPlaceholderText("/img/nome-immagine.jpg")
        self.field_image_alt.setPlaceholderText("Descrizione accessibile dell'immagine")

        # QDateEdit — widget per selezionare una data con calendario
        self.date_edit.setCalendarPopup(True)    # Mostra calendario al click
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")

        # ── Layout a griglia su due colonne ───────────────────────────────────
        # Riga 0: Titolo | Data
        grid.addWidget(self._label("Titolo"),       0, 0)
        grid.addWidget(self.field_title,            0, 1)
        grid.addWidget(self._label("Data"),         0, 2)
        grid.addWidget(self.date_edit,              0, 3)

        # Riga 1: Description | Tags
        grid.addWidget(self._label("Description"), 1, 0)
        grid.addWidget(self.field_description,     1, 1)
        grid.addWidget(self._label("Tags"),        1, 2)
        grid.addWidget(self.field_tags,            1, 3)

        # Riga 2: Excerpt | Permalink
        grid.addWidget(self._label("Excerpt"),     2, 0)
        grid.addWidget(self.field_excerpt,         2, 1)
        grid.addWidget(self._label("Permalink"),   2, 2)
        grid.addWidget(self.field_permalink,       2, 3)

        # Riga 3: Image | ImageAlt
        grid.addWidget(self._label("Image"),       3, 0)
        grid.addWidget(self.field_image,           3, 1)
        grid.addWidget(self._label("ImageAlt"),    3, 2)
        grid.addWidget(self.field_image_alt,       3, 3)

        form_widget.setLayout(grid)
        scroll.setWidget(form_widget)

        main_layout.addWidget(header)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def _label(self, text: str) -> QLabel:
        """Helper — crea un'etichetta con stile uniforme."""
        lbl = QLabel(text + ":")
        lbl.setStyleSheet("font-size: 10pt; color: #64748B;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return lbl

    def _input_style(self) -> str:
        return """
            QLineEdit {
                font-size: 10pt;
                padding: 4px 8px;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
            }
        """

    # ─── Metodi pubblici — chiamati dal controller ────────────────────────────

    def load_article(self, article: Article):
        """
        Popola il form con i dati di un articolo.
        Chiamato dal controller quando l'utente seleziona un articolo dalla lista.
        """
        self.field_title.setText(article.title)
        self.field_description.setText(article.description)

        # I tag sono una lista — li mostriamo come stringa separata da virgola
        # Escludiamo 'post' dalla visualizzazione — viene aggiunto automaticamente
        user_tags = [t for t in article.tags if t != "post"]
        self.field_tags.setText(", ".join(user_tags))

        self.field_excerpt.setText(article.excerpt)
        self.field_permalink.setText(f"/blog/{{{{ title | slug }}}}/")
        self.field_image.setText(article.image)
        self.field_image_alt.setText(article.image_alt)

        # Converte date Python in QDate per il widget
        self.date_edit.setDate(QDate(
            article.date.year,
            article.date.month,
            article.date.day
        ))

    def get_metadata(self) -> dict:
        """
        Legge tutti i valori del form e li restituisce come dizionario.
        Chiamato dal controller prima di salvare l'articolo.
        """
        # Legge la data dal QDateEdit e la converte in date Python
        qdate = self.date_edit.date()

        # Parsing tag: "python, pyqt6, tutorial" → ["python", "pyqt6", "tutorial"]
        # strip() rimuove spazi, filter() elimina stringhe vuote
        raw_tags = self.field_tags.text()
        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]

        return {
            "title":       self.field_title.text().strip(),
            "description": self.field_description.text().strip(),
            "tags":        tags,
            "date":        qdate.toPyDate(),
            "excerpt":     self.field_excerpt.text().strip(),
            "image":       self.field_image.text().strip(),
            "image_alt":   self.field_image_alt.text().strip(),
        }

    def clear(self):
        """Svuota tutti i campi — usato per un nuovo articolo."""
        self.field_title.clear()
        self.field_description.clear()
        self.field_tags.clear()
        self.field_excerpt.clear()
        self.field_permalink.setText("/blog/{{ title | slug }}/")
        self.field_image.clear()
        self.field_image_alt.clear()
        self.date_edit.setDate(QDate.currentDate())