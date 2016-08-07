import sys,os,argparse,subprocess,re,configparser
from collections import Counter
import glob2 as glob
from .ask_yn import ask_yn
from tqdm import tqdm

'''
one mode:
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

first, init disk state.
second, depending on overrides, propose actions and ask user confirmation
third, execute user choices.
fourth, ask to repair if possible/necesary.
fifth, final report.
'''

def main():
	#configfile
	config = configparser.ConfigParser(allow_no_value=True,delimiters=('='))

	#CMD arguments and configfile
	parser = argparse.ArgumentParser()
	parser.add_argument("-q", "--quiet", action='store_true', help="Don't asks questions, go with all defaults, including repairing and deleting files (default off).")
	parser.add_argument("-over", "--overwrite", action='store_true', help="Overwrite existing par2 files (default off).")
	parser.add_argument("-novfy", "--noverify", action='store_true', help="Do not verify existing files (default off).")
	parser.add_argument("-keep", "--keep_old", action='store_true', help="Keep unused par2 files and old par2 repair files (.1,.2 and so on).")
	
	parser.add_argument("-dir", "--directory", type=str, default=os.getcwd(), help="Path to operate on (default is current directory).")
	parser.add_argument("-pc", "--percentage", type=int, default=5, help="Set the parity percentage (default 5%%).")
	parser.add_argument("-pcmd", "--par_cmd", type=str, default="par2", help="Set path to alternative par2 command (default \"par2\").")
	args = parser.parse_args()

	nf = str(1) #number of parity files
	pc = str(args.percentage)
	dr = os.path.abspath(args.directory)
	over = args.overwrite
	novfy = args.noverify
	keep = args.keep_old
	q = args.quiet
	excludes=[]

	if os.path.isfile(os.path.join(dr,'par2deep.ini')):
		config.read(os.path.join(dr,'par2deep.ini'))
	try:
		par_cmd = list(dict(config['pcmd']).keys())[0]
	except KeyError:
		par_cmd = args.par_cmd
	try:
		excludes = list(dict(config['exclude']).keys())
	except KeyError:
		pass #no excludes

	## Load filesystem
	print("Using",par_cmd,"...")
	print("Looking for files in",dr,"...")

	allfiles = [f for f in glob.glob(os.path.join(dr,"**","*")) if os.path.isfile(f)] #not sure why required, but glob may introduce paths...
	if 'root' in excludes:
		allfiles = [f for f in allfiles if os.path.dirname(f) != dr]
	for excl in excludes:
		allfiles = [f for f in allfiles if not f.startswith(os.path.join(dr,excl))]

	parrables = [f for f in allfiles if not f.endswith(".par2")]

	pattern = '.+vol[0-9]+\+[0-9]+\.par2'
	par2corrfiles = [f for f in allfiles if re.search(pattern, f)]
	par2files = [f for f in allfiles if f.endswith(".par2") and not re.search(pattern, f)]

	par2errcopies = [f for f in allfiles if f.endswith(".1") or f.endswith(".2")] #remove copies with errors fixed previously by par.

	## Determine state
	def disp10(lst):
		if len(lst)<=10:
			for f in lst:
				if isinstance(f, list):
					print(f[0],':',f[1])
				else:
					print(f)

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

	create = []
	print("Checking files without .par2 ...")
	for f in parrables:
		if not os.path.isfile(f+".par2") or over:
			create.append(f)

	verify = []
	if not novfy and not over:
		print("Checking files with .par2 ...")
		for f in parrables:
			if os.path.isfile(f+".par2"):
				verify.append(f)

	unused = []
	if not keep:
		print("Checking for .par files with missing files ...")
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
	if not novfy:
		print('Will verify',len(verify),'par2 files.')
		disp10(verify)
	if not keep:
		print('Will remove',len(unused),'unused par2 files of which',len(par2errcopies),'old repair files.')
		disp10(unused)

	all_actions = create + verify + unused
	if len(create) > 10 or len(verify) >= 10 or len(unused) >= 10:
		if not q and ask_yn("Display all filenames?"):
			displong(all_actions)

	if not q and len(all_actions)>0 and not ask_yn("Perform actions?", default=None):
		print('Exiting...')
		return 0

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
		for f in tqdm(parrables if over else create):
			pars = glob.glob(f+'*.par2')
			for p in pars:
				os.remove(p)
			createdfiles.append([ f , runpar([par_cmd,"c","-r"+pc,"-n"+nf,f]) ])
		createdfiles_err=[ [i,j] for i,j in createdfiles if j != 0 and j != 100 ]

	verifiedfiles=[]
	verifiedfiles_err=[]
	verifiedfiles_repairable=[]
	if not novfy:
		for f in tqdm(verify):
			verifiedfiles.append([ f , runpar([par_cmd,"v",f]) ])
		verifiedfiles_err=[ [i,j] for i,j in verifiedfiles if j != 0 and j != 100 and j != 1 ]
		verifiedfiles_repairable=[ [i,j] for i,j in verifiedfiles if j == 1 ]

	removedfiles=[]
	removedfiles_err=[]
	if not keep:
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
	if not q and len(all_err)>10 and ask_yn("Display all files with errors?"):
		for l in all_err:
			print(l[0],':',errorcodes[l[1]])

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
				pars = glob.glob(f+'*.par2')
				for p in pars:
					os.remove(p)
				recreatedfiles.append([ f , runpar([par_cmd,"c","-r"+pc,"-n"+nf,f]) ])
		elif not q and not novfy and ask_yn("Would you like to recreate par files for the changed and unrepairable files?", default=None):
			for f,retcode in tqdm(verifiedfiles_repairable+verifiedfiles_err):
				pars = glob.glob(f+'*.par2')
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
	print(len(repairedfiles),"succesful fixes")
	print(len(removedfiles),"files removed.")
	print(len(recreatedfiles),"overwritten new parity files.")

	if len(all_err)>0:
		return 1
	else:
		return 0
