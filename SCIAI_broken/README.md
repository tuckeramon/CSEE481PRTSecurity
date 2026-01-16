# SCIAI
PRT and Smart Manufacturing Systems

def update_cart_status_icons(self):
        specific_cart_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        while self.cart_status_layout.count():
            item = self.cart_status_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for cart_id in specific_cart_ids:
            label = QLabel()
            data = get_cart_info(cart_id)

            if not data:
                status = "unkown"
            else:
                status = data.get('event_type', 'unknown').lower()

            if status == 'active':
                pixmap = QPixmap("Icons/Active.png")
            elif status in ['idle', 'station']:
                pixmap = QPixmap("Icons/Idle.png")
            else:
                pixmap = QPixmap("Icons/Inactive.png")

            label.setPixmap(pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label.setToolTip(f"Cart {cart_id} - {status.capitalize()}")
            self.cart_status_layout.addWidget(label)