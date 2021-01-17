import sys,pprint,enum,struct,ctypes,os,subprocess,re,glob,shutil
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
fourth, ask to repair if possible/necessary.
fifth, final report.
'''

class errorcodes(enum.IntEnum):
	SUCCESS = 0 # "Success.", #can mean no error, but also successfully repaired!
	REPAIRABLE = 1 # "Repairable damage found.",
	IRREPAIRABLE = 2 # "Irreparable damage found.",
	INVALIDARGS = 3 # "Invalid commandline arguments.",
	UNUSABLE = 4 # "Parity file unusable.",
	FAIL = 5 # "Repair failed.",
	IO = 6 # "IO error.",
	INTERNAL = 7 # "Internal error",
	OOM = 8 # "Out of memory.",
	SEND2TRASH_OK = 100 # "send2trash succeeded.",
	SEND2TRASH_FAIL = 101 # "send2trash did not succeed.",
	NOTFOUND = 127 # "par2 command not found."


class par2deep():
	def __init__(self,chosen_dir=None):
		#CMD arguments and configfile
		if chosen_dir == None or not os.path.isdir(chosen_dir):
			current_data_dir = os.getcwd()
			parser = ArgParser(default_config_files=['par2deep.ini', '~/.par2deep'])
		else:
			current_data_dir = os.path.abspath(chosen_dir)
			parser = ArgParser(default_config_files=[os.path.join(current_data_dir,'par2deep.ini'), '~/.par2deep'])

		parser.add_argument("-q", "--quiet", action='store_true', help="Don't asks questions, go with all defaults, including repairing and deleting files.")
		parser.add_argument("-over", "--overwrite", action='store_true', help="Overwrite existing par2 files.")
		parser.add_argument("-novfy", "--noverify", action='store_true', help="Do not verify existing files.")
		parser.add_argument("-keepor", "--keep_orphan", action='store_true', help="Keep orphaned par2 files.")
		parser.add_argument("-clean", "--clean_backup", action='store_true', help="Remove backups created by par2 (.1,.2 and so on) from your file tree.")
		parser.add_argument("-ex", "--excludes", action="append", type=str, default=[], help="Optionally excludes directories ('root' is files in the root of -dir).")
		parser.add_argument("-exex", "--extexcludes", action="append", type=str, default=[], help="Optionally excludes file extensions.")
		parser.add_argument("-dir", "--directory", type=str, default=current_data_dir, help="Path to protect (default is current directory).")
		parser.add_argument("-parsubdir", "--parity_subdirectory", action='store_true', help="Path to parity data store ($dir/parity).") #for now hardcode
		parser.add_argument("-pc", "--percentage", type=int, default=5, help="Set the parity percentage (default 5%%).")
		parser.add_argument("-pcmd", "--par_cmd", type=str, default="", help="Set path to alternative par2 executable (default built-in library or \"par2\" in path).")

		#lets get a nice dict of all o' that.
		#FIXME: catch unrecognized arguments
		args = {k:v for k,v in vars(parser.parse_args()).items() if v is not None}

		#constants
		args["nr_parfiles"] = 1 #number of parity files
		args["parity_subdirectory_dir"] = "parity"

		#set that shit
		self.args = args
		return


	def getblocksizecount(self,filename):
		f_size = os.path.getsize(filename)
		blocksize_min = f_size//2**15 # size can never be below this
		blocksize_f = (f_size*self.percentage)//100
		blockcount_max = 2**7-1 #some logic to keep blockcount and overhead for small files under control
		if f_size < 1e6:
			blockcount_max = 2**3-1
		elif f_size < 4e6:
			blockcount_max = 2**4-1
		elif f_size < 20e6:
			blockcount_max = 2**5-1
		if blocksize_f > blocksize_min:
			blockcount = min(blockcount_max,blocksize_f//blocksize_min)
			blocksize = blocksize_f/blockcount
		else:
			blockcount = 1
			blocksize = blocksize_min
		blocksize = (blocksize//4+1)*4 #make multiple of 4
		return int(blocksize),int(blockcount)


	def runpar(self,command=""):
		if self.libpar2_works:
			def strlist2charpp(stringlist):
				argc = len(stringlist)
				Args = ctypes.c_char_p * (len(stringlist)+1)
				argv = Args(*[ctypes.c_char_p(arg.encode("utf-8")) for arg in stringlist])
				return argc,argv
			return self.libpar2.par2cmdline(*strlist2charpp(command))
		else:
			cmdcommand = [self.par_cmd]
			cmdcommand.extend(command)
			devnull = open(os.devnull, 'wb')
			try:
				subprocess.check_call(cmdcommand,shell=self.shell)#,stdout=devnull,stderr=devnull)
				return errorcodes.SUCCESS
			except subprocess.CalledProcessError as e:
				return e.returncode
			except FileNotFoundError:
				return errorcodes.NOTFOUND


	def init_par_cmd(self):
		## first, set possibly changed self.args
		pprint.pprint(self.args)
		for k,v in self.args.items():
			setattr(self, k, v)

		#we provide a win64 and lin64 library, use if on those platforms, otherwise fallback to par_cmd, and check if that is working
		_void_ptr_size = struct.calcsize('P')
		bit64 = _void_ptr_size * 8 == 64
		windows = 'win32' in str(sys.platform).lower()
		linux = 'linux' in str(sys.platform).lower()
		macos = 'darwin' in str(sys.platform).lower()

		self.shell=False
		if windows:
			self.shell=True #shell true because otherwise pythonw.exe pops up a window for every par2 action!

		self.libpar2_works = False

		if self.args["par_cmd"]:
			if shutil.which(self.args["par_cmd"]):
				self.par_cmd = self.args["par_cmd"]
				return errorcodes.SUCCESS
			else:
				return errorcodes.NOTFOUND
		else:
			#pcmd not set by user, so lets see if we can use builtin libpar2 or par2
			if bit64:
				this_script_dir = os.path.dirname(os.path.abspath(__file__))
				if windows:
					try:
						os.add_dll_directory(this_script_dir) #needed on python3.8 on win
					except:
						pass #not available or necesary on py37 and before
					try:
						self.libpar2 = ctypes.CDLL(os.path.join(this_script_dir,"libpar2.dll"))
						self.libpar2_works = True
					except:
						pass
				elif linux:
					try:
						self.libpar2 = ctypes.CDLL(os.path.join(this_script_dir,"libpar2.so"))
						self.libpar2_works = True
					except:
						pass
				elif macos:
					pass #TODO, hope somebody can contribute
				else: #otheros
					pass
			else: #bit32
				pass
			if self.libpar2_works == False:
				#use par2 in path.
				if windows:
					self.par_cmd = 'par2.exe'
				else:
					self.par_cmd = 'par2'
			# now test
			if not self.libpar2_works and self.runpar() == errorcodes.NOTFOUND:
				return errorcodes.NOTFOUND
			else:
				return errorcodes.SUCCESS


	def get_parf(self,fname,ext='.par2'):
		# if self.parity_subdirectory:
		# 	return os.path.join(self.parity_directory,os.path.relpath(fname,self.directory)+ext)
		# else:
		# 	return fname+ext
		print("get_parf",os.path.relpath(fname,self.directory)+ext)
		return os.path.relpath(fname,self.directory)+ext


	def get_f(self,parfname):
		# if parfname.endswith('.par2'):
		# 	return parfname[:-5].replace(self.parity_directory,self.directory)
		# else:
		# 	return parfname.replace(self.parity_directory,self.directory)
		print("get_f",parfname)
		if parfname.endswith('.par2'):
			return parfname[:-5]#.replace(self.parity_directory,self.directory)
		else:
			return parfname#.replace(self.parity_directory,self.directory)


	def get_parf_glob(self,fname,ext='*.par2'):
		return glob.glob(glob.escape(self.get_parf(fname,''))+ext)


	def set_state(self):
		# self.directory = os.path.abspath(self.directory)
		self.parity_directory = self.directory
		if self.parity_subdirectory:
			self.parity_directory=os.path.join(self.directory,self.parity_subdirectory_dir)

		allfiles = [f for f in glob.glob(os.path.join(self.directory,"**","*"), recursive=True) if os.path.isfile(f)] #not sure why required, but glob may introduce paths...

		if self.parity_subdirectory:
			allfiles = [f for f in allfiles if self.parity_directory not in f] #remove parity dir if we use a subdir

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
		if self.parity_subdirectory:
			parity_subdirectory_glob = glob.glob(os.path.join(self.parity_directory,"**","*.par2"), recursive=True)
			par2files = [f for f in parity_subdirectory_glob if os.path.isfile(f) and f.endswith(".par2") and not re.search(pattern, f)]
			par2corrfiles = [f for f in parity_subdirectory_glob if re.search(pattern, f)]
		else:
			par2files = [f for f in allfiles if f.endswith(".par2") and not re.search(pattern, f)]
			par2corrfiles = [f for f in allfiles if re.search(pattern, f)]

		if self.clean_backup:
			backups_delete = [i for i in backups_keep]
			backups_keep = []

		create = []
		verify = []
		incomplete = []
		#print("Checking files for parrability ...")
		for f in parrables:
			# check if both or one of the par files is missing
			ispar = os.path.isfile(self.get_parf(f))
			isvolpar = len(self.get_parf_glob(f,".vol*.par2")) > 0
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
		for parf in par2files:
			if not os.path.isfile(self.get_f(parf)):
				if self.keep_orphan:
					orphans_keep.append(parf)
				else:
					orphans_delete.append(parf)
		for parf in par2corrfiles:
			if not os.path.isfile(self.get_f(parf.split('.vol')[0])):
				if self.keep_orphan:
					orphans_keep.append(parf)
				else:
					orphans_delete.append(parf)
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

		createdfiles=[]
		createdfiles_err=[]
		if len(create)>0:
			#print('Creating ...')
			for f in create:
				yield f
				parf = self.get_parf(f)
				pars = self.get_parf_glob(f)
				for p in pars:
					send2trash(p)
					#par2 does not delete preexisting parity data, so delete any possible data.
				blocksize,blockcount = self.getblocksizecount(f)
				createdfiles.append([ f ,
										self.runpar(["c",
										"-s",str(blocksize),
										"-c",str(blockcount),
										#"-B"+os.path.dirname(f),
										parf,
										f
										])
									])
			createdfiles_err=[ [i,j] for i,j in createdfiles
										if j != errorcodes.SUCCESS
										and j != errorcodes.SEND2TRASH_OK ]

		verifiedfiles=[]
		verifiedfiles_success=[]
		verifiedfiles_err=[]
		verifiedfiles_repairable=[]
		if not self.noverify and not self.overwrite and len(verify)>0:
			#print('Verifying ...')
			for f in verify:
				yield f
				parf = self.get_parf(f)
				print(self.directory,parf,f)
				verifiedfiles.append([ f ,
										self.runpar(["v",
										#"-B"+os.path.dirname(f),
										parf,
										f
										])
									])
			verifiedfiles_err=[ [i,j] for i,j in verifiedfiles
										if j != errorcodes.SUCCESS
										and j != errorcodes.SEND2TRASH_OK
										and j != errorcodes.REPAIRABLE ]
			verifiedfiles_repairable=[ [i,j] for i,j in verifiedfiles
										if j == errorcodes.REPAIRABLE ]
			verifiedfiles_success=[ [i,j] for i,j in verifiedfiles
										if j == errorcodes.SUCCESS ]
		removedfiles=[]
		removedfiles_err=[]
		if len(orphans_delete)>0:
			#print('Removing ...')
			for f in orphans_delete:
				yield f
				if os.path.isfile(f): # so send2trash always succeeds and returns None
					send2trash(f)
					removedfiles.append([ f , errorcodes.SEND2TRASH_OK ])
				else:
					removedfiles.append([ f , errorcodes.SEND2TRASH_FAIL ])
			removedfiles_err=[ [i,j] for i,j in removedfiles
										if j != errorcodes.SUCCESS
										and j != errorcodes.SEND2TRASH_OK ]
		if len(backups_delete)>0:
			#print('Removing ...')
			for f in backups_delete:
				yield f
				if os.path.isfile(f): # so send2trash always succeeds and returns None
					send2trash(f)
					removedfiles.append([ f , errorcodes.SEND2TRASH_OK ])
				else:
					removedfiles.append([ f , errorcodes.SEND2TRASH_FAIL ])
			removedfiles_err=[ [i,j] for i,j in removedfiles
										if j != errorcodes.SUCCESS
										and j != errorcodes.SEND2TRASH_OK ]

		self.createdfiles=createdfiles
		self.verifiedfiles_success=verifiedfiles_success
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
				parf = self.get_parf(f)
				retval = self.runpar(["r",
										#"-B"+os.path.dirname(f),
										parf,
										f])
				if retval == errorcodes.SUCCESS:
					if self.clean_backup:
						#backups should just have been cleaned in the execute phase and therefore a .1 been created.
						backupfile=f+".1"
						if os.path.isfile(backupfile):
							send2trash(backupfile)
				repairedfiles.append([ f , retval ])

			for f,retcode in self.verifiedfiles_err:
				yield f
				parf = self.get_parf(f)
				pars = self.get_parf_glob(f)
				for p in pars:
					send2trash(p)
				blocksize,blockcount = self.getblocksizecount(f)
				recreatedfiles.append([ f ,
										self.runpar(["c",
										"-s",str(blocksize),
										"-c",str(blockcount),
										#"-B"+os.path.dirname(f),
										parf,
										f
										])
									])

		self.recreate = sorted(recreatedfiles)
		self.recreate_err = sorted([f for f,err in recreatedfiles if err != errorcodes.SUCCESS])
		self.fixes = sorted([f for f,err in repairedfiles if err == errorcodes.SUCCESS])
		self.fixes_err = sorted([f for f,err in repairedfiles if err != errorcodes.SUCCESS])

		self.len_all_err = self.len_all_err + len(self.recreate_err) + len(self.fixes_err)

		return


	def execute_recreate(self):
		recreatedfiles=[]
		# we recreate everything, including repairables. we do create a backup for the repairables

		if self.len_verified_actions>0:
			for f,retcode in self.verifiedfiles_repairable:
				yield f
				parf = self.get_parf(f)
				if not self.clean_backup:
					# first, copy the repairable file, we need it later
					ftmp = f+".par2deep_tmpfile"
					shutil.copyfile(f,ftmp)
					# now that we have a backup of the repairable, repair to obtain the actual backup we want.
					retval = self.runpar(["r",
										#"-B"+os.path.dirname(f),
										parf,
										f])
					if retval == errorcodes.SUCCESS:
						# f is now the file we actually want to backup.
						shutil.copyfile(f,f+".0") # will overwrite acc. to docs
						# the last .[0-9] is the copy par2 just made, let's delete it.
						for nbr in range(1,10):
							# we dont know how many backups were on disk, up to 10 just in case
							if not os.path.isfile(f+"."+str(nbr)):
								# we overshot by 1
								os.remove(f+"."+str(nbr-1))
								break
					elif retval != errorcodes.SUCCESS:
						# making the backup failed, no need to move it. we don't report it anywhere, nothing we can do to handle.
						# we made ftmp and did not rely on par2's backup in case the repair was attempted but failed.
						# probably never happens, but you can never be too certain
						pass
					# regardless of retval, we put ftmp back to f. this is the file we want to recreate for.
					os.replace(ftmp,f)
				# same as verifiedfiles_err
				pars = self.get_parf_glob(f)
				for p in pars:
					send2trash(p)
				blocksize,blockcount = self.getblocksizecount(f)
				recreatedfiles.append([ f ,
										self.runpar(["c",
										"-s",str(blocksize),
										"-c",str(blockcount),
										#"-B"+os.path.dirname(f),
										parf,
										f
										])
									])

			for f,retcode in self.verifiedfiles_err:
				yield f
				parf = self.get_parf(f)
				pars = self.get_parf_glob(f)
				for p in pars:
					send2trash(p)
				blocksize,blockcount = self.getblocksizecount(f)
				recreatedfiles.append([ f ,
										self.runpar(["c",
										"-s",str(blocksize),
										"-c",str(blockcount),
										#"-B"+os.path.dirname(f),
										parf,
										f
										])
									])

		self.recreate = sorted(recreatedfiles)
		self.recreate_err = sorted([f for f,err in recreatedfiles if err != errorcodes.SUCCESS])
		self.fixes = []
		self.fixes_err = []

		self.len_all_err = self.len_all_err + len(self.recreate_err)

		return
