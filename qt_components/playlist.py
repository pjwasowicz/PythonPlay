from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QAbstractItemView, QHeaderView

class PlaylistTree(QTreeWidget):
    filesDropped = Signal(list, int)
    orderChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(False)
        self.header().setStretchLastSection(True)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        # Native Qt auto-scrolling is enabled by default, but we can explicitly set the margin
        self.setAutoScroll(True)
        self.setAutoScrollMargin(20)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        # External File Drop
        if event.mimeData().hasUrls() and event.source() != self:
            file_paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if file_paths:
                drop_item = self.itemAt(event.position().toPoint())
                if drop_item:
                    row = self.indexOfTopLevelItem(drop_item)
                    # If dropped below center of item, insert after
                    rect = self.visualItemRect(drop_item)
                    if event.position().toPoint().y() > rect.center().y():
                        row += 1
                else:
                    # Dropped in empty space
                    row = self.topLevelItemCount()
                    
                self.filesDropped.emit(file_paths, row)
            event.acceptProposedAction()
            return

        # Let Qt handle the internal move and UI updating natively
        super().dropEvent(event)
        self.orderChanged.emit()
