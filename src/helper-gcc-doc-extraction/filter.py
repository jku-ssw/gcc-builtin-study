#!/usr/bin/env python3

""" outputs all __builtin functions from a text

For example, enter the following text on the command line (obtained from https://gcc.gnu.org/onlinedocs/gcc-7.2.0/gcc/Other-Builtins.html) and press Ctrl + d:

Built-in Function: _Floatnx __builtin_huge_valfnx (void)
Similar to __builtin_huge_val, except the return type is _Floatnx.
Built-in Function: int __builtin_fpclassify (int, int, int, int, int, ...)
This built-in implements the C99 fpclassify functionality. The first five int arguments should be the target library’s notion of the possible FP classes and are used for return values. They must be constant values and they must appear in this order: FP_NAN, FP_INFINITE, FP_NORMAL, FP_SUBNORMAL and FP_ZERO. The ellipsis is for exactly one floating-point value to classify. GCC treats the last argument as type-generic, which means it does not do default promotion from float to double.
Built-in Function: double __builtin_inf (void)
Similar to __builtin_huge_val, except a warning is generated if the target floating-point format does not support infinities.
Built-in Function: _Decimal32 __builtin_infd32 (void)
Similar to __builtin_inf, except the return type is _Decimal32.
Built-in Function: _Decimal64 __builtin_infd64 (void)

The output is a list of builtins that can be conveniently pasted into a .def file:

__builtin_fpclassify
__builtin_inf
__builtin_infd64
__builtin_infd32
__builtin_huge_val
__builtin_huge_valfnx
"""

import re
import sys

input = ''
for line in sys.stdin:
    input += line

for match in set(re.findall('__builtin[a-zA-Z_0-9]*', input)):
    print(match)

