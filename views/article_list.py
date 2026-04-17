from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel,
    QPushButton, QLineEdit    
    )
from PyQt6.QtCore import Qt, pyqtSignal
from models.article import Article


class ArticleListPanel(QWidget):
    """
    Pannello sinistro — lista degli articoli salvati nel DB.

    Emette segnali custom invece di fare cose direttamente:
    - article_selected  → quando l'utente clicca un articolo
    - new_article       → quando l'utente clicca "Nuovo"
    - delete_requested  → quando l'utente clicca "Elimina"

    Il controller ascolta questi segnali e decide cosa fare.
    """

    # ── Segnali custom ────────────────────────────────────────────────────────
    # pyqtSignal(tipo) definisce un segnale che trasporta un valore di quel tipo.
    # È diverso dai segnali built-in come clicked — questi li definiamo noi.
    article_selected  = pyqtSignal(int)   # Emette l'id dell'articolo selezionato
    new_article       = pyqtSignal()      # Nessun dato — solo notifica
    delete_requested  = pyqtSignal(int)   # Emette l'id da eliminare

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(220)
        self.setMaximumWidth(300)

        # Mappa id_articolo → QListWidgetItem — per ritrovare l'item per id
        self._id_map: dict[int, QListWidgetItem] = {}

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_search())
        layout.addWidget(self._build_list())
        layout.addWidget(self._build_footer())

        self.setLayout(layout)

    def _build_header(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: #1E293B;")
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Articoli")
        title.setStyleSheet("font-size: 13pt; font-weight: bold; color: white;")

        self.btn_new = QPushButton("+")
        self.btn_new.setFixedSize(28, 28)
        self.btn_new.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 18pt;
                font-weight: bold;
            }
            QPushButton:hover { background: #2563EB; }
        """)
        # Connette il click del pulsante al segnale custom new_article
        self.btn_new.clicked.connect(self.new_article.emit) # type: ignore[attr-defined]

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.btn_new)
        container.setLayout(layout)
        return container

    def _build_search(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: #1E293B; padding-bottom: 8px;")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 0, 12, 8)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Cerca articolo...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                background: #334155;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 10pt;
            }
        """)
        # textChanged emette il testo ad ogni carattere digitato
        self.search_box.textChanged.connect(self._on_search) # type: ignore[attr-defined]

        layout.addWidget(self.search_box)
        container.setLayout(layout)
        return container

    def _build_list(self) -> QWidget:
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: #1E293B;
                border: none;
                color: #CBD5E1;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-bottom: 1px solid #334155;
            }
            QListWidget::item:selected {
                background: #3B82F6;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background: #334155;
            }
        """)
        # itemClicked emette l'item cliccato
        self.list_widget.itemClicked.connect(self._on_item_clicked) # type: ignore[attr-defined]
        return self.list_widget

    def _build_footer(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: #1E293B; border-top: 1px solid #334155;")
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)

        self.btn_delete = QPushButton("Elimina")
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #EF4444;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 10pt;
            }
            QPushButton:hover { background: #450A0A; }
            QPushButton:disabled { color: #475569; border-color: #475569; }
        """)
        self.btn_delete.setEnabled(False)  # Disabilitato finché non si seleziona un articolo
        self.btn_delete.clicked.connect(self._on_delete_clicked) # type: ignore[attr-defined]

        layout.addStretch()
        layout.addWidget(self.btn_delete)
        container.setLayout(layout)
        return container

    # ─── Metodi pubblici — chiamati dal controller ────────────────────────────

    def populate(self, articles: list[Article]):
        """
        Popola la lista con gli articoli dal DB.
        Chiamato dal controller all'avvio e dopo ogni salvataggio.
        """
        self.list_widget.clear()
        self._id_map.clear()

        for article in articles:
            if article.id is None:
                continue

            # Testo dell'item: titolo + data
            label = article.title if article.title else "Senza titolo"
            date_str = article.date.strftime("%d/%m/%Y")
            item = QListWidgetItem(f"{label}\n{date_str}")

            # Salva l'id nell'item — lo recuperiamo al click
            item.setData(Qt.ItemDataRole.UserRole, article.id)

            self.list_widget.addItem(item)
            self._id_map[article.id] = item

    def select_article(self, article_id: int):
        """Seleziona un articolo nella lista per id."""
        if article_id in self._id_map:
            self.list_widget.setCurrentItem(self._id_map[article_id])
            self.btn_delete.setEnabled(True)

    def clear_selection(self):
        """Deseleziona tutto e disabilita il pulsante elimina."""
        self.list_widget.clearSelection()
        self.btn_delete.setEnabled(False)

    # ─── Slot privati ─────────────────────────────────────────────────────────

    def _on_item_clicked(self, item: QListWidgetItem):
        """Quando si clicca un item, emette l'id dell'articolo."""
        article_id = item.data(Qt.ItemDataRole.UserRole)
        if article_id is not None:
            self.btn_delete.setEnabled(True)
            self.article_selected.emit(article_id)

    def _on_delete_clicked(self):
        """Quando si clicca Elimina, emette l'id dell'articolo selezionato."""
        current = self.list_widget.currentItem()
        if current is None:
            return
        article_id = current.data(Qt.ItemDataRole.UserRole)
        if article_id is not None:
            self.delete_requested.emit(article_id)

    def _on_search(self, text: str):
        """
        Filtra gli item della lista in base al testo cercato.
        Nasconde gli item che non corrispondono — non li elimina.
        """
        text = text.lower().strip()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item is not None:
                # setHidden(True) nasconde l'item senza rimuoverlo
                item.setHidden(text not in item.text().lower())