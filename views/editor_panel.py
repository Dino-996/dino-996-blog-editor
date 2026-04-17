from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QSplitter, QLabel
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QTextCursor, QFont
import markdown2


class EditorPanel(QWidget):
    """
    Pannello centrale — editor Markdown a sinistra, preview HTML a destra.

    Emette un segnale content_changed ogni volta che il testo cambia,
    così il controller sa che ci sono modifiche non salvate.
    """

    content_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        # QTimer per la preview — aggiorna 500ms dopo l'ultimo tasto premuto.
        # Senza il timer, la preview si aggiornerebbe ad ogni singolo carattere
        # digitato, causando lag. Con il timer aspettiamo che l'utente
        # smetta di digitare prima di aggiornare.
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)   # Si attiva una sola volta
        self._preview_timer.setInterval(500)       # 500ms di attesa
        self._preview_timer.timeout.connect(self._update_preview) # type: ignore[attr-defined]

        self.editor = QTextEdit()
        self.preview = QWebEngineView()

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_toolbar())
        layout.addWidget(self._build_editor_area())

        self.setLayout(layout)

    def _build_toolbar(self) -> QWidget:
        """
        Toolbar con scorciatoie Markdown.
        Ogni pulsante inserisce la sintassi corretta nel punto del cursore.
        """
        toolbar = QWidget()
        toolbar.setStyleSheet("""
            QWidget { background: #F8FAFC; border-bottom: 1px solid #E2E8F0; }
            QPushButton {
                background: transparent;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 10pt;
                color: #1E293B;
                min-width: 32px;
            }
            QPushButton:hover { background: #E2E8F0; }
            QPushButton:pressed { background: #CBD5E1; }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Definizione pulsanti: (testo, prefisso, suffisso, placeholder)
        # prefisso e suffisso sono i caratteri Markdown da inserire attorno al testo
        buttons = [
            ("H1",   "# ",       "",   "Titolo"),
            ("H2",   "## ",      "",   "Sottotitolo"),
            ("H3",   "### ",     "",   "Sezione"),
            ("B",    "**",       "**", "grassetto"),
            ("I",    "_",        "_",  "corsivo"),
            ("`",    "`",        "`",  "codice"),
            ("```",  "```\n",    "\n```", "codice"),
            ("Link", "[",        "](url)", "testo link"),
            ("Img",  "![",       "](url)", "alt text"),
            ("---",  "\n---\n",  "",   ""),
            ("- ",   "\n- ",     "",   "elemento lista"),
        ]

        for label, prefix, suffix, placeholder in buttons:
            btn = QPushButton(label)
            # Usa una lambda con argomenti di default per catturare i valori
            # corretti — senza default gli argomenti verrebbero catturati
            # per riferimento e avrebbero tutti l'ultimo valore del loop
            btn.clicked.connect(lambda checked, p=prefix, s=suffix, ph=placeholder:self._insert_markdown(p, s, ph)) # type: ignore[attr-defined]
            layout.addWidget(btn)

        layout.addStretch()

        # Label che mostra il conteggio parole
        self.lbl_wordcount = QLabel("0 parole")
        self.lbl_wordcount.setStyleSheet("font-size: 9pt; color: #94A3B8;")
        layout.addWidget(self.lbl_wordcount)

        toolbar.setLayout(layout)
        return toolbar

    def _build_editor_area(self) -> QSplitter:
        """
        QSplitter divide lo spazio tra editor e preview.
        L'utente può trascinare il divisore per ridimensionare i pannelli.
        """
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Editor ────────────────────────────────────────────────────────────
        self.editor.setFont(QFont("Courier New", 11))
        self.editor.setStyleSheet("""
            QTextEdit {
                background: #1E293B;
                color: #E2E8F0;
                border: none;
                padding: 16px;
                line-height: 1.6;
            }
        """)
        self.editor.setPlaceholderText("Inizia a scrivere in Markdown...")

        # textChanged si attiva ad ogni modifica del testo
        self.editor.textChanged.connect(self._on_text_changed) # type: ignore[attr-defined]

        # ── Preview ───────────────────────────────────────────────────────────
        # QWebEngineView mostra HTML — useremo setHtml() per aggiornarlo
        self.preview.setStyleSheet("border: none;")

        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)

        # setSizes imposta la dimensione iniziale dei due pannelli
        # I valori sono proporzioni — 1:1 divide lo spazio a metà
        splitter.setSizes([500, 500])

        return splitter

    # ─── Slot privati ─────────────────────────────────────────────────────────

    def _on_text_changed(self):
        """
        Chiamato ad ogni modifica del testo.
        Aggiorna il contatore parole e riavvia il timer della preview.
        """
        text = self.editor.toPlainText()

        # Conteggio parole — split() divide per spazi e newline
        word_count = len(text.split()) if text.strip() else 0
        self.lbl_wordcount.setText(f"{word_count} parole")

        # Riavvia il timer — se l'utente continua a digitare il timer
        # viene resettato e la preview non si aggiorna fino a quando
        # smette di digitare per 500ms
        self._preview_timer.start()

        # Notifica il controller che ci sono modifiche non salvate
        self.content_changed.emit()

    def _update_preview(self):
        """
        Converte il Markdown in HTML e lo mostra nella preview.
        Chiamato dal timer 500ms dopo l'ultimo tasto premuto.
        """
        markdown_text = self.editor.toPlainText()

        # markdown2.markdown converte Markdown in HTML
        # extras aggiunge funzionalità extra:
        # - fenced-code-blocks: blocchi ```codice```
        # - tables: tabelle Markdown
        # - strike: ~~testo barrato~~
        html_body = markdown2.markdown(markdown_text, extras=["fenced-code-blocks", "tables", "strike"])

        # Costruisce una pagina HTML completa con CSS per lo stile
        # Questo è il CSS che vedrà l'utente nella preview
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-size: 16px;
                line-height: 1.7;
                color: #1E293B;
                max-width: 720px;
                margin: 0 auto;
                padding: 24px;
            }}
            h1, h2, h3 {{ color: #0F172A; margin-top: 1.5em; }}
            h1 {{ font-size: 2em; border-bottom: 2px solid #E2E8F0; padding-bottom: 0.3em; }}
            h2 {{ font-size: 1.5em; border-bottom: 1px solid #E2E8F0; padding-bottom: 0.2em; }}
            code {{
                background: #F1F5F9;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                color: #7C3AED;
            }}
            pre {{
                background: #1E293B;
                color: #E2E8F0;
                padding: 16px;
                border-radius: 8px;
                overflow-x: auto;
            }}
            pre code {{ background: none; color: #E2E8F0; padding: 0; }}
            blockquote {{
                border-left: 4px solid #3B82F6;
                margin: 0;
                padding: 8px 16px;
                background: #EFF6FF;
                color: #1E40AF;
            }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #E2E8F0; padding: 8px 12px; text-align: left; }}
            th {{ background: #F1F5F9; font-weight: 600; }}
            a {{ color: #3B82F6; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            img {{ max-width: 100%; border-radius: 8px; }}
            hr {{ border: none; border-top: 2px solid #E2E8F0; margin: 2em 0; }}
        </style>
        </head>
        <body>
        {html_body}
        </body>
        </html>
        """

        # setHtml aggiorna il contenuto della WebView
        self.preview.setHtml(html)

    def _insert_markdown(self, prefix: str, suffix: str, placeholder: str):
        """
        Inserisce la sintassi Markdown attorno al testo selezionato,
        oppure inserisce un placeholder se non c'è selezione.
        """
        cursor = self.editor.textCursor()

        if cursor.hasSelection():
            # Testo selezionato — avvolgi con prefix e suffix
            selected = cursor.selectedText()
            cursor.insertText(f"{prefix}{selected}{suffix}")
        else:
            # Nessuna selezione — inserisci prefix + placeholder + suffix
            # e seleziona il placeholder per permettere sostituzione immediata
            start_pos = cursor.position()
            cursor.insertText(f"{prefix}{placeholder}{suffix}")

            # Seleziona il placeholder inserito
            if placeholder:
                cursor.setPosition(start_pos + len(prefix))
                cursor.setPosition(
                    start_pos + len(prefix) + len(placeholder),
                    QTextCursor.MoveMode.KeepAnchor
                )
                self.editor.setTextCursor(cursor)

        # Rimetti il focus sull'editor dopo il click sul pulsante
        self.editor.setFocus()

    # ─── Metodi pubblici — chiamati dal controller ────────────────────────────

    def set_content(self, content: str):
        """Carica il contenuto Markdown nell'editor."""
        # blockSignals(True) impedisce che setText emetta textChanged
        # evitando un aggiornamento inutile della preview durante il caricamento
        self.editor.blockSignals(True)
        self.editor.setPlainText(content)
        self.editor.blockSignals(False)
        self._update_preview()

    def get_content(self) -> str:
        """Restituisce il contenuto Markdown dell'editor."""
        return self.editor.toPlainText()

    def clear(self):
        """Svuota l'editor."""
        self.editor.blockSignals(True)
        self.editor.clear()
        self.editor.blockSignals(False)
        self.preview.setHtml("<html><body></body></html>")
        self.lbl_wordcount.setText("0 parole")