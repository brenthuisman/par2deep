import sys,os,subprocess,re,glob
from collections import Counter
from .ask_yn import ask_yn
from tqdm import tqdm
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
fourth, ask to repair if possible/necesary.
fifth, final report.
'''

def main():
	#CMD arguments and configfile
	parser = ArgParser(default_config_files=['par2deep.ini', '~/.par2deep'])

	parser.add_argument("-q", "--quiet", action='store_true', help="Don't asks questions, go with all defaults, including repairing and deleting files (default off).")
	parser.add_argument("-over", "--overwrite", action='store_true', help="Overwrite existing par2 files (default off).")
	parser.add_argument("-novfy", "--noverify", action='store_true', help="Do not verify existing files (default off).")
	parser.add_argument("-keep", "--keep_old", action='store_true', help="Keep unused par2 files and old par2 repair files (.1,.2 and so on).")
	parser.add_argument("-ex", "--excludes", action="append", type=str, default=[], help="Optionally excludes directories ('root' is files in the root of -dir).")
	parser.add_argument("-exex", "--extexcludes", action="append", type=str, default=[], help="Optionally excludes file extensions.")
	parser.add_argument("-dir", "--directory", type=str, default=os.getcwd(), help="Path to operate on (default is current directory).")
	parser.add_argument("-pc", "--percentage", type=int, default=5, help="Set the parity percentage (default 5%%).")
	parser.add_argument("-pcmd", "--par_cmd", type=str, default="par2", help="Set path to alternative par2 command (default \"par2\").")
	args = parser.parse_args()

	nf = str(1) #number of parity files

	q = args.quiet
	over = args.overwrite
	novfy = args.noverify
	keep = args.keep_old
	excludes=args.excludes
	exex=args.extexcludes
	dr = os.path.abspath(args.directory)
	pc = str(args.percentage)
	par_cmd = args.par_cmd

	## Load filesystem
	print("Using",par_cmd,"...")
	print("Looking for files in",dr,"...")

	allfiles = [f for f in glob.glob(os.path.join(dr,"**","*"), recursive=True) if os.path.isfile(f)] #not sure why required, but glob may introduce paths...
	if 'root' in excludes:
		allfiles = [f for f in allfiles if os.path.dirname(f) != dr]
		excludes.remove('root')
	for excl in excludes:
		allfiles = [f for f in allfiles if not f.startswith(os.path.join(dr,excl))]
	for ext in exex:
		allfiles = [f for f in allfiles if not f.endswith(ext)]

	parrables = [f for f in allfiles if not f.endswith(".par2")]

	pattern = '.+vol[0-9]+\+[0-9]+\.par2'
	par2corrfiles = [f for f in allfiles if re.search(pattern, f)]
	par2files = [f for f in allfiles if f.endswith(".par2") and not re.search(pattern, f)]

	par2errcopies = [f for f in allfiles if f.endswith(".1") or f.endswith(".2")] #remove copies with errors fixed previously by par.

	## Determine state
	def displong(lst):
		x = 0
		for f in lst:
			x += 1
			if isinstance(f, list):
				print(f[0],':',f[1])
			else:
				print(f)
			if x % 500 == 0:
				q = input("Press Enter for next 500:")

	def disp10(lst):
		if len(lst)<=10 or q: #if quiet, then print all.
			for f in lst:
				if isinstance(f, list):
					print(f[0],':',f[1])
				else:
					print(f)
		elif not q and ask_yn("Display these files?"):
			displong(lst)

	create = []
	verify = []
	incomplete = []
	print("Checking files for parrability ...")
	for f in parrables:
		# check if both or one of the par files is missing
		ispar = os.path.isfile(f+".par2")
		isvolpar = len(glob.glob(glob.escape(f)+".vol*.par2")) > 0
		if over:
			create.append(f)
		elif not ispar and not isvolpar:
			#both missing
			create.append(f)
		elif not novfy and ispar and isvolpar:
			#both present
			verify.append(f)
		elif novfy and ispar and isvolpar:
			#both present, but novfy is on, so no action
			pass
		else:
			#one of them is missing but not both
			incomplete.append(f)

	unused = []
	if not keep:
		print("Checking for unused par2 files ...")
		for f in par2files:
			if not os.path.isfile(f[:-5]):
				unused.append(f)
		for f in par2corrfiles:
			if not os.path.isfile(f.split('.vol')[0]):
				unused.append(f)
		unused.extend(par2errcopies)

	print("==========================================================")
	print('Will create',len(create),'new par2 files.')
	disp10(create)
	print('Will replace',len(incomplete),'par2 files because parity data is incomplete (missing file).')
	disp10(incomplete)
	if not novfy:
		print('Will verify',len(verify),'par2 files.')
		disp10(verify)
	if not keep:
		print('Will remove',len(unused),'unused par2 files of which',len(par2errcopies),'old repair files.')
		disp10(unused)

	all_actions = len(create) + len(incomplete) + len(verify) + len(unused)
	if not q and all_actions>0 and not ask_yn("Perform actions?", default=None):
		print('Exiting...')
		return 0

	create.extend(incomplete)

	## Execute
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
		101: "os.remove did not succeed."
	}

	devnull = open(os.devnull, 'wb')
	def runpar(command):
		try:
			subprocess.check_call(command,shell=False,stdout=devnull,stderr=devnull)
			return 0
		except subprocess.CalledProcessError as e:
			#errors.append(( command[-1],errorcodes[e.returncode] ))
			return e.returncode

	createdfiles=[]
	createdfiles_err=[]
	if len(create)>0 or over and len(parrables)>0:
		print('Creating ...')
		for f in tqdm(parrables if over else create):
			pars = glob.glob(glob.escape(f)+'*.par2')
			for p in pars:
				os.remove(p)
			createdfiles.append([ f , runpar([par_cmd,"c","-r"+pc,"-n"+nf,f]) ])
		createdfiles_err=[ [i,j] for i,j in createdfiles if j != 0 and j != 100 ]

	verifiedfiles=[]
	verifiedfiles_err=[]
	verifiedfiles_repairable=[]
	if not novfy and not over and len(verify)>0:
		print('Verifying ...')
		for f in tqdm(verify):
			verifiedfiles.append([ f , runpar([par_cmd,"v",f]) ])
		verifiedfiles_err=[ [i,j] for i,j in verifiedfiles if j != 0 and j != 100 and j != 1 ]
		verifiedfiles_repairable=[ [i,j] for i,j in verifiedfiles if j == 1 ]

	removedfiles=[]
	removedfiles_err=[]
	if not keep and len(unused)>0:
		print('Removing ...')
		for f in tqdm(unused):
			if os.path.isfile(f): # so os.remove always succeeds and returns None
				os.remove(f)
				removedfiles.append([ f , 100 ])
			else:
				removedfiles.append([ f , 101 ])
		removedfiles_err=[ [i,j] for i,j in removedfiles if j !=0 and j != 100 ]

	## Report, ask repair, autorepair if required, or recreation of parfiles
	print("==========================================================")
	all_err = createdfiles_err+verifiedfiles_err+verifiedfiles_repairable+removedfiles_err

	for err,count in Counter([j for i,j in all_err]).items():
		if err != 0 and err != 100:
			print("Error \"",errorcodes[err],"\" occured",count,"times.")
	disp10([[i,errorcodes[j]] for i,j in all_err])

	repairedfiles=[]
	recreatedfiles=[]
	if len(verifiedfiles_repairable)>0 or len(verifiedfiles_err)>0:
		if q or (not q and not novfy and ask_yn("Would you like to fix the repairable corrupted files and recreate for unrepairable files?", default=None)):
			for f,retcode in tqdm(verifiedfiles_repairable):
				retval = runpar([par_cmd,"r",f])
				if retval == 0:
					if not keep and os.path.isfile(f+".1"):
						os.remove(f+".1")
					repairedfiles.append([ f , "Succesfully repaired" ])
			for f,retcode in tqdm(verifiedfiles_err):
				pars = glob.glob(glob.escape(f)+'*.par2')
				for p in pars:
					os.remove(p)
				recreatedfiles.append([ f , runpar([par_cmd,"c","-r"+pc,"-n"+nf,f]) ])
		elif not q and not novfy and ask_yn("Would you like to recreate par files for the changed and unrepairable files?", default=None):
			for f,retcode in verifiedfiles_repairable+verifiedfiles_err:
				pars = glob.glob(glob.escape(f)+'*.par2')
				for p in pars:
					os.remove(p)
				recreatedfiles.append([ f , runpar([par_cmd,"c","-r"+pc,"-n"+nf,f]) ])
		else:
			print('No reparation or recreation will take place.')

	if len(repairedfiles)>0:
		for f,err in repairedfiles:
			print(f,":",err)
	if len(recreatedfiles)>0:
		for f,err in recreatedfiles:
			print(f,":",errorcodes[err])

	## Final Report
	print("Finished.")
	print("==========================================================")
	print("There were:")
	print(len(createdfiles),"newly created parity files.")
	print(len(all_err),"errors.")
	print(len(repairedfiles),"attempted fixes, of which",len([f for f in repairedfiles if f !=0]),"failed.")
	print(len(removedfiles),"files removed.")
	print(len(recreatedfiles),"attempted (overwritten) new parity files, of which",len([f for f in recreatedfiles if f !=0]),"failed.")

	if len(all_err)>0:
		return 1
	else:
		return 0
