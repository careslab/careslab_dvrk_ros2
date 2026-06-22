#!/usr/bin/env python3

import sys

from rqt_gui.main import Main


def main():
	plugin = 'dvrk_cares_rqt_plugin'
	main_obj = Main(filename=plugin)
	sys.exit(main_obj.main(sys.argv, standalone=plugin))


if __name__ == '__main__':
	main()
