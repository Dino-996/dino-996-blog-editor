from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QToolBar,
    QStatusBar, QPushButton, QLabel,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QCloseEvent

from views.article_list import ArticleListPanel
from views.editor_panel import EditorPanel
from views.metadata_panel import MetadataPanel


class MainWindow(QMainWindow):
    """
    Finestra principale — assembla tutti i pannelli e li coordina.

    Usiamo QMainWindow invece di QWidget perché QMainWindow offre
    gratis: toolbar, menu bar, status bar e dock widgets.
    In tutti i progetti precedenti usavamo QWidget perché non
    avevamo bisogno di queste funzionalità.

    Emette segnali che il controller ascolta:
    - save_requested      → utente vuole salvare
    - export_requested    → utente vuole esportare in .md
    - new_requested       → utente vuole un nuovo articolo
    - article_selected    → utente ha selezionato un articolo dalla lista
    - delete_requested    → utente vuole eliminare un articolo
    """

    save_requested    = pyqtSignal()
    export_requested  = pyqtSignal()
    new_requested     = pyqtSignal()
    article_selected  = pyqtSignal(int)
    delete_requested  = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blog Editor")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        # Flag che traccia se ci sono modifiche non salvate
        # Usato per mostrare un avviso prima di chiudere o cambiare articolo
        self._has_unsaved_changes = False

        # I tre pannelli principali — dichiarati qui perché il controller
        # ne ha bisogno per connettersi ai loro segnali
        self.article_list   = ArticleListPanel()
        self.editor_panel   = EditorPanel()
        self.metadata_panel = MetadataPanel()

        self._build_ui()
        self._build_toolbar()
        self._build_statusbar()
        self._connect_internal_signals()

    def _build_ui(self):
        """
        Assembla i tre pannelli con QSplitter.
        Layout finale:
            [Lista articoli] | [Editor + Preview]
                               [Metadati]
        """

        # Splitter verticale destra: editor sopra, metadati sotto
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.editor_panel)
        right_splitter.addWidget(self.metadata_panel)
        # Editor occupa 70% dello spazio, metadati 30%
        right_splitter.setSizes([500, 200])
        right_splitter.setHandleWidth(4)

        # Splitter orizzontale principale: lista a sinistra, editor+metadati a destra
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(self.article_list)
        main_splitter.addWidget(right_splitter)
        # Lista occupa ~20%, editor+metadati ~80%
        main_splitter.setSizes([250, 1000])
        main_splitter.setHandleWidth(4)

        # QMainWindow richiede un widget centrale — non puoi fare setLayout()
        # direttamente come con QWidget
        self.setCentralWidget(main_splitter)

    def _build_toolbar(self):
        """
        QToolBar — barra degli strumenti in cima alla finestra.
        Contiene le azioni principali dell'applicazione.
        """
        toolbar = QToolBar("Principale")
        toolbar.setMovable(False)    # Non spostabile dall'utente
        toolbar.setStyleSheet("""
            QToolBar {
                background: #F8FAFC;
                border-bottom: 1px solid #E2E8F0;
                padding: 4px 8px;
                spacing: 4px;
            }
            QPushButton {
                background: transparent;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 10pt;
                color: #1E293B;
            }
            QPushButton:hover { background: #E2E8F0; }
            QPushButton:pressed { background: #CBD5E1; }
        """)

        # ── Pulsante Nuovo ────────────────────────────────────────────────────
        btn_new: QPushButton = QPushButton("+ Nuovo")
        btn_new.clicked.connect(self.new_requested.emit) # type: ignore[attr-defined]
        toolbar.addWidget(btn_new)

        toolbar.addSeparator()

        # ── Pulsante Salva ────────────────────────────────────────────────────
        self.btn_save = QPushButton("Salva")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: #1A56A0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 10pt;
            }
            QPushButton:hover { background: #1E40AF; }
            QPushButton:pressed { background: #1E3A8A; }
        """)
        self.btn_save.clicked.connect(self.save_requested.emit) # type: ignore[attr-defined]
        # Scorciatoia da tastiera Ctrl+S
        self.btn_save.setShortcut(QKeySequence("Ctrl+S"))
        toolbar.addWidget(self.btn_save)

        # ── Pulsante Esporta .md ──────────────────────────────────────────────
        btn_export = QPushButton("Esporta .md")
        btn_export.clicked.connect(self.export_requested.emit) # type: ignore[attr-defined]
        toolbar.addWidget(btn_export)

        toolbar.addSeparator()

        # ── Label titolo articolo corrente ────────────────────────────────────
        self.lbl_current = QLabel("Nessun articolo aperto")
        self.lbl_current.setStyleSheet("font-size: 10pt; color: #64748B; padding: 0 8px;")
        toolbar.addWidget(self.lbl_current)

        self.addToolBar(toolbar)

    def _build_statusbar(self):
        """
        QStatusBar — barra in fondo alla finestra.
        Mostra messaggi di stato temporanei (salvataggio, errori...).
        """
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: #F1F5F9;
                border-top: 1px solid #E2E8F0;
                font-size: 9pt;
                color: #64748B;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto")

    def _connect_internal_signals(self):
        """
        Connette i segnali interni tra i pannelli.
        Questi non passano dal controller — sono dettagli interni della view.
        """
        # Quando la lista emette article_selected, lo riemettiamo verso il controller 
        self.article_list.article_selected.connect(self.article_selected.emit) # type: ignore[attr-defined]
        self.article_list.new_article.connect(self.new_requested.emit) # type: ignore[attr-defined]
        self.article_list.delete_requested.connect(self.delete_requested.emit) # type: ignore[attr-defined]

        # Quando il contenuto cambia, aggiorna il flag modifiche non salvate
        self.editor_panel.content_changed.connect(self._on_content_changed) # type: ignore[attr-defined]

    # ─── Slot privati ─────────────────────────────────────────────────────────

    def _on_content_changed(self):
        """Marca l'articolo come modificato — aggiorna titolo finestra."""
        self._has_unsaved_changes = True
        # Aggiunge asterisco al titolo per indicare modifiche non salvate
        # Convenzione standard in tutti gli editor desktop
        if not self.windowTitle().startswith("*"):
            self.setWindowTitle(f"* Blog Editor")

    # ─── Metodi pubblici — chiamati dal controller ────────────────────────────

    def set_current_title(self, title: str):
        """Aggiorna il label del titolo nella toolbar."""
        self.lbl_current.setText(title if title else "Senza titolo")
        self.setWindowTitle(f"Blog Editor — {title}" if title else "Blog Editor")
        self._has_unsaved_changes = False

    def show_status(self, message: str, timeout: int = 3000):
        """
        Mostra un messaggio nella status bar.
        timeout in millisecondi — 0 = messaggio permanente.
        """
        self.status_bar.showMessage(message, timeout)

    def confirm_discard(self) -> bool:
        """
        Mostra un dialogo di conferma se ci sono modifiche non salvate.
        Restituisce True se l'utente vuole procedere, False se vuole annullare.
        Programmazione difensiva — chiamata prima di aprire un altro articolo
        o creare uno nuovo.
        """
        if not self._has_unsaved_changes:
            return True

        # QMessageBox.question mostra un dialogo con pulsanti personalizzati
        reply = QMessageBox.question(
            self,
            "Modifiche non salvate",
            "Hai modifiche non salvate. Vuoi continuare senza salvare?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No    # Pulsante di default
        )
        return reply == QMessageBox.StandardButton.Yes

    def ask_export_path(self, suggested_name: str) -> str:
        """
        Apre il dialogo di salvataggio file e restituisce il percorso scelto.
        Restituisce stringa vuota se l'utente annulla.
        """
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Esporta articolo",
            suggested_name,
            "Markdown (*.md);;Tutti i file (*)"
        )
        return path

    def mark_saved(self):
        """Rimuove il marcatore di modifiche non salvate."""
        self._has_unsaved_changes = False
        title = self.lbl_current.text()
        self.setWindowTitle(f"Blog Editor — {title}" if title else "Blog Editor")

    # ─── Gestione chiusura finestra ───────────────────────────────────────────
    
    def closeEvent(self, a0: QCloseEvent) -> None:
        """
        Intercetta la chiusura della finestra.
        closeEvent è un metodo di QWidget che viene chiamato automaticamente
        quando l'utente clicca la X — possiamo sovrascriverlo per aggiungere
        logica prima della chiusura.
        """
        if self._has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Modifiche non salvate",
                "Hai modifiche non salvate. Vuoi salvare prima di uscire?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            if reply == QMessageBox.StandardButton.Save:
                # Emette il segnale di salvataggio e poi chiude
                self.save_requested.emit()
                a0.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                a0.accept()
            else:
                # Cancel — non chiudere
                a0.ignore()
        else:
            a0.accept()