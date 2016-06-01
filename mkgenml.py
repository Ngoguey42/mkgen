# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    mkgenml.py                                         :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: ngoguey <ngoguey@student.42.fr>            +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2016/06/01 07:48:00 by ngoguey           #+#    #+#              #
#    Updated: 2016/06/01 12:58:36 by ngoguey          ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import os, subprocess, re, sys
from ftocamldep import from_sourcefiles_per_trgtdir

CMD0 = 'make -pn nosuchrule 2>/dev/null | grep -A1 "^# makefile"| grep -v "^#\|^--" | sort | uniq'

PATTERNOBJDIR = r"^MKGEN_OBJDIR .\= ([^\s]*)$"
PATTERNSRCS = r"^MKGEN_SRCSDIRS_([^\s]*) .\= (.*)$"
PATTERNOBJSUFFIX = r"^MKGEN_OBJSUFFIX_([^\s]*) .\= (.*)$"
PATTERNDEPCMD = r"^MKGEN_DEPCMD .\= (.*)$"
PATTERNSRC = r"^(.*)\.(ml|mli)$"

src_to_bin_ext = {'cmo':'ml', 'cmx':'ml', 'cmi':'mli'}


def objdir_of_output(s):
	grps = re.search(PATTERNOBJDIR, s, re.MULTILINE)
	if grps == None:
		print("\033[31mError: Could not find variable MKGEN_OBJDIR\033[0m")
		return None
	return grps.group(1)

def depcmd_of_output(s):
	grps = re.search(PATTERNDEPCMD, s, re.MULTILINE)
	if grps == None:
		print("\033[31mError: Could not find variable MKGEN_DEPCMD\033[0m")
		return None
	return grps.group(1)

def srcstargets_of_output(s):
	srcsdirs = re.findall(PATTERNSRCS, s, re.MULTILINE)
	if srcsdirs == None or len(srcsdirs) == 0:
		print("\033[31mError: Could not find any variable PATTERN MKGEN_SRCSDIRS_*\033[0m")
		return None
	targets = []
	for match in srcsdirs:
		objsuffix_pattern = r"^MKGEN_OBJSUFFIX_" + match[0] + " .\= (.*)$"
		objsuffixes = re.findall(objsuffix_pattern, s, re.MULTILINE)
		if objsuffixes == None or len(objsuffixes) != 1:
			print("\033[31mError: Could not find variable MKGEN_OBJSUFFIX_" + match[0] + "\033[0m")
			exit()
		suffixes = eval(objsuffixes[0])
		targets.append((match[0], match[1].split(' '), suffixes));
	return targets

def sourcefiles_of_directory(dirname):
	files_found = []
	print('exploring:', directory) #debug
	if not os.path.isdir(dirname):
		print("\033[33mWarning: No such directory %s\033[0m" % dirname)
		return []
	for file in os.listdir(dirname):
		grps = re.search(PATTERNSRC, file)
		if grps != None:
			files_found.append((directory, grps.group(1), grps.group(2)))
	if len(files_found) == 0:
		print("\033[33mWarning: No sources found in %s\033[0m" % dirname)
		return []
	print('    found:', files_found)
	return files_found;

def write_targets_to_file(stream, srcstargets, sourcefiles_per_trgtdir, objdir, depcmd):
	for srcstarget in sorted(srcstargets, key=lambda f: f[0].upper()):
		stream.write("MKGEN_SRCSBIN_%s :=" % srcstarget[0].upper())
		unsorted = ""
		for directory in sorted(srcstarget[1]):
			files = sourcefiles_per_trgtdir[directory]
			for f in sorted(files):
				if f[2] == 'mli':
					continue
				unsorted += " %s/%s.ml" % (f[0], f[1])
		cmd = depcmd + ' -one-line -sort' + unsorted
		print('cmd: \033[32m%s\033[0m' % cmd)
		sort = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)\
					   .stdout.read().decode("utf-8");
		suffix = srcstarget[2]['ml']
		sort = ''.join([" %s/%s.%s" % (objdir, x[:-3], suffix) for x in sort.strip().split(' ') if x != ''])
		stream.write(sort)
		stream.write("\n")

def write_deps_to_file(stream, deps, objdir):
	for filedep in sorted(deps):
		stream.write("%s/%s/%s.%s :" % (objdir, filedep[0][0], filedep[0][1],
										filedep[0][2]))
		stream.write(" %s/%s.%s" % (filedep[0][0], filedep[0][1]
			, src_to_bin_ext[filedep[0][2]]))
		for dep in sorted(filedep[1]):
			stream.write(" %s/%s" % (objdir, dep))
		stream.write(" | %s/%s/\n" % (objdir, filedep[0][0]))
		pass

if __name__ == "__main__":
	if not os.path.isfile("Makefile"):
		print(("\033[31mError: %s/Makefile missing\033[0m") %(os.getcwd()))
		exit()
	print('cmd: \033[32m%s\033[0m' % CMD0)
	mkvars = subprocess.Popen(CMD0, shell=True, stdout=subprocess.PIPE)\
					   .stdout.read().decode("utf-8");
	# print('mkvars:', mkvars)
	objdir = objdir_of_output(mkvars)
	if objdir == None:
		print('\033[31mError: MKGEN_OBJDIR missing\033[0m')
		exit()
	print('objdir: \033[32m%s\033[0m' % objdir)

	print(sys.argv)
	if len(sys.argv) > 2:
		depcmd = sys.argv[2]
	else:
		depcmd = 'ocamldep'

	srcstargets = srcstargets_of_output(mkvars)
	if srcstargets == None:
		exit()
	print('srcstargets: \033[32m%s\033[0m' % srcstargets)

	sourcefiles_per_trgtdir = dict()
	for trgt in srcstargets:
		for directory in trgt[1]:
			if directory not in sourcefiles_per_trgtdir:
				sourcefiles = sourcefiles_of_directory(directory)
				sourcefiles_per_trgtdir[directory] = sourcefiles;

	deps = from_sourcefiles_per_trgtdir(sourcefiles_per_trgtdir, depcmd)
	with open("depend.mk", "w") as stream:
		write_targets_to_file(stream, srcstargets, sourcefiles_per_trgtdir, objdir, depcmd)
		write_deps_to_file(stream, deps, objdir)
