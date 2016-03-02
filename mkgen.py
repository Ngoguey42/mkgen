# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    mkgen.py                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: ngoguey <ngoguey@student.42.fr>            +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2016/03/02 15:19:56 by ngoguey           #+#    #+#              #
#    Updated: 2016/03/02 18:22:03 by ngoguey          ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import os
from include_explorer import Explorer
import re
import subprocess

CMD = 'make -pn nosuchrule 2>/dev/null | grep -A1 "^# makefile"| grep -v "^#\|^--" | sort | uniq'

PATTERNINC = r"^MKGEN_INCLUDESDIRS .\= (.*)$"
PATTERNOBJDIR = r"^MKGEN_OBJDIR .\= ([^\s]*)$"
PATTERNSRCS = r"^MKGEN_SRCSDIRS_([^\s]*) .\= (.*)$"
PATTERNSRC = r"^(.*)\.(c|cpp)$"
PATTERNSRCBODY = r"^\s*\#\s*include\s*\"(.*)\""

def includes_list_of_output(s):
	grps = re.search(PATTERNINC, s, re.MULTILINE)
	if grps == None:
		print("\033[31mError: Could not find variable MKGEN_INCLUDESDIRS\033[0m")
		return None
	return grps.group(1).split(' ')

def objdir_of_output(s):
	grps = re.search(PATTERNOBJDIR, s, re.MULTILINE)
	if grps == None:
		print("\033[31mError: Could not find variable MKGEN_OBJDIR\033[0m")
		return None
	return grps.group(1)

def srcstargets_of_output(s):
	grps = re.findall(PATTERNSRCS, s, re.MULTILINE)
	if grps == None:
		print("\033[31mError: Could not find any variable PATTERN MKGEN_SRCSDIRS_*\033[0m")
		return None
	return [(x[0], x[1].split(' ')) for x in grps];

def sourcefiles_of_directory(dirname, explorer):
	files_found = []
	print("reding dir: " + directory)
	if not os.path.isdir(dirname):
		print("\033[33mWarning: No such directory %s\033[0m" % dirname)
		return []
	for root, dirs, files in os.walk(dirname):
		for file in files:
			grps = re.search(PATTERNSRC, file)
			if grps != None:
				incs = explorer.dep_set_of_sourcefile("%s/%s" %(root, file))
				files_found.append((root, grps.group(1), grps.group(2), incs))
	if len(files_found) == 0:
		print("\033[33mWarning: No sources found in %s\033[0m" % dirname)
		return []
	return files_found;

def write_to_file(stream, srcstargets, sourcefiles_per_trgtdir, objdir):
	for srcstarget in srcstargets:
		stream.write("MKGEN_SRCSBIN_%s :=" % srcstarget[0].upper())
		for directory in srcstarget[1]:
			files = sourcefiles_per_trgtdir[directory]
			i = 0
			for f in files:
				stream.write("\\\n")
				stream.write("\t%s/%s/%s.o" % (objdir, f[0], f[1]))
		stream.write("\n")
	for _, srcdir in sourcefiles_per_trgtdir.items():
		# print(srcdir, '\n')
		for f in srcdir:
			stream.write("%s/%s/%s.o: " % (objdir, f[0], f[1]))
			for dep in f[3]:
				 stream.write("%s " % dep)
			stream.write("| %s/%s/\n" % (objdir, f[0]))


if __name__ == "__main__":
	if not os.path.isfile("Makefile"):
		print(("\033[31mError: %s/Makefile missing\033[0m") %(os.getcwd()))
		exit()
	ret = subprocess.Popen(CMD, shell=True, stdout=subprocess.PIPE).stdout.read()
	# print(ret.decode("utf-8"))
	includes = includes_list_of_output(ret.decode("utf-8"))
	if includes == None:
		exit()
	print(includes) #debug
	objdir = objdir_of_output(ret.decode("utf-8"))
	if objdir == None:
		exit()
	print(objdir) #debug
	srcstargets = srcstargets_of_output(ret.decode("utf-8"))
	if srcstargets == None:
		exit()
	print(srcstargets) #debug
	sourcefiles_per_trgtdir = dict()
	inc_explorer = Explorer(includes)
	for trgt in srcstargets:
		for directory in trgt[1]:
			if directory not in sourcefiles_per_trgtdir:
				sourcefiles = sourcefiles_of_directory(directory, inc_explorer)
				if sourcefiles == None:
					exit()
				sourcefiles_per_trgtdir[directory] = sourcefiles;
	with open("hello.mk", "w") as stream:
		write_to_file(stream, srcstargets, sourcefiles_per_trgtdir, objdir)
	print(sourcefiles_per_trgtdir) #debug
