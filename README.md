## par2deep

Analogous to the various *deep commands (md5deep, hashdeep...) this tool serves to create, verify and repair parity files in a file tree.

This tool will generate one parity file (plus a file for the recovery blocks) per file that you protect. This makes it simple to move files if you change your mind on how your file tree must be organized. Just move the `par2` files along.

On Windows and Linux 64bit platforms, a compiled [libpar2](https://github.com/brenthuisman/libpar2) is provided and no external `par2` required.

## Motivation

I chose to use the old but well tested and well known `par2` program to base this tool on, instead of similar tools such as `zfec`, `rsbep` or something like `pyFileFixity`. Some recent forks of `par2` have added recursive scanning abilities, but they're generally not cross-platform. They also do not offer an interactive way of diagnosing (parts of) your file tree, and different problem handling for different areas of your file tree.

I use `par2deep` to secure my photos and music across drives, machines and operating systems, and I intend to keep securing my data this way in the decades to come. I felt that the wide availability of the `par2` tool was my best bet.

## Install

If you have Python installed, you can use pip! Make sure to update pip before installation (PyQt5 won't install without a recent pip). On Windows, you may have to run `python` for `python3` and `pip` for `pip3`.

    $ pip3 install -U pip
    $ pip3 install par2deep --user

If you use Windows, and do not have Python installed, you can grab an installer [here](https://github.com/brenthuisman/par2deep/releases). These msi packages are generated created with the `cx_Freeze` package using the `setup_cx.py` script:

    $ python3 setup_cx.py bdist_msi

Alternatively, clone/download this repo and install:

    $ python3 setup.py install --user

Or run directly:

    $ python3 par2deep

## Usage

After installation, run with `par2deep` for the GUI or `par2deep-cli` if you live in the terminal. Command line options may be enumerated by using the --help option. Note that `-q` will update, fix or recreate parity files as it sees fit. If unrepairable damage is found, it will recreate parity data. (The old tkinter GUI is unmaintained but available at `par2deep-tk`.)

An optional `par2deep.ini` file may be placed in the target directory or as `~/.par2deep` defining all the commandline options. For the excludes, separate by comma.

Example `par2deep.ini`:

	excludes = [new, root]
	extexcludes = [JPG, jpg]
	par_cmd = c:/sync/apps/par/par2.exe

## Dependencies

 * tqdm
 * configargparse
 * Send2Trash
 * PyQt5
 * Optional, if you are not on Windows or Linux 64bit, `par2` in path or specify with `par_cmd`.

### Changelog

 * 2022-01-31: v1.9.4.1: Moved kinda-broken (no UTF8 filename support) `gopar` changes to gopar branch, release last commit as new version as it fixes some things.
 * 2020-04-26: v1.9.4: Include libpar2 for win64 and lin64 platforms, no external `par2` needed anymore.
 * 2020-04-20: recreate verified_repairable creates backup. backups are shows upon init. orphans are shown upon init.
 * 2020-04-16: v1.9.3: Packaging still is a pain!
 * 2020-04-16: v1.9.0: GUI rewritten in with Qt (PyQt5). Open Issues should be solved for 2.0.0 release.
 * 2019-02-15: v1.0.5: Instead of deleting files (os.remove), now Send2Trash is used.
 * 2018-12-05: v1.0.4: Gui mode is now shutdownable (threads dont keep running in the background anymore).
 * 2018-12-05: v1.0.3. Once again fixed imports. Should now work with local, pip-installed and bundled versions. Gui and cli now show filename during executing actions stage.
 * 2018-05-30: v1.0.2. GUI updates: file doubleclick now checkes if string is file, added tooltips to GUI settings, and treeview category headers have a bit for info (nb of files in category). CLI updates: same par2deep import check as GUI.
 * 2018-05-25: v1.0.1. Crossplatform doubleclick in treeview. Improved Windows par2 executable finding. New cx_Freeze installer script. Converted relative imports.
 * 2016-08-20: Ensured par2 command is called correctly from Windows and other OS in GUI mode. Added NSIS installer script.
 * 2016-08-12: Revamped tool. Reset to v1.0.0. Includes Tkinter gui. cli unchanged apart from cosmetics.
 * 2016-08-07: Added optional config files, excludes, extensions, and parity completeness check.
 * 2016-08-06: Program no longer maps to `par2` commandline options but (loosely) to `hashdeep` tools: run it, and see what has changed and needs to be done with respect to the previous run.
 * 2016-03-22: Finish port to Python 3, added setup.py.
 * 2016-03-19: Added quiet mode, keep backup files upon unsuccesful repair.
 * 2016-03-17: First release
