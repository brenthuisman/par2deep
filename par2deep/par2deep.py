import sys,os,subprocess,re,glob
from configargparse import ArgParser

'''
first, init disk state.
second, depending on overrides, propose actions and ask user confirmation
	- create if not exist
		- file but no .par2
		- override = create even .par exist
			- file and .par2
	- verify if exist
		- file and .par2
		- override = no verify if .par2 exist
	- remove unused .par2
		- no file but .par2
		- override = dont remove .par2 if no file
third, execute user choices.
	- these _execute function are iterable through yield, which is done at the start of the loop such that we know what the current file being worked on is.
fourth, ask to repair if possible/necesary.
fifth, final report.
'''

class par2deep():
	def __init__(self,chosen_dir=None):
		#CMD arguments and configfile
		if sys.platform == 'win32':
			self.shell=True
			locs = [os.path.join(sys.path[0],'phpar2.exe'),
					'phpar2.exe',
					os.path.join(sys.path[0],'par2.exe'),
					'par2.exe',
					]
			par_cmd = 'par2'
			for p in locs:
				if os.path.isfile(p):
					par_cmd = p
					break
		else:
			self.shell=False
			par_cmd = 'par2'

		if chosen_dir == None:
			parser = ArgParser(default_config_files=['par2deep.ini', '~/.par2deep'])
		else:
			parser = ArgParser(default_config_files=[os.path.join(chosen_dir,'par2deep.ini'), '~/.par2deep'])

		parser.add_argument("-q", "--quiet", action='store_true', help="Don't asks questions, go with all defaults, including repairing and deleting files (default off).")
		parser.add_argument("-over", "--overwrite", action='store_true', help="Overwrite existing par2 files (default off).")
		parser.add_argument("-novfy", "--noverify", action='store_true', help="Do not verify existing files (default off).")
		parser.add_argument("-keep", "--keep_old", action='store_true', help="Keep unused par2 files and old par2 repair files (.1,.2 and so on).")
		parser.add_argument("-ex", "--excludes", action="append", type=str, default=[], help="Optionally excludes directories ('root' is files in the root of -dir).")
		parser.add_argument("-exex", "--extexcludes", action="append", type=str, default=[], help="Optionally excludes file extensions.")
		parser.add_argument("-dir", "--directory", type=str, default=os.getcwd(), help="Path to operate on (default is current directory).")
		parser.add_argument("-pc", "--percentage", type=int, default=5, help="Set the parity percentage (default 5%%).")
		parser.add_argument("-pcmd", "--par_cmd", type=str, default=par_cmd, help="Set path to alternative par2 command (default \"par2\").")
		
		#lets get a nice dict of all o' that.
		args = {k:v for k,v in vars(parser.parse_args()).items() if v is not None}
		self.args = args

		#add number of files
		args["nr_parfiles"] = str(1) #number of parity files

		#set that shit
		for k,v in self.args.items():
			setattr(self, k, v)

		return


	def runpar(self,command):
		devnull = open(os.devnull, 'wb')
		#shell true because otherwise pythonw.exe pops up a cmd.exe for EVERY file.
		try:
			subprocess.check_call(command,shell=self.shell,stdout=devnull,stderr=devnull)
			return 0
		except subprocess.CalledProcessError as e:
			return e.returncode
		except FileNotFoundError:
			return 200


	def check_state(self):
		#set that shit if changed in gui
		for k,v in self.args.items():
			setattr(self, k, v)
		self.percentage = str(self.percentage)
		
		if self.runpar([self.par_cmd]) == 200:
			return 200
			#if 200, then par2 doesnt exist.

		allfiles = [f for f in glob.glob(os.path.join(self.directory,"**","*"), recursive=True) if os.path.isfile(f)] #not sure why required, but glob may introduce paths...

		if 'root' in self.excludes:
			allfiles = [f for f in allfiles if os.path.dirname(f) != self.directory]
			self.excludes.remove('root')
		for excl in self.excludes:
			allfiles = [f for f in allfiles if not f.startswith(os.path.join(self.directory,excl))]
		for ext in self.extexcludes:
			allfiles = [f for f in allfiles if not f.endswith(ext)]

		parrables = [f for f in allfiles if not f.endswith(".par2")]

		pattern = '.+vol[0-9]+\+[0-9]+\.par2'
		par2corrfiles = [f for f in allfiles if re.search(pattern, f)]
		par2files = [f for f in allfiles if f.endswith(".par2") and not re.search(pattern, f)]

		par2errcopies = [f for f in allfiles if f.endswith(".1") or f.endswith(".2")] #remove copies with errors fixed previously by par.

		create = []
		verify = []
		incomplete = []
		#print("Checking files for parrability ...")
		for f in parrables:
			# check if both or one of the par files is missing
			ispar = os.path.isfile(f+".par2")
			isvolpar = len(glob.glob(glob.escape(f)+".vol*.par2")) > 0
			if self.overwrite:
				create.append(f)
			elif not ispar and not isvolpar:
				#both missing
				create.append(f)
			elif not self.noverify and ispar and isvolpar:
				#both present
				verify.append(f)
			elif self.noverify and ispar and isvolpar:
				#both present, but noverify is on, so no action
				pass
			else:
				#one of them is missing but not both
				incomplete.append(f)

		unused = []
		if not self.keep_old:
			#print("Checking for unused par2 files ...")
			for f in par2files:
				if not os.path.isfile(f[:-5]):
					unused.append(f)
			for f in par2corrfiles:
				if not os.path.isfile(f.split('.vol')[0]):
					unused.append(f)

		self.create = sorted(create)
		self.incomplete = sorted(incomplete)
		self.verify = sorted(verify)
		self.unused = sorted(unused)
		self.par2errcopies = sorted(par2errcopies)

		self.parrables = sorted(parrables)
		self.par2corrfiles = sorted(par2corrfiles)
		self.par2files = sorted(par2files)

		self.len_all_actions = len(create) + len(incomplete) + len(verify) + len(unused) + len(par2errcopies)

		return


	def execute(self):
		create = self.create
		incomplete = self.incomplete
		verify = self.verify
		unused = self.unused

		create.extend(incomplete)
		unused.extend(self.par2errcopies)

		errorcodes = {
			0: "Succes.", #can mean no error, but also succesfully repaired!
			1: "Repairable damage found.",
			2: "Irreparable damage found.",
			3: "Invalid commandline arguments.",
			4: "Parity file unusable.",
			5: "Repair failed.",
			6: "IO error.",
			7: "Internal error",
			8: "Out of memory.",
			100: "os.remove succeeded.",
			101: "os.remove did not succeed.",
			200: "par2 command not found."
		}

		createdfiles=[]
		createdfiles_err=[]
		if len(create)>0:
			#print('Creating ...')
			for f in create:
				yield f
				pars = glob.glob(glob.escape(f)+'*.par2')
				for p in pars:
					os.remove(p)
				createdfiles.append([ f , self.runpar([self.par_cmd,"c","-r"+self.percentage,"-n"+self.nr_parfiles,f]) ])
			createdfiles_err=[ [i,j] for i,j in createdfiles if j != 0 and j != 100 ]

		verifiedfiles=[]
		verifiedfiles_succes=[]
		verifiedfiles_err=[]
		verifiedfiles_repairable=[]
		if not self.noverify and not self.overwrite and len(verify)>0:
			#print('Verifying ...')
			for f in verify:
				yield f
				verifiedfiles.append([ f , self.runpar([self.par_cmd,"v",f]) ])
			verifiedfiles_err=[ [i,j] for i,j in verifiedfiles if j != 0 and j != 100 and j != 1 ]
			verifiedfiles_repairable=[ [i,j] for i,j in verifiedfiles if j == 1 ]
			verifiedfiles_succes=[ [i,j] for i,j in verifiedfiles if j == 0 ]

		removedfiles=[]
		removedfiles_err=[]
		if not self.keep_old and len(unused)>0:
			#print('Removing ...')
			for f in unused:
				yield f
				if os.path.isfile(f): # so os.remove always succeeds and returns None
					os.remove(f)
					removedfiles.append([ f , 100 ])
				else:
					removedfiles.append([ f , 101 ])
			removedfiles_err=[ [i,j] for i,j in removedfiles if j !=0 and j != 100 ]

		self.createdfiles=createdfiles
		self.verifiedfiles_succes=verifiedfiles_succes
		self.removedfiles=removedfiles

		self.createdfiles_err=createdfiles_err
		self.verifiedfiles_err=verifiedfiles_err
		self.verifiedfiles_repairable=verifiedfiles_repairable
		self.removedfiles_err=removedfiles_err

		self.len_all_err = len(self.createdfiles_err)+len(self.verifiedfiles_err)+len(self.verifiedfiles_repairable)+len(self.removedfiles_err)
		self.len_verified_actions = len(self.verifiedfiles_err)+len(self.verifiedfiles_repairable)

		return


	def execute_repair(self):
		repairedfiles=[]
		recreatedfiles=[]
		if self.len_verified_actions>0:
			for f,retcode in self.verifiedfiles_repairable:
				yield f
				retval = self.runpar([self.par_cmd,"r",f])
				if retval == 0:
					if not self.keep_old and os.path.isfile(f+".1"):
						os.remove(f+".1")
					repairedfiles.append([ f , retval ])
			for f,retcode in self.verifiedfiles_err:
				yield f
				pars = glob.glob(glob.escape(f)+'*.par2')
				for p in pars:
					os.remove(p)
				recreatedfiles.append([ f , self.runpar([self.par_cmd,"c","-r"+self.percentage,"-n"+self.nr_parfiles,f]) ])

		self.recreate = sorted(recreatedfiles)
		self.recreate_err = sorted([f for f,err in recreatedfiles if err !=0])
		self.fixes = sorted([f for f,err in repairedfiles if err ==0])
		self.fixes_err = sorted([f for f,err in repairedfiles if err !=0])

		self.len_all_err = self.len_all_err + len(self.recreate_err) + len(self.fixes_err)

		return


	def execute_recreate(self):
		repairedfiles=[]
		recreatedfiles=[]
		if self.len_verified_actions>0:
			for f,retcode in self.verifiedfiles_repairable+self.verifiedfiles_err:
				yield f
				pars = glob.glob(glob.escape(f)+'*.par2')
				for p in pars:
					os.remove(p)
				recreatedfiles.append([ f , self.runpar([self.par_cmd,"c","-r"+self.percentage,"-n"+self.nr_parfiles,f]) ])

		self.recreate = sorted(recreatedfiles)
		self.recreate_err = sorted([f for f,err in recreatedfiles if err !=0])
		self.fixes = sorted([f for f,err in repairedfiles if err ==0])
		self.fixes_err = sorted([f for f,err in repairedfiles if err !=0])

		self.len_all_err = self.len_all_err + len(self.recreate_err) + len(self.fixes_err)

		return
