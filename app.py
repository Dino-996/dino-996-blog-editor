import sys
from PyQt6.QtWidgets import QApplication
from views.main_window import MainWindow
from controllers.editor_controller import EditorController
from models.database import Database


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Applica uno stile globale all'applicazione
    app.setStyle("Fusion")

    # 1. Crea il database (o si connette se esiste già)
    db = Database("blog.db")

    # 2. Crea la view
    window = MainWindow()

    # 3. Crea il controller passandogli view e database
    controller = EditorController(window, db)

    # 4. Mostra la finestra e avvia il loop degli eventi
    window.show()
    sys.exit(app.exec())