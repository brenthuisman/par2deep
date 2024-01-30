from cx_Freeze import setup, Executable
import sys,os.path,glob

VERSION = '1.10.1'
NAME = 'par2deep'
DESCRIPTION = "Produce, verify and repair par2 files recursively."

exe_options = {
	'include_files':[
		NAME+'.ico',
		] + glob.glob("par2deep/*.py") + glob.glob("par2deep/*.exe"),
	'packages': ["configargparse","PyQt5", "send2trash", "tqdm"], #adding tqdm causes every installed pip package to be included...
}

shortcut_table = [
	("DesktopShortcut",        # Shortcut
		"DesktopFolder",          # Directory_
		NAME,           # Name
		"TARGETDIR",              # Component_
		"[TARGETDIR]"+NAME+".exe",# Target
		None,                     # Arguments
		None,                     # Description
		None,                     # Hotkey
		None,                     # Icon
		None,                     # IconIndex
		None,                     # ShowCmd
		'TARGETDIR'               # WkDir
		),
	("ProgramMenuShortcut",        # Shortcut
		"ProgramMenuFolder",          # Directory_
		NAME,           # Name
		"TARGETDIR",              # Component_
		"[TARGETDIR]"+NAME+".exe",# Target
		None,                     # Arguments
		None,                     # Description
		None,                     # Hotkey
		None,                     # Icon
		None,                     # IconIndex
		None,                     # ShowCmd
		'TARGETDIR'               # WkDir
		)
	]

bdist_msi_options = {'data': {"Shortcut": shortcut_table} }

base = None
if sys.platform == 'win32':
	base = 'Win32GUI'

executables = [
	Executable(NAME+'/__main__.py',
			base=base,
			targetName=NAME+'.exe',
			icon=NAME+'.ico',
			#shortcutName=NAME,
			#shortcutDir=["DesktopFolder","ProgramMenuFolder"],
			)
]

def main():
	setup(name=NAME,
		version=VERSION,
		description=DESCRIPTION,
		executables=executables,
		options={
			'bdist_msi': bdist_msi_options,
			'build_exe': exe_options},
	)

if __name__ == '__main__':
	main()
