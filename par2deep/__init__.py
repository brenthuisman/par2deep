import sys,os,argparse,subprocess,glob2 as glob
from ask_yn import ask_yn
from tqdm import tqdm
from collections import Counter as cntr

#TODO: flag large file only (1MB+?) perhaps also higher default percentage for smaller files?

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("operation", type=str, choices=["c","v","r","u"], help="Set the type of operation: (c)reate (keeps existing par2 files), (u)pdate and create par2 files, (v)erify or auto(r)epair par2 files, (i)nteractive verification and repair.")
	parser.add_argument("-q", "--quiet", action='store_true', help="Don't offer to repair when verification fails.")
	parser.add_argument("-dir", "--directory", type=str, default=os.getcwd(), help="Path to operate on (default is current directory).")
	parser.add_argument("-ir", "--include_root", action='store_true', help="Include files in the root of the specified directory (default off).")
	parser.add_argument("-ko", "--keep_old", action='store_true', help="Keep old files when par2 finds and corrects errors.")
	parser.add_argument("-pc", "--percentage", type=int, default=5, help="Set the parity percentage (default 5%%).")
	parser.add_argument("-cmd", "--par_cmd", type=str, default="par2", help="Set path to alternative par2 command (default \"par2\").")
	args = parser.parse_args()

	nf = str(1) #number of parity files
	pc = str(args.percentage)
	dr = os.path.abspath(args.directory)
	ko = args.keep_old
	ir = args.include_root
	q = args.quiet
	par_cmd = args.par_cmd

	def cmd_exists(cmd):
	    return subprocess.check_call("type " + cmd, shell=True) == 0

	if not cmd_exists(par_cmd):
		if not cmd_exists(os.path.join(sys.path[0],"par2.exe")):
			sys.stderr.write(par_cmd+" not in path, aborting...")
			sys.exit(1)

	print("Looking for files in",dr,"...")

	filel = glob.glob(os.path.join(dr,"**","*"))
	filel = [f for f in filel if not f.endswith(".par2")]
	filel = [f for f in filel if not f.endswith(".1") and not f.endswith(".2")] #remove copies with errors fixed previously by par.
	filel = [f for f in filel if os.path.isfile(f)] #not sure why required, but glob may introduce paths...
	if not ir:
		filel = [f for f in filel if os.path.dirname(f) != dr]

	errors=[]
	succes=[]

	errorcodes = {
		0: "Succes.", #can mean no error, but also succesfully repaired!
		1: "Repairable damage found.",
		2: "Irreparable damage found.",
		3: "Invalid commandline arguments.",
		4: "Parity file unusable.",
		5: "Repair failed.",
		6: "IO error.",
		7: "Internal error",
		8: "Out of memory."
	}

	devnull = open(os.devnull, 'wb')

	def runpar(command):
		try:
			subprocess.check_call(command,shell=False,stdout=devnull,stderr=devnull)
			return 0
		except subprocess.CalledProcessError as e:
			errors.append(( command[-1],errorcodes[e.returncode] ))
			return e.returncode

	if args.operation is "c":
		print("Creating par2 files in",dr)
		for f in tqdm(filel):
			if not os.path.isfile(f+".par2"):
				runpar([par_cmd,"c","-r"+pc,"-n"+nf,f])

	if args.operation is "u":
		print("Updating and creating par2 files in",dr)
		for f in tqdm(filel):
			[os.remove(x) for x in glob.glob(f+"*.par2")]
			runpar([par_cmd,"c","-r"+pc,"-n"+nf,f])

	if args.operation is "v":
		print("Verifying files in",dr)
		for f in tqdm(filel):
			if not os.path.isfile(f+".par2"):
				errors.append((f,"no .par2 found"))
				continue
			runpar([par_cmd,"v",f])
		if len(errors)>0 and not q:
			print("There were",len(errors),"errors.")
			if ask_yn("Would you like to fix them?"):
				for f,retcode in tqdm(errors):
					retval = runpar([par_cmd,"r",f])
					if retval == 0 and not ko and os.path.isfile(f+".1"):
						os.remove(f+".1")
						succes.append((f,"Succesfully repaired"))

	if args.operation is "r":
		print("Repairing files in",dr)
		for f in tqdm(filel):
			if not os.path.isfile(f+".par2"):
				errors.append((f,"no .par2 found"))
				continue
			retval = runpar([par_cmd,"r",f])
			if retval == 0 and not ko and os.path.isfile(f+".1"):
				os.remove(f+".1")
				succes.append((f,"Succesfully repaired"))

	print("Finished.")
	print("There were",len(errors),"errors and",len(succes),"succesful fixes.")

	if len(errors)>0:
		for err,count in cntr([j for i,j in errors]).items():
			print("Error \"",err,"\" occured",count,"times.")
		for filen,err in errors:
			print(filen,": ",err)
	if len(succes)>0:
		for filen,err in succes:
			print(filen,": ",err)

	if len(errors)>0:
		return 1
	else:
		return 0
