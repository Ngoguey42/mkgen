# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    mkgenml.py                                         :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: ngoguey <ngoguey@student.42.fr>            +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2016/06/01 07:48:00 by ngoguey           #+#    #+#              #
#    Updated: 2016/06/15 14:23:55 by ngoguey          ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import os, subprocess, re, sys
from ftocamldep import dependencies_of_data

src_to_bin_ext = {'cmo':'ml', 'cmx':'ml', 'cmi':'mli'}

"""
data_of_makefilevars() INVARIANTS

objdir: must be present, must be string, must be longer than 0
targets: must be present, must be dict, must be longer than 0
targets.*:
	must be dicts
	must contain srcdirs
	must contain objsuffixes
	may contain depcmd (if missing, is set to 'ocamldep')
targets.*.srcdirs: must be non-empty list of non-empty strings
targets.*.objsuffixes: must be dict of non-empty strings
targets.*.depcmd: must be non-empty string

TODO: all keys must be non empty strings

"""

def data_of_makefilevars(txt):
	pattern = r"^\bMKGEN\b\s*\:\=(.*)$"
	match = re.search(pattern, mkvars)
	if match == None or match.group(1) == None:
		print("\033[31mError: Could not find a valid MGKEN variable in Makefile\033[0m")
		exit()
	data = eval(match.group(1))
	if data == None:
		print("\033[31mError: Could not find a valid MGKEN variable in Makefile\033[0m")
		exit()
	if 'objdir' not in data:
		print("\033[31mError: Missing MGKEN['objdir'] variable\033[0m")
		exit()
	if type(data['objdir']) is not str or len(data['objdir']) < 1:
		print("\033[31mError: Invalid MGKEN['objdir'] variable\033[0m")
		exit()
	if 'targets' not in data:
		print("\033[31mError: Missing MGKEN['targets'] variable\033[0m")
		exit()
	if type(data['targets']) is not dict:
		print("\033[31mError: Invalid MGKEN['targets'] variable\033[0m")
		exit()
	if len(data['targets']) < 1:
		print("\033[31mError: Empty MGKEN['targets'] variable\033[0m")
		exit()
	for trgname, trgdat in data['targets'].items():
		if 'srcdirs' not in trgdat:
			print("\033[31mError: Missing MGKEN['%s']['srcdirs'] variable\033[0m" % trgname)
			exit()
		if type(trgdat['srcdirs']) is not list:
			print("\033[31mError: Invalid MGKEN['%s']['srcdirs'] variable\033[0m" % trgname)
			exit()
		if len(trgdat['srcdirs']) < 1:
			print("\033[31mError: Empty MGKEN['%s']['srcdirs'] variable\033[0m" % trgname)
			exit()
		for path in trgdat['srcdirs']:
			if type(path) is not str or len(path) < 1:
				print("\033[31mError: Invalid path '%s'\033[0m" % path)
				exit()
		if 'objsuffixes' not in trgdat:
			print("\033[31mError: Missing MGKEN['%s']['objsuffixes'] variable\033[0m" % trgname)
			exit()
		if type(trgdat['objsuffixes']) is not dict:
			print("\033[31mError: Invalid MGKEN['%s']['objsuffixes'] variable\033[0m" % trgname)
			exit()
		if len(trgdat['objsuffixes']) < 1:
			print("\033[31mError: Empty MGKEN['%s']['objsuffixes'] variable\033[0m" % trgname)
			exit()
		for k, suffix in trgdat['objsuffixes'].items():
			if type(suffix) is not str or len(suffix) < 1:
				print("\033[31mError: Invalid suffix '%s:%s'\033[0m" % (k, suffix))
				exit()
		if 'depcmd' in trgdat and (type(trgdat['depcmd']) != str or len(trgdat['depcmd']) < 1):
			print("\033[31mError: Invalid MGKEN['%s']['depcmd'] variable\033[0m" % trgname)
			exit()
		elif 'depcmd' not in trgdat:
			trgdat['depcmd'] = 'ocamldep'

	return data

def sourcefiles_of_directory(path, srcsuffix_dict):
	file_list = []
	print('exploring:', path) #debug
	if not os.path.isdir(path):
		print("\033[33mWarning: No such directory %s\033[0m" % path)
		return []
	for file in os.listdir(path):
		dotpos = file.rfind('.')
		if dotpos < 0:
			continue
		suffix = file[dotpos+1:]
		if suffix in srcsuffix_dict:
			file_list.append((path, file[:dotpos], suffix, srcsuffix_dict[suffix]))
	return file_list


def write_to_trgstream(trgname, trgdat, trgstream, objdir):
	trgstream.write("MKGEN_SRCSBIN_%s :=" % trgname.upper())
	for prefix, body, _, suffix in trgdat['src_list_sorted']:
		if suffix == 'cmi':
			continue
		trgstream.write(" %s/%s/%s.%s" % (objdir, prefix, body, suffix))
	trgstream.write("\n\n")

	for filedep in sorted(trgdat['dep_list']):
		trgstream.write("%s/%s/%s.%s :" % (objdir, filedep[0][0], filedep[0][1],
										filedep[0][2]))
		trgstream.write(" %s/%s.%s" % (filedep[0][0], filedep[0][1]
			, src_to_bin_ext[filedep[0][2]]))
		for dep in sorted(filedep[1]):
			trgstream.write(" %s/%s" % (objdir, dep))
		trgstream.write(" | %s/%s/\n" % (objdir, filedep[0][0]))


if __name__ == "__main__":
	if not os.path.isfile("Makefile"):
		print(("\033[31mError: %s/Makefile missing\033[0m") %(os.getcwd()))
		exit()
	cmd = 'make -pn nosuchrule 2>/dev/null | grep "MKGEN :="'
	print('cmd: \033[32m%s\033[0m' % cmd)

	mkvars = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)\
					   .stdout.read().decode("utf-8");

	data = data_of_makefilevars(mkvars)

	if not os.path.exists("deps"):
		os.mkdir("deps")
	elif not os.path.isdir("deps"):
		print("\033[31mError: ./deps is not a directory\033[0m")
		exit()

	# with open("depend.mk", "w") as mainstream:
	if True:
		for trgname, trgdat in data['targets'].items():
			src_list = []
			for path in trgdat['srcdirs']:
				src_list += sourcefiles_of_directory(path, trgdat['objsuffixes'])
				trgdat['src_list_unsorted'] = src_list

			(src_list_sorted, dep_list) = dependencies_of_data(trgdat)
			del trgdat['src_list_unsorted']
			trgdat['src_list_sorted'] = src_list_sorted
			trgdat['dep_list'] = dep_list

			with open("deps/depend_" + trgname.lower() + ".mk", "w") as trgstream:
				write_to_trgstream(trgname, trgdat, trgstream, data['objdir'])

	# print(data)
