import platform,struct,ctypes,os,subprocess,re,glob,shutil
from configargparse import ArgParser
try:
	from Send2Trash import send2trash
except:
	from send2trash import send2trash #package name seem case sensitive. sometimes...

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
	- remove orphans .par2
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
		if chosen_dir == None or not os.path.isdir(chosen_dir):
			current_data_dir = os.getcwd()
			parser = ArgParser(default_config_files=['par2deep.ini', '~/.par2deep'])
		else:
			current_data_dir = os.path.abspath(chosen_dir)
			parser = ArgParser(default_config_files=[os.path.join(current_data_dir,'par2deep.ini'), '~/.par2deep'])

		parser.add_argument("-q", "--quiet", action='store_true', help="Don't asks questions, go with all defaults, including repairing and deleting files (default off).")
		parser.add_argument("-over", "--overwrite", action='store_true', help="Overwrite existing par2 files (default off).")
		parser.add_argument("-novfy", "--noverify", action='store_true', help="Do not verify existing files (default off).")
		parser.add_argument("-keepor", "--keep_orphan", action='store_true', help="Keep orphaned par2 files.")
		#parser.add_argument("-seppardir", "--separate_parity_directory", action='store_true', help="Store parity data in a subdirectory.")
		parser.add_argument("-clean", "--clean_backup", action='store_true', help="Remove backups created by par2 (.1,.2 and so on) from your file tree.")
		parser.add_argument("-ex", "--excludes", action="append", type=str, default=[], help="Optionally excludes directories ('root' is files in the root of -dir).")
		parser.add_argument("-exex", "--extexcludes", action="append", type=str, default=[], help="Optionally excludes file extensions.")
		parser.add_argument("-dir", "--directory", type=str, default=current_data_dir, help="Path to protect (default is current directory).")
		#parser.add_argument("-pardir", "--parity_directory", type=str, default=os.getcwd(), help="Path to parity data store (default is current directory).")
		parser.add_argument("-pc", "--percentage", type=int, default=5, help="Set the parity percentage (default 5%%).")
		parser.add_argument("-pcmd", "--par_cmd", type=str, default="", help="Set path to alternative par2 executable (default \"par2\").")
		
		#lets get a nice dict of all o' that.
		#FIXME: catch unrecognized arguments
		args = {k:v for k,v in vars(parser.parse_args()).items() if v is not None}
		args["nr_parfiles"] = str(1) #number of parity files
		
		#set that shit
		self.args = args
		return


	def runpar(self,command=""):
		if self.includedpar2_works:
			cmdcommand = [self.includedpar2]
		else:
			cmdcommand = [self.par_cmd]
		cmdcommand.extend(command)
		devnull = open(os.devnull, 'wb')
		try:
			subprocess.check_call(cmdcommand,shell=self.shell,stdout=devnull,stderr=devnull)
			return 0
		except subprocess.CalledProcessError as e:
			return e.returncode
		except FileNotFoundError:
			return 200


	def check_state(self):
		for k,v in self.args.items():
			setattr(self, k, v)
		self.percentage = str(self.args["percentage"])
		
		# use builtins if on supported platforms, otherwise fallback to par_cmd, and check if that is working
		_void_ptr_size = struct.calcsize('P')
		bit64 = _void_ptr_size * 8 == 64
		windows = 'windows' in str(platform.system()).lower()
		linux = 'linux' in str(platform.system()).lower()
		macos = 'darwin' in str(platform.system()).lower()
		arm = 'arm' in str(platform.processor()).lower()
		
		self.shell=False
		if windows:
			self.shell=True #shell true because otherwise pythonw.exe pops up a window for every par2 action!
		
		self.includedpar2_works = False
		if os.path.isfile(self.args["par_cmd"]):
			self.par_cmd = self.args["par_cmd"]
		else:
			#pcmd not set by user, so lets see if we can use libpar2
			if bit64:
				this_script_dir = os.path.dirname(os.path.abspath(__file__))
				if windows:
					try:
						os.add_dll_directory(this_script_dir) #needed on python3.8 on win
					except:
						pass #not available or necesary on py37 and before
					ppath = os.path.join(this_script_dir,"par2.exe")
					if os.path.exists(ppath):
						self.includedpar2 = ppath
						self.includedpar2_works = True
				elif linux:
					if arm:
						ppath = os.path.join(this_script_dir,"par2cmdline-turbo-v1.1.1-linux-arm64")
						if os.path.exists(ppath):
							self.includedpar2 = ppath
							self.includedpar2_works = True
					else:
						ppath = os.path.join(this_script_dir,"par2cmdline-turbo-v1.1.1-linux-amd64")
						if os.path.exists(ppath):
							self.includedpar2 = ppath
							self.includedpar2_works = True
				elif macos:
					if arm:
						ppath = os.path.join(this_script_dir,"par2cmdline-turbo-v1.1.1-macos-arm64")
						if os.path.exists(ppath):
							self.includedpar2 = ppath
							self.includedpar2_works = True
					else:
						ppath = os.path.join(this_script_dir,"par2cmdline-turbo-v1.1.1-macos-x64")
						if os.path.exists(ppath):
							self.includedpar2 = ppath
							self.includedpar2_works = True
				else: #otheros
					pass
			else: #bit32
				pass
			if self.includedpar2_works == False:
				#use par2 in path.
				if windows:
					self.par_cmd = 'par2.exe'
				else:
					self.par_cmd = 'par2'
		# now test
		if not self.includedpar2_works and self.runpar() == 200:
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

		backups_delete = []
		backups_keep = [f for f in allfiles if f.endswith(tuple(['.'+str(i) for i in range(0,10)])) and f[:-2] in allfiles] #even though we wont create more backups than max_keep_backups, we'll check up to .9 for existence. we include .0, which is what par2deep created for verifiedfiles_repairable that was recreated anyway.
		allfiles = [f for f in allfiles if f not in backups_keep] #update allfiles with the opposite.

		parrables = [f for f in allfiles if not f.endswith((".par2",".par2deep_tmpfile"))]

		pattern = '.+vol[0-9]+\+[0-9]+\.par2'
		par2corrfiles = [f for f in allfiles if re.search(pattern, f)]
		par2files = [f for f in allfiles if f.endswith(".par2") and not re.search(pattern, f)]

		if self.clean_backup:
			backups_delete = [i for i in backups_keep]
			backups_keep = []

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

		orphans_delete = []
		orphans_keep = []
		#print("Checking for orphans par2 files ...")
		for f in par2files:
			if not os.path.isfile(f[:-5]):
				if self.keep_orphan:
					orphans_keep.append(f)
				else:
					orphans_delete.append(f)
		for f in par2corrfiles:
			if not os.path.isfile(f.split('.vol')[0]):
				if self.keep_orphan:
					orphans_keep.append(f)
				else:
					orphans_delete.append(f)
		backups_delete.extend([f for f in allfiles if f.endswith(".par2deep_tmpfile")])

		self.create = sorted(create)
		self.incomplete = sorted(incomplete)
		self.verify = sorted(verify)
		self.orphans_delete = sorted(orphans_delete)
		self.backups_delete = sorted(backups_delete)
		self.orphans_keep = sorted(orphans_keep)
		self.backups_keep = sorted(backups_keep)

		self.parrables = sorted(parrables)
		self.par2corrfiles = sorted(par2corrfiles)
		self.par2files = sorted(par2files)

		self.len_all_actions = len(create) + len(incomplete) + len(verify) + len(orphans_delete) + len(backups_delete)

		return


	def execute(self):
		create = self.create
		incomplete = self.incomplete
		verify = self.verify
		orphans_delete = self.orphans_delete
		backups_delete = self.backups_delete

		create.extend(incomplete)

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
			100: "send2trash succeeded.",
			101: "send2trash did not succeed.",
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
					send2trash(p)
					#par2 does not delete preexisting parity data, so delete any possible data.
				createdfiles.append([ f , self.runpar(["c","-r"+self.percentage,"-n"+self.nr_parfiles,f]) ])
			createdfiles_err=[ [i,j] for i,j in createdfiles if j != 0 and j != 100 ]

		verifiedfiles=[]
		verifiedfiles_succes=[]
		verifiedfiles_err=[]
		verifiedfiles_repairable=[]
		if not self.noverify and not self.overwrite and len(verify)>0:
			#print('Verifying ...')
			for f in verify:
				yield f
				verifiedfiles.append([ f , self.runpar(["v",f]) ])
			verifiedfiles_err=[ [i,j] for i,j in verifiedfiles if j != 0 and j != 100 and j != 1 ]
			verifiedfiles_repairable=[ [i,j] for i,j in verifiedfiles if j == 1 ]
			verifiedfiles_succes=[ [i,j] for i,j in verifiedfiles if j == 0 ]

		removedfiles=[]
		removedfiles_err=[]
		if len(orphans_delete)>0:
			#print('Removing ...')
			for f in orphans_delete:
				yield f
				if os.path.isfile(f): # so send2trash always succeeds and returns None
					send2trash(f)
					removedfiles.append([ f , 100 ])
				else:
					removedfiles.append([ f , 101 ])
			removedfiles_err=[ [i,j] for i,j in removedfiles if j !=0 and j != 100 ]
		if len(backups_delete)>0:
			#print('Removing ...')
			for f in backups_delete:
				yield f
				if os.path.isfile(f): # so send2trash always succeeds and returns None
					send2trash(f)
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
				retval = self.runpar(["r",f])
				if retval == 0:
					if self.clean_backup:
						#backups should just have been cleaned in the execute phase and therefore a .1 been created.
						backupfile=f+".1"
						if os.path.isfile(backupfile):
							send2trash(backupfile)
				repairedfiles.append([ f , retval ])
			
			for f,retcode in self.verifiedfiles_err:
				yield f
				pars = glob.glob(glob.escape(f)+'*.par2')
				for p in pars:
					send2trash(p)
				recreatedfiles.append([ f , self.runpar(["c","-r"+self.percentage,"-n"+self.nr_parfiles,f]) ])

		self.recreate = sorted(recreatedfiles)
		self.recreate_err = sorted([f for f,err in recreatedfiles if err !=0])
		self.fixes = sorted([f for f,err in repairedfiles if err ==0])
		self.fixes_err = sorted([f for f,err in repairedfiles if err !=0])

		self.len_all_err = self.len_all_err + len(self.recreate_err) + len(self.fixes_err)

		return


	def execute_recreate(self):
		recreatedfiles=[]
		# we recreate everything, including repairables. we do create a backup for the repairables
		
		if self.len_verified_actions>0:
			for f,retcode in self.verifiedfiles_repairable:
				yield f
				if not self.clean_backup:
					# first, copy the repairable file, we need it later
					ftmp = f+".par2deep_tmpfile"
					shutil.copyfile(f,ftmp)
					# now that we have a backup of the repairable, repair to obtain the actual backup we want.
					retval = self.runpar(["r",f])
					if retval == 0:
						# f is now the file we actually want to backup.
						shutil.copyfile(f,f+".0") # will overwrite acc. to docs
						# the last .[0-9] is the copy par2 just made, let's delete it.
						for nbr in range(1,10):
							# we dont know how many backups were on disk, up to 10 just in case
							if not os.path.isfile(f+"."+str(nbr)):
								# we overshot by 1
								os.remove(f+"."+str(nbr-1))
								break
					elif retval != 0:
						# making the backup failed, no need to move it. we don't report it anywhere, nothing we can do to handle.
						# we made ftmp and did not rely on par2's backup in case the repair was attempted but failed.
						# probably never happens, but you can never be too certain
						pass
					# regardless of retval, we put ftmp back to f. this is the file we want to recreate for.
					os.replace(ftmp,f)
				# same as verifiedfiles_err
				pars = glob.glob(glob.escape(f)+'*.par2')
				for p in pars:
					send2trash(p)
				recreatedfiles.append([ f , self.runpar(["c","-r"+self.percentage,"-n"+self.nr_parfiles,f]) ])
			
			for f,retcode in self.verifiedfiles_err:
				yield f
				pars = glob.glob(glob.escape(f)+'*.par2')
				for p in pars:
					send2trash(p)
				recreatedfiles.append([ f , self.runpar(["c","-r"+self.percentage,"-n"+self.nr_parfiles,f]) ])

		self.recreate = sorted(recreatedfiles)
		self.recreate_err = sorted([f for f,err in recreatedfiles if err !=0])
		self.fixes = []
		self.fixes_err = []

		self.len_all_err = self.len_all_err + len(self.recreate_err)

		return
