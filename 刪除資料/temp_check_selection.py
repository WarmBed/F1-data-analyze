from PyQt5.QtWidgets import QApplication
from f1t_gui_main import StyleHMainWindow

app = QApplication([])
win = StyleHMainWindow()
index_value = win.race_combo.currentIndex()
text_value = win.race_combo.currentText()
print("index", index_value, flush=True)
print("text", text_value, flush=True)
with open("temp_selection_output.txt", "w", encoding="utf-8") as handle:
	handle.write(f"index={index_value}\n")
	handle.write(f"text={text_value}\n")
win.close()
app.quit()
