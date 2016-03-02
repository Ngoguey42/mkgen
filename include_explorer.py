# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    include_explorer.py                                :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: ngoguey <ngoguey@student.42.fr>            +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2016/03/02 17:05:28 by ngoguey           #+#    #+#              #
#    Updated: 2016/03/02 17:57:44 by ngoguey          ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import os
import re

PATTERNSRCBODY = r"^\s*\#\s*include\s*\"(.*)\""

class Explorer:
	def __init__(self, inc_dirs):
		self.inc_dirs = []
		for directory in inc_dirs:
			if os.path.isdir(directory):
				self.inc_dirs.append(directory)
			else:
				print("\033[33mWarning: No such directory %s\033[0m" % directory)
		self.incs_dict = dict()

	def fpath_from_fname(self, fname):
		for directory in self.inc_dirs:
			fpath = "%s/%s" % (directory, fname)
			if os.path.isfile(fpath):
				return fpath
		return None

	def includes_of_fpath(self, fpath):
		buf = None
		with open(fpath, "r") as stream:
			buf = stream.read()
		if buf == None:
			print("\033[33mWarning: Could not read file %s\033[0m" % fpath)
			return []
		grps = re.findall(PATTERNSRCBODY, buf, re.MULTILINE)
		if grps == None:
			return []
		return grps


	def dependencies_of_fpath(self, fpath):
		if fpath in self.incs_dict:
			return self.incs_dict[fpath]
		if fpath in self.encountered_set:
			print("\033[33mWarning: Loop detected with file %s\033[0m" % fpath)
			return set()
		self.encountered_set.add(fpath)
		incs = self.includes_of_fpath(fpath)
		cur_set = set()
		cur_set.add(fpath)

		if incs != None:
			for inc in incs:
				ipath = self.fpath_from_fname(inc)
				if ipath != None:
					cur_set |= self.dependencies_of_fpath(ipath)

		print("Read file %s (%d inc %d deps) %s" % (fpath, len(incs), len(cur_set), str(incs))) #debug
		self.incs_dict[fpath] = cur_set
		return cur_set


	def dep_set_of_sourcefile(self, fpath):
		self.encountered_set = set()
		return self.dependencies_of_fpath(fpath)
