## par2deep

Analogous to the various *deep commands (md5deep, hasdeep...) this tool serves to create, verify and repair parity files in an entire directory hierarchy.

This tool will generate one parity file (plus a file for the recovery blocks) per file that you protect. This makes it simple to move files if you change your mind on how your file tree must be organized. Just move the `par2`files along.

## Motivation
I chose to use the old but well tested and well known `par2` program to base this tool on, instead of similar tools such as `zfec`, `rsbep` or something like `pyFileFixity`. Some recent forks of `par2` have added recursive scanning abilities, but they're generally not cross-platform.

I use `par2deep` to secure my photos and music across drives, machines and operating systems, and I intend to keep securing my data this way in the decades to come. I felt that the wide availability of the `par2` tool was my best bet.

## Install

This script requires Python 2 and two `pip`able libraries: `glob2` and `tqdm`.

If you run Python 3, just put push `par2deep` through `2to3` and `pip3` the same libraries, and you're good to go.

`par2deep` assumes that `par2` is in your path, which you can override by specifying `-par`.

## Usage

By default, `par2deep` operates on all files under the current directory. It uses `par2`s `c`reate, `v`erify and `r`epair arguments. Run `par2deep.py c` to get started!

See `par2deep -h` for all options.