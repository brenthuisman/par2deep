#!/usr/bin/env python
import threading,time,queue
import tqdm
try:
	from .par2deep import *
except:
	from par2deep import *
try:
	from .ask_yn import *
except:
	from ask_yn import *

def displong(lst,q=False):
	x = 0
	for f in lst:
		x += 1
		if isinstance(f, list):
			print(f[0],':',f[1])
		else:
			print(f)
		if x % 500 == 0:
			input("Press Enter for next 500:")

def disp10(lst,q=False):
	if len(lst)<=10 or q: #if quiet, then print all.
		for f in lst:
			if isinstance(f, list):
				print(f[0],':',f[1])
			else:
				print(f)
	elif not q and ask_yn("Display these files?"):
		displong(lst)

def main():
	p2d = par2deep()

	print("Using",p2d.par_cmd,"...")
	print("Looking for files in",p2d.directory,"...")
	
	if p2d.check_state() == 200:
		print("The par2 command you specified is invalid.")
		return 1

	print("==========================================================")
	print('Will create',len(p2d.create),'new par2 files.')
	disp10(p2d.create,p2d.quiet)
	print('Will replace',len(p2d.incomplete),'par2 files because parity data is incomplete (missing file).')
	disp10(p2d.incomplete,p2d.quiet)
	print('Will verify',len(p2d.verify),'par2 files.')
	disp10(p2d.verify,p2d.quiet)
	print('Will remove',len(p2d.unused),'unused par2 files.')
	disp10(p2d.unused,p2d.quiet)
	print('Will remove',len(p2d.par2errcopies),'old repair files.')
	disp10(p2d.par2errcopies,p2d.quiet)

	if not p2d.quiet and p2d.len_all_actions>0 and not ask_yn("Perform actions?", default=None):
		print('Exiting...')
		return 1

	print(p2d.len_all_actions)
	with tqdm.tqdm(total=p2d.len_all_actions, unit='files', unit_scale=True) as pbar:
		for i in p2d.execute():
			pbar.update(1)
			pbar.set_postfix_str(i[-20:])

	print("==========================================================")
	print(len(p2d.verifiedfiles_succes),'files verified and in order.')
	disp10(p2d.verifiedfiles_succes,p2d.quiet)
	print(len(p2d.createdfiles_err),'files failed to create.')
	disp10(p2d.createdfiles_err,p2d.quiet)
	print(len(p2d.verifiedfiles_err),'files verified and unrepairable.')
	disp10(p2d.verifiedfiles_err,p2d.quiet)
	print(len(p2d.verifiedfiles_repairable),'files verified and repairable.')
	disp10(p2d.verifiedfiles_repairable,p2d.quiet)
	print(len(p2d.removedfiles_err),'files failed to remove.')
	disp10(p2d.removedfiles_err,p2d.quiet)

	noaction=False
	if p2d.len_verified_actions>0:
		if p2d.quiet or (not p2d.quiet and not p2d.noverify and ask_yn("Would you like to fix the repairable corrupted files and recreate for unrepairable files?", default=None)):
			with tqdm.tqdm(total=p2d.len_verified_actions, unit='files', unit_scale=True) as pbar:
				for i in p2d.execute_repair():
					pbar.update(1)
					pbar.set_postfix_str(i[-20:])
		elif not p2d.quiet and not p2d.noverify and ask_yn("Would you like to recreate par files for the changed and unrepairable files?", default=None):
			with tqdm.tqdm(total=p2d.len_verified_actions, unit='files', unit_scale=True) as pbar:
				for i in p2d.execute_recreate():
					pbar.update(1)
					pbar.set_postfix_str(i[-20:])
		else:
			noaction=True
			# print('No reparation or recreation will take place.')

	print("Finished.")
	print("==========================================================")
	print("There were:")
	print(len(p2d.verifiedfiles_succes),'files verified and in order.')
	print(len(p2d.createdfiles),"newly created parity files.")
	print(len(p2d.removedfiles),"files removed.")
	print(p2d.len_all_err,"errors.")

	print(len(p2d.createdfiles_err),"files failed to create.")
	disp10(p2d.createdfiles_err,p2d.quiet)
	print(len(p2d.removedfiles_err),"files failed to remove.")
	disp10(p2d.removedfiles_err,p2d.quiet)

	if noaction:
		print(len(p2d.fixes),"verified files succesfully fixed.")
		disp10(p2d.fixes,p2d.quiet)
		print(len(p2d.fixes_err),"verified files failed to fix.")
		disp10(p2d.fixes_err,p2d.quiet)
		print(len(p2d.recreate),"(overwritten) new parity files.")
		disp10(p2d.recreate,p2d.quiet)
		print(len(p2d.recreate_err),"failed (overwritten) new parity files.")
		disp10(p2d.recreate_err,p2d.quiet)

	if p2d.len_all_err>0:
		return 1
	else:
		return 0

if __name__ == "__main__":
	main()
