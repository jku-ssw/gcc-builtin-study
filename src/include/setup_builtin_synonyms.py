#!/usr/bin/env python3

# These are the names for Table 2

from .common import *

builtin_synonyms = """
__builtin_expect=compiler interaction
__builtin_clz=bitwise operation
__builtin_bswap32=bitwise operation
__builtin_constant_p=compiler interaction
__builtin_alloca=stack allocation
__builtin_bswap64=bitwise operation
__builtin_ctz=bitwise operation
__builtin_bswap16=bitwise operation
__builtin_clzll=bitwise operation
__builtin_ctzll=bitwise operation
__builtin_unreachable=compiler interaction
__builtin_types_compatible_p=compiler interaction
__builtin_popcount=bitwise operation
__builtin_prefetch=compiler interaction
__builtin_clzl=bitwise operation
__builtin_ffs=bitwise operation
__builtin_popcountll=bitwise operation
__builtin_choose_expr=compiler interaction
__builtin_ctzl=bitwise operation
__builtin_trap=compiler interaction
__builtin_popcountl=bitwise operation
__builtin_huge_val=special value
__builtin_nanf=special value
__builtin_huge_valf=special value
__builtin_inf=special value
__builtin_memcpy=libc
__builtin_memset=libc
__builtin_memcmp=libc
__builtin_strlen=libc
"""

c.execute('DELETE FROM BuiltinCategorySynonyms')

lines = builtin_synonyms.split('\n')
for line in lines:
    if line != '':
        left = line.split('=')[0]
        right = line.split('=')[1]
        print(left + "=" + right)
        query = """insert into BuiltinCategorySynonyms(
                                    BUILTIN_NAME,
                                    CATEGORY_SYNONYM
                                    )

                                    VALUES(?, ?)
                                    """
        c.execute(query, (left, right))
conn.commit()
