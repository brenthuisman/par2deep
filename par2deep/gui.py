#!/usr/bin/env python
import os,threading
from tkinter import *
from tkinter.ttk import *
from tkinter import Scale #new one sucks
from tkinter import filedialog #old one dont work
try:
	from .par2deep import *
except:
	from par2deep import *


class CreateToolTip(object):
	"""
	create a tooltip for a given widget.
	Copied from https://stackoverflow.com/a/36221216
	"""
	def __init__(self, widget, text='widget info'):
		self.waittime = 500     #milliseconds
		self.wraplength = 250   #pixels
		self.widget = widget
		self.text = text
		self.widget.bind("<Enter>", self.enter)
		self.widget.bind("<Leave>", self.leave)
		self.widget.bind("<ButtonPress>", self.leave)
		self.id = None
		self.tw = None

	def enter(self, event=None):
		self.schedule()

	def leave(self, event=None):
		self.unschedule()
		self.hidetip()

	def schedule(self):
		self.unschedule()
		self.id = self.widget.after(self.waittime, self.showtip)

	def unschedule(self):
		id = self.id
		self.id = None
		if id:
			self.widget.after_cancel(id)

	def showtip(self, event=None):
		x = y = 0
		x, y, cx, cy = self.widget.bbox("insert")
		x += self.widget.winfo_rootx() + 25
		y += self.widget.winfo_rooty() + 20
		# creates a toplevel window
		self.tw = Toplevel(self.widget)
		# Leaves only the label and removes the app window
		self.tw.wm_overrideredirect(True)
		self.tw.wm_geometry("+%d+%d" % (x, y))
		label = Label(self.tw, text=self.text, justify='left',
					background="#ffffff", relief='solid', borderwidth=1,
					wraplength = self.wraplength)
		label.pack(ipadx=1)

	def hidetip(self):
		tw = self.tw
		self.tw= None
		if tw:
			tw.destroy()


