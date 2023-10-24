import sys
from os import path

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFileDialog

from Objects.mole import Mole


class ImageViewer(QtWidgets.QWidget):
    def __init__(self, moleID, profile):
        super(ImageViewer, self).__init__()
        # Finding all details of mole using mole ID and connection to SQLite database.
        self.moleID = moleID
        self.moles = None
        # Passing connection to database as well. Won't be an issue as its being accessed infrequently, so won't
        # cause any concurrent connections/latency
        self.profile = profile
        self.update_mole_list()

        # Keeping track of the mole ID and coords, in case all moles are deleted and another needs to be added.
        self.x = self.moles[0].x
        self.y = self.moles[0].y
        self.mole_number = 0
        self.text_size = 40
        self.viewer = PhotoViewer(self)

        # 'Load image' buttons
        self.prevBtn = QtWidgets.QToolButton(self)
        self.prevBtn.setText('<')
        self.prevBtn.setFont(QFont('Times', self.text_size))
        self.prevBtn.clicked.connect(self.prevButton)

        self.nextBtn = QtWidgets.QToolButton(self)
        self.nextBtn.setText('>')
        self.nextBtn.setFont(QFont('Times', self.text_size))
        self.nextBtn.clicked.connect(self.nextButton)

        # Labels to add space between other elements.
        self.sep_label = QtWidgets.QLabel(self)
        self.sep_label.setFont(QFont('Times', self.text_size))
        self.sep_label.setText("      ")

        self.sep_label2 = QtWidgets.QLabel(self)
        self.sep_label2.setFont(QFont('Times', self.text_size))
        self.sep_label2.setText("      ")

        # Label to keep track of which picture is being displayed
        self.mole_label = QtWidgets.QLabel(self)
        self.mole_label.setFont(QFont('Times', self.text_size))

        # Date the picture was taken
        self.date_label = QtWidgets.QLabel(self)
        self.date_label.setFont(QFont('Times', self.text_size))

        # Add picture to this record
        self.add_pic_button = QtWidgets.QToolButton(self)
        self.add_pic_button.setText('Add Picture')
        self.add_pic_button.setFont(QFont('Times', self.text_size))
        self.add_pic_button.clicked.connect(self.add_pic)

        # Remove picture from record
        self.remove_pic_button = QtWidgets.QToolButton(self)
        self.remove_pic_button.setText('Remove Picture')
        self.remove_pic_button.setFont(QFont('Times', self.text_size))
        self.remove_pic_button.clicked.connect(self.remove_pic)

        # Close window
        self.exitButton = QtWidgets.QToolButton(self)
        self.exitButton.setText('Exit')
        self.exitButton.setFont(QFont('Times', self.text_size))
        self.exitButton.clicked.connect(self.close)

        # Arrange layout
        VBlayout = QtWidgets.QVBoxLayout(self)
        VBlayout.addWidget(self.viewer)
        left_layout = QtWidgets.QHBoxLayout()
        left_layout.setAlignment(QtCore.Qt.AlignLeft)
        left_layout.addWidget(self.prevBtn)
        left_layout.addWidget(self.nextBtn)
        left_layout.addWidget(self.mole_label)
        left_layout.addWidget(self.sep_label)
        left_layout.addWidget(self.date_label)
        left_layout.addWidget(self.sep_label2)
        left_layout.addWidget(self.add_pic_button)
        left_layout.addWidget(self.remove_pic_button)
        left_layout.addWidget(self.exitButton)
        VBlayout.addLayout(left_layout)

        # Load first image
        self.nextImage()

        self.setWindowTitle("Mole Viewer")

    # This function updates the date and mole number labels. Called when next or previous picture is pressed,
    # or when mole added/removed
    def update_labels(self):
        if len(self.moles) > 0:
            text_str = str(self.mole_number + 1) + ' / ' + str(len(self.moles))
            self.mole_label.setText(text_str)
            self.date_label.setText(self.moles[self.mole_number].date)
        else:
            text_str = ""
            self.mole_label.setText(text_str)
            self.date_label.setText(text_str)

    # Load the next image
    def nextButton(self):
        if self.mole_number + 1 != len(self.moles):
            self.mole_number = self.mole_number + 1
            self.nextImage()

    # Load previous image
    def prevButton(self):
        if self.mole_number != 0:
            self.mole_number = self.mole_number - 1
            self.nextImage()

    # Uses the mole number to load the image from the list of moles
    def nextImage(self):
        pix = QtGui.QPixmap()
        if len(self.moles) > 0:
            pix.loadFromData(self.moles[self.mole_number].pic)
        else:
            pix.load(self.get_img_path("none.png"))
        self.viewer.setPhoto(pix)
        self.update_labels()

    # Bundling images with pyinstaller changes their filepath, this function accounts for that
    def get_img_path(self, filename):
        if hasattr(sys, "_MEIPASS"):
            return path.join(sys._MEIPASS, filename)
        else:
            return filename
        pass

    # Add new image to this record.
    def add_pic(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Choose Image", options=options)
        print(file_name)
        if file_name != "":
            print("Adding image")
            blob = self.profile.convertToBinaryData(file_name)
            self.profile.add_existing_record(self.moleID, self.x, self.y, blob)
            self.update_mole_list()
            self.mole_number = len(self.moles) - 1
            self.update_labels()
            self.nextImage()

    # Remove image from this record
    def remove_pic(self):
        if len(self.moles) != 0:
            query = QtWidgets.QMessageBox
            res = query.question(self, 'Delete Picture', 'Are you sure you want to delete this picture?', query.Yes | query.No)
            if res == query.Yes:
                self.profile.removeMolePic(self.moles[self.mole_number].unique_id)
                self.update_mole_list()
                self.mole_number = 0
                self.update_labels()
                self.nextImage()

    # Easier to recreate the moles list than attempt to get a unique ID from the SQLITE database, and append/remove
    def update_mole_list(self):
        res = self.profile.get_mole_details(self.moleID)
        self.moles = [Mole(*mol) for mol in res]


# This class handles the image being displayed and interacted with. Can zoom/pan around image.
class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.pyqtSignal(QtCore.QPoint)

    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def hasPhoto(self):
        return not self._empty

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    def setPhoto(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
        if self.hasPhoto():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        if self._photo.isUnderMouse():
            self.photoClicked.emit(self.mapToScene(event.pos()).toPoint())
        super(PhotoViewer, self).mousePressEvent(event)



