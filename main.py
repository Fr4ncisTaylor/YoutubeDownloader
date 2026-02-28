# Youtube downloader in pyqt6 by Francis Taylor :3

import os
import sys
import yt_dlp
import requests
import subprocess
from PIL import Image
from io import BytesIO
from pprint import pprint
from PyQt6.QtGui import QPixmap, QIcon, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
	QApplication, QWidget, QVBoxLayout, QHBoxLayout,
	QPushButton, QLineEdit, QLabel, QListWidget,
	QListWidgetItem, QTabWidget, QComboBox, QScrollArea, QFrame )


DOWNLOAD_DIR = "downloads" 
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

dark_stylesheet = """
QWidget {
    background-color: #101010;
    color: #E0E0E0;
    font-family: Segoe UI, Arial;
    font-size: 12px;
}
QLineEdit, QComboBox {
    background-color: #242424;
    border: 1px solid #3a3a3a;
    padding: 6px;
    border-radius: 8px;
    color: #E0E0E0;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #CA7428;
}
QComboBox QAbstractItemView {
    background-color: #242424;
    border: 1px solid #3a3a3a;
    selection-background-color: #CA7428;
    color: #E0E0E0;
    padding: 4px;
}
QPushButton {
    background-color: #2C2C2C;
    border: none;
    padding: 8px 16px;
    border-radius: 10px;
    color: #E0E0E0;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #0E0E0E;
}
QPushButton:pressed {
    background-color: #3A3A3A;
}
QTabWidget::pane {
    border: none;
    background-color: #181818;
}
QTabBar::tab {
    background: #242424;
    padding: 10px 30px;
    border: 1px solid #3a3a3a;
    border-bottom: none;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 5px;
    color: #E0E0E0;
    min-width: 100px;
}
QTabBar::tab:selected {
    background: #3C3C3C;
    color: #fff;
}
QFrame {
    background-color: #161616;
    border-radius: 10px;
    border: 1px solid #3A3A3A;
}
QFrame:hover {
    background-color: #3A3A3A;
}
QScrollArea {
    background-color: #181818;
}
QListWidget {
    background-color: #242424;
    border: none;
    border-radius: 8px;
    color: #E0E0E0;
}
QLabel {
    color: #E0E0E0;
}
"""

class VideoInfoThread(QThread):
	finished = pyqtSignal(dict)
	def __init__(self, url):
		super().__init__()
		self.url = url
	def run(self):
		ydl_opts = {"quiet": True}
		with yt_dlp.YoutubeDL(ydl_opts) as ydl:
			info = ydl.extract_info(self.url, download=False)
			self.finished.emit(info)

class DownloadThread(QThread):
	done = pyqtSignal(str)
	def __init__(self, url, format_id):
		super().__init__()
		self.url = url
		self.format_id = format_id
	def run(self):
		ydl_opts = {
			"format": self.format_id,
			"outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
			"quiet": False
		}
		with yt_dlp.YoutubeDL(ydl_opts) as ydl:
			result = ydl.extract_info(self.url, download=True)
			filename = ydl.prepare_filename(result)
		self.done.emit(filename)

class SearchThread(QThread):
	finished = pyqtSignal(list)
	def __init__(self, query):
		super().__init__()
		self.query = query
	def run(self):
		search_url = f"ytsearch10:{self.query}"
		ydl_opts = {"quiet": True, "extract_flat": "in_playlist"}
		with yt_dlp.YoutubeDL(ydl_opts) as ydl:
			results = ydl.extract_info(search_url, download=False)
			videos = []
			for entry in results.get("entries", []):
				videos.append({
					"id": entry["id"],
					"title": entry["title"],
					"url": f"https://www.youtube.com/watch?v={entry['id']}",
					"thumbnail": entry.get("thumbnail", "")
				})
			self.finished.emit(videos)

