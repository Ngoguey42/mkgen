# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    mkgen.py                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: ngoguey <ngoguey@student.42.fr>            +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2016/03/02 15:19:56 by ngoguey           #+#    #+#              #
#    Updated: 2016/03/02 16:06:41 by ngoguey          ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import os
import re
import subprocess

CMD = 'make -pn nosuchrule 2>/dev/null | grep -A1 "^# makefile"| grep -v "^#\|^--" | sort | uniq'

PATTERNINC = r"^MKGEN_INCLUDESDIRS .\= (.*)$"
PATTERNOBJDIR = r"^MKGEN_OBJDIR .\= ([^\s]*)$"
PATTERNSRCS = r"^MKGEN_SRCSDIRS_([^\s]*) .\= (.*)$"

def includes_list_of_output(s):
	grps = re.search(PATTERNINC, s, re.MULTILINE)
	if grps == None:
		print("\033[31mCould not find variable MKGEN_INCLUDESDIRS\033[0m")
		return None
	return grps.group(1).split(' ')

def objdir_of_output(s):
	grps = re.search(PATTERNOBJDIR, s, re.MULTILINE)
	if grps == None:
		print("\033[31mCould not find variable MKGEN_OBJDIR\033[0m")
		return None
	return grps.group(1)

def srcstargets_of_output(s):
	grps = re.findall(PATTERNSRCS, s, re.MULTILINE)
	if grps == None:
		print("\033[31mCould not find any variable PATTERN MKGEN_SRCSDIRS_*\033[0m")
		return None
	return [(x[0], x[1].split(' ')) for x in grps];

if __name__ == "__main__":
	if not os.path.isfile("Makefile"):
		print(("\033[31m%s/Makefile missing\033[0m") %(os.getcwd()))
		exit()
	ret = subprocess.Popen(CMD, shell=True, stdout=subprocess.PIPE).stdout.read()
	print(ret.decode("utf-8"))
	includes = includes_list_of_output(ret.decode("utf-8"))
	if includes == None:
		exit()
	print(includes)
	objdir = objdir_of_output(ret.decode("utf-8"))
	if objdir == None:
		exit()
	print(objdir)
	srcstargets = srcstargets_of_output(ret.decode("utf-8"))
	if srcstargets == None:
		exit()
	print(srcstargets)
