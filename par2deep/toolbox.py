import os,sys


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


def startfile(fname):
	fname = os.path.normpath(fname)
	if os.path.isfile(fname):
		if sys.platform == 'win32':
			os.startfile(fname)
		elif sys.platform == 'linux':
			os.system("nohup xdg-open \""+fname+"\" >/dev/null 2>&1 &")
		# TODO macos?
	return
