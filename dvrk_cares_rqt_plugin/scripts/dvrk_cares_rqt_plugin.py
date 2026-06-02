#!/usr/bin/env python

import sys

from dvrk_cares_rqt_plugin.careslab_module import MyPlugin
from rqt_gui.main import Main

plugin = 'dvrk_cares_rqt_plugin'
main = Main(filename=plugin)
sys.exit(main.main(standalone=plugin))
