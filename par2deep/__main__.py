import os,gui_qt,cli

if __name__ == '__main__':
	if 'DISPLAY' in os.environ:
		gui_qt.main()
	else:
		cli.main()
