from cx_Freeze import setup, Executable
import sys,os.path,glob

VERSION = '1.0.2'
NAME = 'par2deep'
DESCRIPTION = "Produce, verify and repair par2 files recursively."

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

exe_options = {
	'include_files':[
		os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'),
		os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),
		'phpar2.exe',
		NAME+'.ico',
		] + glob.glob("par2deep/*.py"),
	'packages': ['configargparse','tkinter'], #adding tqdm causes every installed pip package to be included...
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
