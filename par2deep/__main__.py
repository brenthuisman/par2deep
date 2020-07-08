import gui_qt

if __name__ == '__main__':
	if 'DISPLAY' in os.environ:
		gui_qt.main()
	else:
		cli.main()
