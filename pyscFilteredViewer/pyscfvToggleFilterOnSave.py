# encoding=utf-8
"""Runs the active Notepad++ file buffer through an x-to-HTML filter, and launches the resulting temporary file in the default browser
"""

import sys
from os.path import dirname             # https://stackoverflow.com/a/3144107/5508606
d = dirname(__file__)
if not d in sys.path:
    sys.path.append(dirname(__file__))

import pyscFilteredViewerLibrary
pyscFilteredViewerLibrary.pyscfv_setDebug(False)
pyscFilteredViewerLibrary.pyscfv_Toggle_FilterOnSave()