class app_frame(Frame):
	def __init__(self, master):
		Frame.__init__(self, master)
		self.grid(row=0, column=0, sticky=NSEW)
		#main window has 1 frame, thats it
		Grid.rowconfigure(master, 0, weight=1)
		Grid.columnconfigure(master, 0, weight=1)
		self.waittime = 500     #milliseconds

		#swithin that, frames, row-wise, which are updated as necesary.
		#topbar: displays stage of verification
		#middle screen shows options or info
		#bottom bar shows actions
		self.new_window(self.topbar_frame(0), self.start_options_frame(), self.start_actions_frame())
		return


	def startfile(self, fname):
		fname = os.path.normpath(fname)
		if os.path.isfile(fname): #otherwise its probably a category in the treeview
			if sys.platform == 'win32':
				os.startfile(fname)
			elif sys.platform == 'linux':
				os.system("nohup xdg-open \""+fname+"\" >/dev/null 2>&1 &")
		return


	def new_window(self,t,m,b):
		#swithin that, frames, row-wise, which are updated as necesary.
		#topbar: displays stage of verification
		#middle screen shows options or info
		#bottom bar shows actions

		for rows in range(3):
			Grid.rowconfigure(self, rows, weight=1)
		for columns in range(1):
			Grid.columnconfigure(self, columns, weight=1)

		Grid.rowconfigure(self, 0, weight=0) #override weight: sets size to minimal size
		self.topbar = t
		self.topbar.grid(row=0, column=0, sticky=N+S+E+W,padx=20,pady=(20,0))

		self.mid = m
		self.mid.grid(row=1, column=0, sticky=N+S+E+W,padx=20,pady=(20,0))

		Grid.columnconfigure(self, 2, weight=0)
		self.actbar = b
		self.actbar.grid(row=2, column=0, sticky=N+S+E+W,padx=20,pady=20)
		return


	def topbar_frame(self,stage):
		subframe = Frame(self)
		labels = list(range(6))
		labels[0] = Label(subframe, text="Start", pad=10)
		labels[1] = Label(subframe, text="Proposed actions", pad=10)
		labels[2] = Label(subframe, text="Executing actions", pad=10)
		labels[3] = Label(subframe, text="Report", pad=10)
		labels[4] = Label(subframe, text="Further actions", pad=10)
		labels[5] = Label(subframe, text="Final report", pad=10)
		labels[stage].configure(font="-weight bold")
		[x.pack(side=LEFT) for x in labels]

		return subframe


	def start_options_frame(self,chosen_dir=None):
		self.p2d = par2deep(chosen_dir)

		self.args = {}

		subframe = Frame(self)

		basicset = LabelFrame(subframe, text="Basic Settings",pad=10)
		basicset.pack(fill=X,pady=(0,20))
		advset = LabelFrame(subframe, text="Advanced Settings",pad=10)
		advset.pack(fill=X)

		def pickdir():
			# self.args["directory"].delete(0,END)
			# self.args["directory"].insert(0,filedialog.askdirectory())
			# self.p2d.__init__(self.args["directory"].get())
			self.new_window(self.topbar_frame(0), self.start_options_frame(filedialog.askdirectory()), self.start_actions_frame())
		Button(basicset, text="Pick directory", command=pickdir).pack(side='left')
		self.args["directory"] = Entry(basicset)
		self.args["directory"].pack(fill=X)
		if chosen_dir == None:
			self.args["directory"].insert(0,self.p2d.args["directory"])
		else:
			self.args["directory"].insert(0,chosen_dir)

		self.args["overwrite"] = IntVar()
		self.args["overwrite"].set(self.p2d.args["overwrite"])
		cb1 = Checkbutton(advset, text="Overwrite all parity data", variable=self.args["overwrite"])
		cb1.pack(fill=X)
		CreateToolTip(cb1,"Any existing parity data found (any *.par* files) will be removed and overwritten.")

		self.args["noverify"] = IntVar()
		self.args["noverify"].set(self.p2d.args["noverify"])
		cb2 = Checkbutton(advset, text="Skip verification", variable=self.args["noverify"])
		cb2.pack(fill=X)
		CreateToolTip(cb2,"Skips verification of files with existing parity data. Use when you only want to create parity data for new files.")

		self.args["keep_old"] = IntVar()
		self.args["keep_old"].set(self.p2d.args["keep_old"])
		cb3 = Checkbutton(advset, text="Keep old parity files or par2 backup files", variable=self.args["keep_old"])
		cb3.pack(fill=X)
		CreateToolTip(cb3,"Do not remove par backup files (*.[0-9]) and do not remove unused parity files (*.par*).")

		Label(advset, text="Exclude directories (comma separated)").pack(fill=X)
		self.args["excludes"] = Entry(advset)
		self.args["excludes"].pack(fill=X)
		self.args["excludes"].insert(0,','.join(self.p2d.args["excludes"]))
		CreateToolTip(self.args["excludes"],"These subdirectories will be excluded from the analysis. Use 'root' for the root of the directory.")

		Label(advset, text="Exclude extensions (comma separated)").pack(fill=X)
		self.args["extexcludes"] = Entry(advset)
		self.args["extexcludes"].pack(fill=X)
		self.args["extexcludes"].insert(0,','.join(self.p2d.args["extexcludes"]))
		CreateToolTip(self.args["extexcludes"],"These extensions will be excluded from the analysis.")

		Label(advset, text="Path to par2.exe").pack(fill=X)
		self.args["par_cmd"] = Entry(advset)
		self.args["par_cmd"].pack(fill=X)
		self.args["par_cmd"].insert(0,self.p2d.args["par_cmd"])
		CreateToolTip(self.args["par_cmd"],"Should be set automatically and correctly, but can be overriden.")

		Label(advset, text="Percentage of protection").pack(fill=X)
		self.args["percentage"] = IntVar()
		self.args["percentage"].set(self.p2d.args["percentage"])
		s1 = Scale(advset,orient=HORIZONTAL,from_=5,to=100,resolution=1,variable=self.args["percentage"])
		s1.pack(fill=X)
		CreateToolTip(s1,"The maximum percentage of corrupted data you will be able to recover from. Higher is safer, but uses more data.")

		return subframe


	def start_actions_frame(self):
		subframe = Frame(self)
		Button(subframe, text="Check directory contents", command=self.set_start_actions).pack()
		return subframe


	def repair_actions_frame(self):
		subframe = Frame(self)
		if self.p2d.len_verified_actions > 0:
			Button(subframe, text="Fix repairable corrupted files and recreate unrepairable files", command=self.repair_action).pack()
			Button(subframe, text="Recreate parity files for the changed and unrepairable files", command=self.recreate_action).pack()
		else:
			Button(subframe, text="Nothing to do. Exit.", command=self.master.destroy).pack()
		return subframe


	def execute_actions_frame(self):
		subframe = Frame(self)
		if self.p2d.len_all_actions > 0:
			Button(subframe, text="Run actions", command=self.execute_actions).pack()
		else:
			Button(subframe, text="Nothing to do. Exit.", command=self.master.destroy).pack()
		return subframe


	def exit_actions_frame(self):
		subframe = Frame(self)
		if hasattr(self.p2d,'len_all_err'):
			Label(subframe, text="There were "+str(self.p2d.len_all_err)+" errors.").pack(fill=X)
		Button(subframe, text="Exit", command=self.master.destroy).pack()
		return subframe


	def exit_frame(self):
		subframe = Frame(self)
		Label(subframe, text="The par2 command you specified is invalid.").pack(fill=X)
		return subframe


	def progress_indef_frame(self):
		subframe = Frame(self)
		self.pb=Progressbar(subframe, mode='indeterminate')
		self.pb.start()
		self.pb.pack(fill=X,expand=True)
		Label(subframe, text="Indexing directory, may take a few moments...").pack(fill=X)
		return subframe


	def progress_frame(self,length):
		subframe = Frame(self)
		self.pb=Progressbar(subframe, mode='determinate',maximum=length)
		self.pb.pack(fill=X,expand=True)
		self.pb_currentfile = StringVar()
		self.pb_currentfile.set("Executing actions, may take a few moments...")
		Label(subframe, textvariable = self.pb_currentfile).pack(fill=X)
		return subframe


	def blank_frame(self):
		subframe = Frame(self)
		return subframe


	def repair_action(self):
		self.new_window(self.topbar_frame(4), self.blank_frame(), self.progress_frame(self.p2d.len_verified_actions))
		self.update()

		self.cnt = 0
		self.cnt_stop = False
		def run():
			for i in self.p2d.execute_repair():
				self.cnt+=1
				self.currentfile = i
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
			self.cnt_stop = True
		thread = threading.Thread(target=run)
		thread.daemon = True
		thread.start()

		def upd():
			if not self.cnt_stop:
				self.pb.step(self.cnt)
				self.pb_currentfile.set("Processing "+os.path.basename(self.currentfile))
				self.cnt=0
				self.master.after(self.waittime, upd)
			else:
				return

		upd()
		return


	def recreate_action(self):
		self.new_window(self.topbar_frame(4), self.blank_frame(), self.progress_frame(self.p2d.len_verified_actions))
		self.update()

		self.cnt = 0
		self.cnt_stop = False
		def run():
			for i in self.p2d.execute_recreate():
				self.cnt+=1
				self.currentfile = i
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
			self.cnt_stop = True
		thread = threading.Thread(target=run)
		thread.daemon = True
		thread.start()

		def upd():
			if not self.cnt_stop:
				self.pb.step(self.cnt)
				self.pb_currentfile.set("Processing "+os.path.basename(self.currentfile))
				self.cnt=0
				self.master.after(self.waittime, upd)
			else:
				return

		upd()
		return


	def set_start_actions(self):
		#update p2d args.
		self.p2d.args["quiet"] = False #has no meaning in gui
		self.p2d.args["overwrite"] = self.args["overwrite"].get() == 1
		self.p2d.args["noverify"] = self.args["noverify"].get() == 1
		self.p2d.args["keep_old"] = self.args["keep_old"].get() == 1
		self.p2d.args["excludes"] = self.args["excludes"].get().split(',') if self.args["excludes"].get().split(',') != [''] else []
		self.p2d.args["extexcludes"] = self.args["extexcludes"].get().split(',') if self.args["extexcludes"].get().split(',') != [''] else []
		self.p2d.args["directory"] = os.path.abspath(self.args["directory"].get())
		self.p2d.args["par_cmd"] = str(self.args["par_cmd"].get())
		self.p2d.args["percentage"] = str(int(self.args["percentage"].get()))

		#go to second frame
		self.new_window(self.topbar_frame(0), self.blank_frame(), self.progress_indef_frame())
		self.update()
		def run():
			if self.p2d.check_state() == 200:
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
		thread = threading.Thread(target=run)
		thread.daemon = True
		thread.start()
		return


	def execute_actions(self):
		#go to third frame
		self.new_window(self.topbar_frame(2), self.blank_frame(), self.progress_frame(self.p2d.len_all_actions))
		self.update()

		self.cnt = 0
		self.cnt_stop = False
		def run():
			for i in self.p2d.execute():
				self.cnt+=1
				self.currentfile = i
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
			self.cnt_stop = True
		thread = threading.Thread(target=run)
		thread.daemon = True
		thread.start()

		def upd():
			if not self.cnt_stop:
				self.pb.step(self.cnt)
				self.pb_currentfile.set("Processing "+os.path.basename(self.currentfile))
				self.cnt=0
				self.master.after(self.waittime, upd)
			else:
				return

		upd()
		return


	def scrollable_treeview_frame(self,nodes={}):
		subframe = Frame(self)
		tree = Treeview(subframe)
		tree.pack(side="left",fill=BOTH,expand=True)

		ysb = Scrollbar(subframe, orient='vertical', command=tree.yview)
		ysb.pack(side="right", fill=Y, expand=False)

		def doubleclick_tree(event):
			self.startfile(tree.item(tree.selection()[0],"text"))
			return

		tree.configure(yscroll=ysb.set)
		tree.heading('#0', text="Actions", anchor='w')
		tree.bind("<Double-1>", doubleclick_tree)

		for node,label in nodes.items():
			if len(getattr(self.p2d,node))==0:
				tree.insert("", 'end', text=label+": no files.", open=False)
			else:
				thing = tree.insert("", 'end', text=label+": expand to see "+str(len(getattr(self.p2d,node)))+" files.", open=False)
				for item in getattr(self.p2d,node):
					if not isinstance(item, list):
						tree.insert(thing, 'end', text=item, open=False)
					else:
						tree.insert(thing, 'end', text=item[0], open=False)

		return subframe


def main():
	root = Tk()
	app = app_frame(root)

	w = 800 # width for the Tk root
	h = 650 # height for the Tk root

	# get screen width and height
	ws = root.winfo_screenwidth() # width of the screen
	hs = root.winfo_screenheight() # height of the screen

	# calculate x and y coordinates for the Tk root window
	x = (ws/2) - (w/2)
	y = (hs/2) - (h/2)

	# set the dimensions of the screen
	# and where it is placed
	root.geometry('%dx%d+%d+%d' % (w, h, x, y))
	root.wm_title("par2deep")

	root.mainloop()

	# if app.p2d.len_all_err>0:
	# 	return 1
	# else:
	# 	return 0

if __name__ == "__main__":
	main()
