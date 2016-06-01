# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    ftocamldep.py                                      :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: ngoguey <ngoguey@student.42.fr>            +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2016/06/01 08:07:29 by ngoguey           #+#    #+#              #
#    Updated: 2016/06/01 09:23:59 by ngoguey          ###   ########.fr        #
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

def cmd_from_sourcefiles_per_trgtdir(sourcefiles_per_trgtdir):
	cmd = 'ocamldep -one-line'
	for dirname, _ in sourcefiles_per_trgtdir.items():
		cmd += " -I %s" % dirname
	for _, filelist in sourcefiles_per_trgtdir.items():
		for prefix, filename, suffix in filelist:
			cmd += " %s/%s.%s" % (prefix, filename, suffix)
	return cmd
	# ocamldep -one-line -I src/shared -I src/terminal

def explode_filepath(filepath):
	dotindex = filepath.rindex('.')
	suffix = filepath[dotindex + 1:]
	slashindex = filepath.rindex('/')
	prefix = filepath[:slashindex]
	base = filepath[slashindex + 1:dotindex]
	# print(prefix, base, suffix)
	return (prefix, base, suffix)

def deps_from_rawdeps(rawdeps):
	files_deps = []
	for line in rawdeps.splitlines():
		sides = line.split(' :', 2)
		# print('sides:', sides)
		file_deps = (explode_filepath(sides[0]),
					 [x for x in sides[1].lstrip().split(' ') if x != ''])
		print('filedep: %s' % str(file_deps))
		files_deps.append(file_deps)
	return files_deps

def from_sourcefiles_per_trgtdir(sourcefiles_per_trgtdir):
	cmd = cmd_from_sourcefiles_per_trgtdir(sourcefiles_per_trgtdir)
	print('cmd: \033[32m%s\033[0m' % cmd)
	rawdeps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)\
	            .stdout.read().decode("utf-8");
	deps = deps_from_rawdeps(rawdeps)
	return deps
	# print(rawdeps)