# galeria
class DownloadTab(QWidget):
	def __init__(self):
		super().__init__()
		layout = QVBoxLayout(self)
		layout.addWidget(QLabel("📁 Vídeos Baixados"))

		self.list = QListWidget()
		layout.addWidget(self.list)

		btn_layout = QHBoxLayout()
		self.delete_btn = QPushButton("🗑️ Excluir")
		self.open_folder_btn = QPushButton("📁 Abrir pasta")
		btn_layout.addWidget(self.delete_btn)
		btn_layout.addWidget(self.open_folder_btn)
		layout.addLayout(btn_layout)

		self.delete_btn.clicked.connect(self.delete_selected)
		self.open_folder_btn.clicked.connect(self.open_folder)
		self.refresh()

	def refresh(self):
		self.list.clear()
		for file in os.listdir(DOWNLOAD_DIR):
			item = QListWidgetItem(file)
			self.list.addItem(item)

	def delete_selected(self):
		item = self.list.currentItem()
		if not item:
			return
		file_path = os.path.join(DOWNLOAD_DIR, item.text())
		try:
			os.remove(file_path)
			self.refresh()
		except Exception as e:
			print("Erro ao excluir:", e)

	def open_folder(self):
		folder_path = os.path.abspath(DOWNLOAD_DIR)
		if sys.platform == "win32":
			subprocess.run(f'explorer "{folder_path}"')
		elif sys.platform == "darwin":
			subprocess.run(["open", folder_path])
		else:
			subprocess.run(["xdg-open", folder_path])

def load_pixmap_from_url(url, width=160, height=90):
	pixmap = QPixmap(width, height)
	pixmap.fill(Qt.GlobalColor.darkGray)  # placeholder escuro
	if not url:
		return pixmap
	try:
		headers = {"User-Agent": "Mozilla/5.0"}
		resp = requests.get(url, headers=headers, timeout=10)
		resp.raise_for_status()

		# Converte qualquer formato (webp/jpg/png) para RGBA e depois para QPixmap
		img = Image.open(BytesIO(resp.content)).convert("RGBA")
		data = BytesIO()
		img.save(data, format="PNG")
		pixmap.loadFromData(data.getvalue())
		pixmap = pixmap.scaled(
			width, height,
			Qt.AspectRatioMode.KeepAspectRatio,
			Qt.TransformationMode.SmoothTransformation
		)
	except Exception as e:
		print("Erro ao carregar thumbnail:", e)
	return pixmap

