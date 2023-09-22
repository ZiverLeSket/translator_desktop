import asyncio
import functools
import sys, os

import aiohttp

from PyQt6.QtWidgets import (
# from PySide2.QtWidgets import (
    QWidget,
    QLabel,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
)
from PyQt6.QtGui import QIcon
import qasync
from qasync import asyncSlot, asyncClose, QApplication

basedir = os.path.dirname(__file__)

def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
         base_path = os.path.dirname(__file__)
    return  os.path.join(base_path, relative_path)

class MainWindow(QWidget):
    """Main window."""

    _DEF_URL = 'https://api.mymemory.translated.net/'
    """str: Default URL."""

    _SESSION_TIMEOUT = 1.0
    """float: Session timeout."""

    _LANGUAGE_LIST =  {'Ukrainian': 'uk', 'Russian': 'ru', 'English': 'en', 'Deutch': 'de', 'French': 'fr', 'Romanian': 'ro', 'Moldavian': 'ro'}

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Translator")

        vLayout = QVBoxLayout()
        hLayout = QHBoxLayout()

        self.srcLang = QComboBox(self)
        self.dstLang = QComboBox(self)

        for language, code in self._LANGUAGE_LIST.items():
            self.srcLang.addItem(language, userData=code)
            self.dstLang.addItem(language, userData=code)
            
        hLayout.addWidget(self.srcLang)
        hLayout.addWidget(self.dstLang)
        
        vLayout.addLayout(hLayout)
        hLayout = QHBoxLayout()    
        self.srcText = QTextEdit('', self)
        self.dstText = QTextEdit('', self)
        hLayout.addWidget(self.srcText)
        hLayout.addWidget(self.dstText)
        vLayout.addLayout(hLayout)

        self.btnTranslate = QPushButton("Translate", self)
        self.btnTranslate.clicked.connect(self.on_btnTranslate_clicked)
        vLayout.addWidget(self.btnTranslate)
        
        self.lblStatus = QLabel("Idle", self)
        vLayout.addWidget(self.lblStatus)

        self.setLayout(vLayout)

        self.session = aiohttp.ClientSession(
            loop=asyncio.get_event_loop(),
            timeout=aiohttp.ClientTimeout(total=self._SESSION_TIMEOUT),
        )

    @asyncClose
    async def closeEvent(self, event):
        await self.session.close()

    @asyncSlot()
    async def on_btnTranslate_clicked(self):
        self.btnTranslate.setEnabled(False)
        self.lblStatus.setText("Translating...")

        text = self.srcText.toPlainText()
        srcLang = self.srcLang.currentData()
        dstLang = self.dstLang.currentData()
        params = {
            'q': text,
            'langpair': srcLang + '|' + dstLang,
        }
        try:
            async with self.session.get(self._DEF_URL, params=params) as r:
                r = await r.json()
                self.dstText.setText(r['responseData']['translatedText'])
        except Exception as exc:
            self.lblStatus.setText("Error: {}".format(exc))
        else:
            self.lblStatus.setText("translated")
        finally:
            self.btnTranslate.setEnabled(True)


async def main():
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    loop = asyncio.get_event_loop()
    future = asyncio.Future()

    app = QApplication.instance()
    app.setWindowIcon(QIcon(resource_path("icon.ico")))
    if hasattr(app, "aboutToQuit"):
        getattr(app, "aboutToQuit").connect(
            functools.partial(close_future, future, loop)
        )

    mainWindow = MainWindow()
    mainWindow.show()

    await future
    return True


if __name__ == "__main__":
    try:
        if sys.version_info.major == 3 and sys.version_info.minor == 11:
            with qasync._set_event_loop_policy(qasync.DefaultQEventLoopPolicy()):
                runner = asyncio.runners.Runner()
                try:
                    runner.run(main())
                finally:
                    runner.close()
        else:
            qasync.run(main())

    except asyncio.exceptions.CancelledError:
        sys.exit(0)