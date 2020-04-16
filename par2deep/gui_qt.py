import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon,QStandardItemModel
from PyQt5.QtCore import QSettings,Qt
try:
	from par2deep import *
	from toolbox import *
except:
	from .par2deep import *
	from .toolbox import *


class app_window(QMainWindow):
	def __init__(self, *args,**kwargs):
		super().__init__(*args,**kwargs)
		self.setWindowTitle("par2deep")
		self.resize(800, 800)
		#self.move(300, 300)
		self.setWindowIcon(QIcon('../par2deep.ico'))
		self.guisettings = QSettings("BrentH", "par2deep")
		
		self.new_window(self.topbar_frame(0), self.start_options_frame(), self.start_actions_frame())


	def new_window(self,t,m,b):
		subframe = QWidget()
		mainLayout = QVBoxLayout()
		mainLayout.addWidget(t,0)
		t.setFixedHeight(100)
		mainLayout.addWidget(m,1)
		mainLayout.addWidget(b,0)
		b.setFixedHeight(100)
		subframe.setLayout(mainLayout)
		self.setCentralWidget(subframe)


	def topbar_frame(self,stage):
		subframe = QWidget()
		l = QHBoxLayout()
		l.addStretch(1)
		labels = ["Start","Proposed actions","Executing actions","Report","Further actions","Final report"]
		labels[stage] = '<u>'+labels[stage]+'</u>'
		for label in labels:
			l.addWidget(QLabel(label))
			l.insertSpacing(-1,10)
		l.addStretch(1)
		subframe.setLayout(l)
		return subframe


	def start_options_frame(self,chosen_dir=None):
	
		self.p2d = par2deep(chosen_dir)

		basicset = QGroupBox("Basic Settings")
		
		def pickdir():
			new_dirname = str(QFileDialog.getExistingDirectory(self, 'Set directory in which to protect data'))
			self.new_window(self.topbar_frame(0), self.start_options_frame(new_dirname), self.start_actions_frame())
			
		pickdir_btn = QPushButton("Pick directory")
		pickdir_btn.clicked.connect(pickdir)
		
		def textchanged(text):
			if os.path.isdir(text):
				self.new_window(self.topbar_frame(0), self.start_options_frame(text), self.start_actions_frame())
		
		pickdir_txt = QLineEdit(self.p2d.args["directory"])
		pickdir_txt.textChanged.connect(textchanged)
		
		basicset_layout = QHBoxLayout()
		basicset_layout.addWidget(pickdir_btn,0)
		basicset_layout.addWidget(pickdir_txt,1)
		basicset.setLayout(basicset_layout)

		advset = QGroupBox("Advanced Settings")
		
		cb1 = QCheckBox("Overwrite all parity data")
		cb1.setChecked(self.p2d.args["overwrite"])
		cb1.setToolTip("Existing parity data found (*.par* files) will be removed and overwritten.")
		cb1.stateChanged.connect(lambda fldval : self.p2d.args.update({"overwrite":bool(fldval)}))
		
		cb2 = QCheckBox("Skip verification")
		cb2.setChecked(self.p2d.args["noverify"])
		cb2.setToolTip("Skips verification of files with existing parity data. Use when you just want to create parity data for newly added files.")
		cb2.stateChanged.connect(lambda fldval : self.p2d.args.update({"noverify":bool(fldval)}))
		
		cb3 = QCheckBox("Keep orphaned par2 files")
		cb3.setChecked(self.p2d.args["keep_orphan"])
		cb3.setToolTip("Do not remove unused parity files (*.par*).")
		cb3.stateChanged.connect(lambda fldval : self.p2d.args.update({"keep_orphan":bool(fldval)}))
		
		cb4 = QCheckBox("Keep backup files")
		cb4.setChecked(self.p2d.args["keep_backup"])
		cb4.setToolTip("Do not remove backup files (*.[0-9]).")
		cb4.stateChanged.connect(lambda fldval : self.p2d.args.update({"keep_backup":bool(fldval)}))
		
		ex_lb = QLabel("Exclude directories (comma separated):")
		ex_fld = QLineEdit(','.join(self.p2d.args["excludes"]))
		ex_fld.setToolTip("These sub-directories will be excluded from the analysis. Use 'root' for the root of the directory.")
		ex_fld.textChanged.connect(lambda fldval : self.p2d.args.update({"excludes":fldval.split(',')}))

		exex_lb = QLabel("Exclude extensions (comma separated):")
		exex_fld = QLineEdit(','.join(self.p2d.args["extexcludes"]))
		exex_fld.setToolTip("These extensions will be excluded from the analysis.")
		exex_fld.textChanged.connect(lambda fldval : self.p2d.args.update({"extexcludes":fldval.split(',')}))
		
		parpath_lb = QLabel("Path to par2(.exe):")
		parpath_fld = QLineEdit(self.p2d.args["par_cmd"])
		parpath_fld.setToolTip("Should be set automatically and correctly, but can be overridden.")
		parpath_fld.textChanged.connect(lambda fldval : self.p2d.args.update({"par_cmd":fldval}))
		
		perc_sldr = BSlider("Percentage of protection",5,100,lambda fldval : self.p2d.args.update({"percentage":fldval}),self.p2d.args["percentage"])
		perc_sldr.setToolTip("The maximum percentage of corrupted data you will be able to recover from. Higher is safer, but uses more disk space.")

		advset_layout = QVBoxLayout()
		advset_layout.addWidget(cb1,0)
		advset_layout.addWidget(cb2,0)
		advset_layout.addWidget(cb3,0)
		advset_layout.addWidget(cb4,0)
		advset_layout.addWidget(ex_lb,0)
		advset_layout.addWidget(ex_fld,0)
		advset_layout.addWidget(exex_lb,0)
		advset_layout.addWidget(exex_fld,0)
		advset_layout.addWidget(parpath_lb,0)
		advset_layout.addWidget(parpath_fld,0)
		advset_layout.addWidget(perc_sldr,0)
		advset.setLayout(advset_layout)

		subframe = QWidget()
		l = QVBoxLayout()
		l.addWidget(basicset)
		l.addWidget(advset)
		l.addStretch(1)
		subframe.setLayout(l)
		return subframe


	def start_actions_frame(self):
		ssa_btn = QPushButton("Check directory contents")
		ssa_btn.clicked.connect(self.set_start_actions)
		
		subframe = QWidget()
		l = QHBoxLayout()
		l.addStretch(1)
		l.addWidget(ssa_btn)
		l.addStretch(1)
		subframe.setLayout(l)
		return subframe


	def repair_actions_frame(self):
		subframe = QWidget()
		l = QHBoxLayout()
		l.addStretch(1)
		
		if self.p2d.len_verified_actions > 0:
			btn1 = QPushButton("Fix repairable corrupted files and recreate unrepairable files")
			btn1.clicked.connect(self.repair_action)
			l.addWidget(btn1)
			
			btn2 = QPushButton("Recreate parity files for the repairable and unrepairable files")
			btn2.clicked.connect(self.recreate_action)
			l.addWidget(btn2)
		else:
			btn1 = QPushButton("Nothing to do. Exit.")
			btn1.clicked.connect(QApplication.instance().quit)
			l.addWidget(btn1)
			
		l.addStretch(1)
		subframe.setLayout(l)
		
		return subframe


	def execute_actions_frame(self):
		if self.p2d.len_all_actions > 0:
			b=QPushButton("Run actions")
			b.clicked.connect(self.execute_actions)
		else:
			b=QPushButton("Nothing to do. Exit.")
			b.clicked.connect(QApplication.instance().quit)
		
		subframe = QWidget()
		l = QHBoxLayout()
		l.addStretch(1)
		l.addWidget(b)
		l.addStretch(1)
		subframe.setLayout(l)
		
		return subframe


	def exit_actions_frame(self):
		b=QPushButton("Exit.")
		b.clicked.connect(QApplication.instance().quit)
		
		subframe = QWidget()
		l = QVBoxLayout()
		l.addStretch(1)
		if hasattr(self.p2d,'len_all_err'):
			l.addWidget(QLabel("There were "+str(self.p2d.len_all_err)+" errors."))
		l.addWidget(b)
		l.addStretch(1)
		subframe.setLayout(l)
		return subframe


	def exit_frame(self):
		subframe = QWidget()
		l = QHBoxLayout()
		l.addStretch(1)
		l.addWidget(QLabel("The par2 command you specified is invalid."))
		l.addStretch(1)
		subframe.setLayout(l)
		return subframe


	def progress_indef_frame(self):
		pb = QProgressBar()
		pb.setRange(0,0) #indefinite
		lb = QLabel("Indexing directory, may take a few moments...")
		
		subframe = QWidget()
		l = QVBoxLayout()
		l.addStretch(1)
		l.addWidget(pb)
		l.addWidget(lb)
		l.addStretch(1)
		subframe.setLayout(l)
		return subframe


	def progress_frame(self,length):
		self.pb = QProgressBar()
		self.pb.setRange(0,length) #indefinite
		self.pb_currentfile = QLabel("Executing actions, may take a few moments...")
		
		subframe = QWidget()
		l = QVBoxLayout()
		l.addStretch(1)
		l.addWidget(self.pb)
		l.addWidget(self.pb_currentfile)
		l.addStretch(1)
		subframe.setLayout(l)
		return subframe


	def blank_frame(self):
		return QWidget()


	def repair_action(self):
		self.new_window(self.topbar_frame(4), self.blank_frame(), self.progress_frame(self.p2d.len_verified_actions))

		self.p2d_t = progress_thread(self.p2d,'execute_repair')
		
		def run(pd2_obj):
			self.pd2 = pd2_obj
			dispdict = {
				'verifiedfiles_succes' : 'Verified and in order',
				'createdfiles' : 'Newly created parity files',
				'removedfiles' : 'Files removed',
				'createdfiles_err' : 'Errors during creating parity files',
				'removedfiles_err' : 'Errors during file removal',
				'fixes' : 'Verified files succesfully fixed',
				'fixes_err' : 'Verified files failed to fix',
				'recreate' : 'Succesfully recreated (overwritten) parity files',
				'recreate_err' : 'Failed (overwritten) new parity files'
				}
			self.new_window(self.topbar_frame(5), self.scrollable_treeview_frame(dispdict), self.exit_actions_frame())
			#put p2d.len_all_err somewhere in label of final report
		
		def upd(cnt,currentfile):
			self.pb.setValue(cnt)
			self.pb_currentfile.setText("Processing "+os.path.basename(currentfile))
		
		self.p2d_t.progress.connect(upd)
		self.p2d_t.retval.connect(run)
		self.p2d_t.start()
		return


	def recreate_action(self):
		self.new_window(self.topbar_frame(4), self.blank_frame(), self.progress_frame(self.p2d.len_verified_actions))

		self.p2d_t = progress_thread(self.p2d,'execute_recreate')
		
		def run(pd2_obj):
			self.pd2 = pd2_obj
			dispdict = {
				'verifiedfiles_succes' : 'Verified and in order',
				'createdfiles' : 'Newly created parity files',
				'removedfiles' : 'Files removed',
				'createdfiles_err' : 'Errors during creating parity files',
				'removedfiles_err' : 'Errors during file removal',
				'fixes' : 'Verified files succesfully fixed',
				'fixes_err' : 'Verified files failed to fix',
				'recreate' : 'Succesfully recreated (overwritten) parity files',
				'recreate_err' : 'Failed (overwritten) new parity files'
				}
			self.new_window(self.topbar_frame(5), self.scrollable_treeview_frame(dispdict), self.exit_actions_frame())
			#put p2d.len_all_err somewhere in label of final report
		
		def upd(cnt,currentfile):
			self.pb.setValue(cnt)
			self.pb_currentfile.setText("Processing "+os.path.basename(currentfile))
		
		self.p2d_t.progress.connect(upd)
		self.p2d_t.retval.connect(run)
		self.p2d_t.start()
		return


	def set_start_actions(self):
		# DEBUG: print(self.p2d.args)
		
		self.p2d_t = check_state_thread(self.p2d)
		
		#go to second frame
		self.new_window(self.topbar_frame(0), self.blank_frame(), self.progress_indef_frame())
		
		def run(check_state_retval,pd2_obj):
			self.pd2 = pd2_obj
			if check_state_retval == 200:
				self.new_window(self.topbar_frame(0), self.exit_frame(), self.exit_actions_frame())
				return
			dispdict = {
				'create' : 'Create parity files',
				'incomplete' : 'Replace parity files',
				'verify' : 'Verify files',
				'unused' : 'Remove these unused files',
				'par2errcopies' : 'Remove old repair files'
				}
			self.new_window(self.topbar_frame(1), self.scrollable_treeview_frame(dispdict), self.execute_actions_frame())
		
		self.p2d_t.check_state_retval.connect(run)
		self.p2d_t.start()
		return


	def execute_actions(self):
		self.new_window(self.topbar_frame(2), self.blank_frame(), self.progress_frame(self.p2d.len_all_actions))

		#go to third frame		
		self.p2d_t = progress_thread(self.p2d,'execute')
		
		def run(pd2_obj):
			self.pd2 = pd2_obj
			dispdict = {
				'verifiedfiles_succes' : 'Verified and in order',
				'createdfiles' : 'Newly created parity files',
				'removedfiles' : 'Files removed',
				'createdfiles_err' : 'Errors during creating parity files',
				'verifiedfiles_err' : 'Irrepairable damage found',
				'verifiedfiles_repairable' : 'Repairable damage found',
				'removedfiles_err' : 'Errors during file removal'
				}
			self.new_window(self.topbar_frame(3), self.scrollable_treeview_frame(dispdict), self.repair_actions_frame())
		
		def upd(cnt,currentfile):
			self.pb.setValue(cnt)
			self.pb_currentfile.setText("Processing "+os.path.basename(currentfile))
		
		self.p2d_t.progress.connect(upd)
		self.p2d_t.retval.connect(run)
		self.p2d_t.start()
		return


	def scrollable_treeview_frame(self,nodes={}):
		tree=QTreeWidget()
		tree.setHeaderLabels(["Filename", "Action"])
		tree.setColumnWidth(0,600) #unf at this point tree.width is not jet set to the onscreen value.
		tree.setContextMenuPolicy(Qt.CustomContextMenu);
		
		for i,(node,label) in enumerate(nodes.items()):
			if len(getattr(self.p2d,node))==0:
				tree.addTopLevelItem(QTreeWidgetItem(None,
					[label+": no files.",'']
					))
			else:
				thing = QTreeWidgetItem(None,
					[label+": expand to see "+str(len(getattr(self.p2d,node))),'']
					)
				tree.addTopLevelItem(thing)
	
				# FIXME: show files in fs hierarchy, not flat
				for item in getattr(self.p2d,node):
					if not isinstance(item, list):
						thing.addChild(QTreeWidgetItem(None,
							[item,node]
							))
					else:
						thing.addChild(QTreeWidgetItem(None,
							[item[0],node]
							))

		# http://blog.asimation.com/37/
		
		def doubleclick_tree(event):
			startfile(tree.currentItem().text(0))
			return
		
		tree.itemDoubleClicked.connect(doubleclick_tree)

		def show_contextmenu(position):
			popup = QMenu()
			for node,label in nodes.items():
				popup.addAction(label)
			action = popup.exec_(tree.mapToGlobal(position))
			print(action)
			# FIXME actually change actions per file.
			#for node,label in nodes.items():
				#if action == quitAction:
				#qApp.quit()
				
		tree.customContextMenuRequested.connect(show_contextmenu)
		
		subframe = QWidget()
		l = QHBoxLayout()
		l.addWidget(tree)
		subframe.setLayout(l)
		
		return subframe



def main():
	app = QApplication(sys.argv)
	#print(QStyleFactory.keys())
	#try:
		#app.setStyle('Breeze')
	#except:
		#pass
	mw = app_window()
	mw.show()
	sys.exit(app.exec_())

if __name__ == "__main__":
	main()