# aba principal
class MainTab(QWidget):
	def __init__(self, gallery_tab):
		super().__init__()
		self.gallery_tab = gallery_tab
		self.video_info = None
		self.search_results = []

		main_layout = QVBoxLayout(self)
		top_layout  = QHBoxLayout()

		self.mode_select = QComboBox()
		self.mode_select.addItems(["Pesquisa","URL"])

		font = QFont("Segoe UI", 12)
		self.mode_select.setFont(font)
		self.mode_select.view().setFont(font) 
		self.mode_select.setMinimumHeight(30)

		self.input_field = QLineEdit()
		self.input_field.setPlaceholderText("Cole o link do youtube ou digite o termo...")
		self.input_field.setFont(font)

		self.search_btn = QPushButton("Pesquisar")
		self.search_btn.setFont(font)
		self.search_btn.setStyleSheet("""
			QPushButton {
				background-color: #2c2c2c;
				border: 1px solid #3a3a3a;
				padding: 6px 12px;
				border-radius: 8px;
				color: #e0e0e0;
			}
			QPushButton:hover {
				background-color: #181818;
			}
		""")

		# Layout topo
		top_layout.addWidget(self.mode_select)
		top_layout.addWidget(self.input_field)
		top_layout.addWidget(self.search_btn)
		main_layout.addLayout(top_layout)

		self.result_area = QScrollArea()
		self.result_area.setWidgetResizable(True)
		self.result_container = QWidget()
		self.result_layout = QVBoxLayout(self.result_container)
		self.result_area.setWidget(self.result_container)
		main_layout.addWidget(self.result_area)

		self.search_btn.clicked.connect(self.perform_action)

	def perform_action(self):
		mode = self.mode_select.currentText()
		text = self.input_field.text()
		if not text:
			return

		self.search_btn.setEnabled(False)
		self.search_btn.setText("Carregando...")

		if mode == "URL":
			self.load_url(text)
		else:
			self.perform_search(text)

	def load_url(self, url):
		self.clear_results()
		self.thread = VideoInfoThread(url)
		self.thread.finished.connect(self.show_url_info)
		self.thread.start()

	def show_url_info(self, info):
		self.video_info = info
		self.clear_results()

		# thumbnail
		thumb_label = QLabel()
		thumb_label.setPixmap(load_pixmap_from_url(info.get("thumbnail",""), 400, 250))
		self.result_layout.addWidget(thumb_label)

		# título, duração, descrição
		self.result_layout.addWidget(QLabel(f"<b>{info['title']}</b>"))
		self.result_layout.addWidget(QLabel(f"Duração: {info.get('duration_string', '')}"))


		# formatos
		self.format_list = QListWidget()
		for f in info["formats"]:
			text = f"{f['format_id']} | {f['ext']} | {f.get('format_note','')}"
			item = QListWidgetItem(text)
			item.setData(Qt.ItemDataRole.UserRole, f["format_id"])
			self.format_list.addItem(item)
		self.result_layout.addWidget(self.format_list)

		# botão download
		self.download_btn = QPushButton("⬇ Baixar selecionado")
		self.download_btn.clicked.connect(self.download_selected)
		self.result_layout.addWidget(self.download_btn)

		self.search_btn.setEnabled(True)
		self.search_btn.setText("Pesquisar")

	def perform_search(self, query):
		self.clear_results()
		self.search_thread = SearchThread(query)
		self.search_thread.finished.connect(self.show_search_results)
		self.search_thread.start()

	def show_search_results(self, videos):
		self.search_results = videos
		self.clear_results()

		for video in videos:
			frame = QFrame()
			frame.setFrameShape(QFrame.Shape.StyledPanel)
			frame.setStyleSheet("""
				QFrame {
					background-color: #1e1e1e;
					color: #e0e0e0; 
					border: 1px solid #2D2D2D; 
					border-radius: 8px;
				}
				QFrame:hover {
					background-color: #404040;
				}
			""")
			layout = QHBoxLayout(frame)
			layout.setContentsMargins(5,5,5,5)
			layout.setSpacing(10)

			thumbnail_url = video.get("thumbnail", "")
			if not thumbnail_url and "id" in video:
				# busca info completa para garantir thumbnail
				try:
					ydl_opts = {"quiet": True}
					with yt_dlp.YoutubeDL(ydl_opts) as ydl:
						full_info = ydl.extract_info(f"https://www.youtube.com/watch?v={video['id']}", download=False)
						thumbnail_url = full_info.get("thumbnail", "")
				except Exception as e:
					print("Erro ao buscar thumbnail completa:", e)

			thumb = QLabel()
			thumb.setFixedSize(160, 90)
			thumb.setPixmap(load_pixmap_from_url(thumbnail_url, 160, 90))
			layout.addWidget(thumb)

			label = QLabel(video["title"])
			label.setWordWrap(True)
			layout.addWidget(label)

			def make_click_callback(v=video):
				return lambda e: self.load_url(v["url"])
			
			frame.mousePressEvent = make_click_callback(video)

			self.result_layout.addWidget(frame)

		spacer = QFrame()
		spacer.setFixedHeight(10)
		self.result_layout.addWidget(spacer)

		self.search_btn.setEnabled(True)
		self.search_btn.setText("Pesquisar")

	def clear_results(self):
		for i in reversed(range(self.result_layout.count())):
			widget = self.result_layout.itemAt(i).widget()
			if widget is not None:
				widget.setParent(None)

	def download_selected(self):
		item = self.format_list.currentItem()
		if not item:
			return
		format_id = item.data(Qt.ItemDataRole.UserRole)
		url = self.input_field.text()
		self.download_thread = DownloadThread(url, format_id)
		self.download_thread.done.connect(lambda f: self.gallery_tab.refresh())
		self.download_thread.start()

class App(QWidget):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("YouTube Downloader - PyQt6")
		self.resize(800, 700)
		layout = QVBoxLayout(self)
		self.tabs = QTabWidget()
		self.gallery_tab = DownloadTab()
		self.main_tab = MainTab(self.gallery_tab)
		self.tabs.addTab(self.main_tab, "Baixar conteúdo")
		self.tabs.addTab(self.gallery_tab, "Galeria")
		layout.addWidget(self.tabs)


if __name__ == "__main__":
	app  = QApplication(sys.argv)
	font = QFont("Segoe UI", 12)
	app.setFont(font)
	app.setStyleSheet(dark_stylesheet)
	window = App()
	window.show()
	sys.exit(app.exec())