# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    ftocamldep.py                                      :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: ngoguey <ngoguey@student.42.fr>            +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2016/06/01 08:07:29 by ngoguey           #+#    #+#              #
#    Updated: 2016/06/02 09:55:38 by ngoguey          ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

"""
	Read:
src/terminal/main.cmo : src/shared/bar.cmo src/terminal/main.cmi
	Split:
['src/terminal/main.cmo', ' src/shared/bar.cmo src/terminal/main.cmi']
	In fine:
_build/src/terminal/main.cmo : src/terminal/main.ml _build/src/shared/bar.cmo _build/src/terminal/main.cmi | _build/src/terminal/
	Storing:
(('src/terminal', 'main', 'cmo'), ['src/shared/bar.cmo', 'src/terminal/main.cmi'])



"""

import os, subprocess, re

def cmdsuffix_of_data(trgdat):
	cmd = ' -one-line'
	for dirpath in trgdat['srcdirs']:
		cmd += " -I %s" % dirpath
	for prefix, body, suffix, _ in trgdat['src_list_unsorted']:
		cmd += " %s/%s.%s" % (prefix, body, suffix)
	return cmd

def explode_filepath(filepath):
	dotindex = filepath.rindex('.')
	suffix = filepath[dotindex + 1:]
	slashindex = filepath.rindex('/')
	prefix = filepath[:slashindex]
	base = filepath[slashindex + 1:dotindex]
	return (prefix, base, suffix)

def deps_from_rawdeps(rawdeps):
	files_deps = []
	for line in rawdeps.splitlines():
		sides = line.split(' :', 2)
		file_deps = (explode_filepath(sides[0]),
					 [x for x in sides[1].lstrip().split(' ') if x != ''])
		files_deps.append(file_deps)
	return files_deps

def sorted_dependencies_of_data_cmdsuffix(trgdat, cmdsuffix):
	cmd = trgdat['depcmd'] + ' -sort' + cmdsuffix
	print('cmd: \033[32m%s\033[0m' % cmd)
	sortdeps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)\
	            .stdout.read().decode("utf-8");
	srcindex_dict = dict()
	i = 0
	for x in sortdeps.split(' '):
		x = x.strip()
		if x == '':
			continue
		(prefix, base, suffix) = explode_filepath(x)
		srcindex_dict[(prefix, base, suffix, trgdat['objsuffixes'][suffix])] = i
		i += 1
	return sorted(trgdat['src_list_unsorted'],
				  key=lambda tup: srcindex_dict[tup])

def dependencies_of_data_cmdsuffix(trgdat, cmdsuffix):
	cmd = trgdat['depcmd'] + cmdsuffix
	print('cmd: \033[32m%s\033[0m' % cmd)
	rawdeps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)\
						.stdout.read().decode("utf-8");
	return deps_from_rawdeps(rawdeps)


def dependencies_of_data(trgdat): #EXPOSED
	cmdsuffix = cmdsuffix_of_data(trgdat)

	src_list_sorted = sorted_dependencies_of_data_cmdsuffix(trgdat, cmdsuffix)
	dep_list =  dependencies_of_data_cmdsuffix(trgdat, cmdsuffix)
	return (src_list_sorted, dep_list)
