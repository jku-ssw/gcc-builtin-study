#!/usr/bin/env python3

""" Adds a builtin prefix to a list of function names. This is useful to conveniently paste builtin names into a .def file when the GCC documentation mentions that "functions have corresponding versions prefixed with __builtin_".

For example, enter the following list of names (obtained from  such as in https://gcc.gnu.org/onlinedocs/gcc-7.2.0/gcc/Other-Builtins.html) on stdin and press Ctrl + d:

_exit, alloca, bcmp, bzero, dcgettext, dgettext, dremf, dreml, drem, exp10f, exp10l, exp10, ffsll


The output is the following:
__builtin__exit
__builtin_alloca
__builtin_bcmp
__builtin_bzero
__builtin_dcgettext
__builtin_dgettext
__builtin_dremf
__builtin_dreml
__builtin_drem
__builtin_exp10f
__builtin_exp10l
__builtin_exp10
__builtin_ffsll
"""

import re
import sys

input = ''
for line in sys.stdin:
    input += line

for element in [element.replace(' ','') for element in input.split(',')]:
    print("__builtin_" + element)

