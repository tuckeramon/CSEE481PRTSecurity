from PyQt5.QtWidgets import QWidget, QVBoxLayout


class DemonstrationView(QWidget):
    def __init__(self, user=None):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
