import os,sys
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSlider, QLabel
from PyQt5.QtCore import Qt,QThread,pyqtSignal


def ask_yn(question, default="yes"):
	valid = {"yes": True, "y": True, "ye": True,
			"no": False, "n": False}
	if default is None:
		prompt = " [y/n] "
	elif default == "yes":
		prompt = " [Y/n] "
	elif default == "no":
		prompt = " [y/N] "
	else:
		raise ValueError("invalid default answer: '%s'" % default)

	while True:
		print(question, prompt)
		choice = input().lower()
		if default is not None and choice == '':
			return valid[default]
		elif choice in valid:
			return valid[choice]
		else:
			print("Please respond with 'yes' or 'no' (or 'y' or 'n').")


def startfile(fname): #not really gui related...
	fname = os.path.normpath(fname)
	if os.path.isfile(fname): #otherwise its probably a category in the treeview
		if sys.platform == 'win32':
			os.startfile(fname)
		elif sys.platform == 'linux':
			os.system("nohup xdg-open \""+fname+"\" >/dev/null 2>&1 &")
	return


class BSlider(QWidget):
	def __init__(self, title, minval, maxval, slot=None, defval=0, orientation=Qt.Horizontal, parent=None):
		super().__init__(parent)

		self.value = defval

		self.slider = QSlider(orientation,self)
		self.slider.setTickPosition(QSlider.TicksBelow)
		self.slider.setValue(defval)
		self.slider.valueChanged[int].connect(self.changeValue)
		if slot != None:
			self.slider.valueChanged[int].connect(slot)

		self.title = QLabel(title,self)

		if isinstance(minval, str):
			# assume this is a switch with just two values.
			self.slider.setMinimum(0)
			self.slider.setMaximum(1)
			t = QHBoxLayout()
			t.setContentsMargins(0, 0, 0, 0)
			t.addWidget(QLabel(minval,self))
			t.addStretch(1)
			t.addWidget(QLabel(maxval,self))
		else:
			self.slider.setMinimum(minval)
			self.slider.setMaximum(maxval)
			self.vallabel = QLabel(str(defval),self)
			self.vallabel.setAlignment(Qt.AlignCenter)

		l = QVBoxLayout()
		l.setContentsMargins(0, 0, 0, 0)
		l.addWidget(self.title)
		l.addWidget(self.slider)
		if isinstance(minval, str):
			l.addLayout(t)
		else:
			l.addWidget(self.vallabel)

		self.setLayout(l)

	def changeValue(self,v):
		self.value = v
		# print(self.title.text(),v)
		try:
			self.vallabel.setText(str(v))
		except:
			pass


class progress_thread(QThread):
	progress = pyqtSignal(int,str)
	retval = pyqtSignal('PyQt_PyObject')
	def __init__(self,p2d_obj,iterable_func):
		QThread.__init__(self)
		self.p2d=p2d_obj
		self.iterable_func = iterable_func
	def run(self):
		cnt = 0
		#for i in self.p2d.execute_recreate():
		for i in getattr(self.p2d, self.iterable_func)():
			cnt+=1
			currentfile = i
			self.progress.emit(cnt,currentfile)
		self.retval.emit(self.p2d)


class check_state_thread(QThread):
	check_state_retval = pyqtSignal(int,'PyQt_PyObject')
	def __init__(self,p2d_obj):
		QThread.__init__(self)
		self.p2d=p2d_obj
	def run(self):
		#self.p2d.args['wololo']=True
		state = self.p2d.check_state()
		self.check_state_retval.emit(state,self.p2d)
