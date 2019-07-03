#!/usr/bin/env python3


from common import *

import re

def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None
conn.create_function("REGEXP", 2, regexp)

# delete automatically-identified excludes
c.execute("""
DELETE FROM ExcludedFragments WHERE CATEGORY IS NOT "MANUAL"
""")

# exclude builtins within comments (/* and //)
c.execute("""
INSERT INTO ExcludedFragments (CATEGORY, CODE_FRAGMENT, BUILTIN_ID)
SELECT "COMMENT", CODE_FRAGMENT, BUILTIN_ID FROM BuiltinsInGithubProjectUnfiltered
LEFT JOIN BuiltinsUnfiltered ON BuiltinsUnfiltered.ID = BuiltinsInGithubProjectUnfiltered.BUILTIN_ID
WHERE CODE_FRAGMENT REGEXP (".*(//)(.*)" || BUILTIN_NAME)
AND FILE_PATH NOT LIKE "%/gcc%/%" AND FILE_PATH NOT LIKE "%/llvm%/%" AND FILE_PATH NOT LIKE "%/clang%/%"
GROUP BY BUILTIN_ID, CODE_FRAGMENT
""")

# exclude builtins with comments (/*)
c.execute("""
INSERT OR IGNORE INTO ExcludedFragments (CATEGORY, CODE_FRAGMENT, BUILTIN_ID)
SELECT "COMMENT", CODE_FRAGMENT, BUILTIN_ID FROM BuiltinsInGithubProjectUnfiltered
LEFT JOIN BuiltinsUnfiltered ON BuiltinsUnfiltered.ID = BuiltinsInGithubProjectUnfiltered.BUILTIN_ID
WHERE CODE_FRAGMENT REGEXP (".*(/\*)([^*]*)" || BUILTIN_NAME)
AND FILE_PATH NOT LIKE "%/gcc%/%" AND FILE_PATH NOT LIKE "%/llvm%/%" AND FILE_PATH NOT LIKE "%/clang%/%"
GROUP BY BUILTIN_ID, CODE_FRAGMENT
""")

# exclude builtins within quotes (line starts with *)
c.execute("""
INSERT OR IGNORE INTO ExcludedFragments (CATEGORY, CODE_FRAGMENT, BUILTIN_ID)
SELECT "COMMENT", CODE_FRAGMENT, BUILTIN_ID FROM BuiltinsInGithubProjectUnfiltered
WHERE CODE_FRAGMENT REGEXP ("^[ \t]*\* .*")
AND FILE_PATH NOT LIKE "%/gcc%/%" AND FILE_PATH NOT LIKE "%/llvm%/%" AND FILE_PATH NOT LIKE "%/clang%/%"
GROUP BY BUILTIN_ID, CODE_FRAGMENT
""")

# exclude builtins in strings
c.execute("""
INSERT OR IGNORE INTO ExcludedFragments (CATEGORY, CODE_FRAGMENT, BUILTIN_ID)
SELECT "QUOTES", CODE_FRAGMENT, BUILTIN_ID FROM BuiltinsInGithubProjectUnfiltered
LEFT JOIN BuiltinsUnfiltered ON BuiltinsUnfiltered.ID = BuiltinsInGithubProjectUnfiltered.BUILTIN_ID
WHERE CODE_FRAGMENT REGEXP ('\".*' || BUILTIN_NAME || '.*\"')
AND FILE_PATH NOT LIKE "%/gcc%/%" AND FILE_PATH NOT LIKE "%/llvm%/%" AND FILE_PATH NOT LIKE "%/clang%/%"
GROUP BY BUILTIN_ID, CODE_FRAGMENT
""")

# sync BuiltinsInGithubProject -> ExcludedFragments
c.execute("""
INSERT INTO ExcludedFragments
    SELECT t1.CODE_FRAGMENT, t1.BUILTIN_ID, "MANUAL" FROM BuiltinsInGithubProjectUnfiltered t1 LEFT JOIN ExcludedFragments t2
        ON t1.CODE_FRAGMENT = t2.CODE_FRAGMENT AND t1.BUILTIN_ID = t2.BUILTIN_ID
        WHERE EXCLUDE=1 AND t2.CODE_FRAGMENT IS NULL
        GROUP BY t1.CODE_FRAGMENT, t1.BUILTIN_ID
""")
# sync ExcludedFragments -> BuiltinsInGithubProject
c.execute("""
UPDATE BuiltinsInGithubProjectUnfiltered
    SET EXCLUDE=1
    WHERE CODE_FRAGMENT IN (SELECT CODE_FRAGMENT FROM ExcludedFragments)
""")

# delete manually-identified builtins if they were also automatically detected
c.execute("""
DELETE FROM ExcludedFragments WHERE CATEGORY = "MANUAL"
    AND CODE_FRAGMENT IN (SELECT CODE_FRAGMENT FROM ExcludedFragments WHERE CATEGORY IS NOT "MANUAL")
""")

# delete manually-identified builtins which exclude only already excluded fragments
c.execute("""
DELETE FROM ExcludedFragments WHERE CODE_FRAGMENT NOT IN (
	SELECT CODE_FRAGMENT FROM BuiltinsInGithubProjectUnfiltered WHERE 
	FILE_PATH NOT LIKE "%/gcc%/%" AND FILE_PATH NOT LIKE "%/llvm%/%" AND FILE_PATH NOT LIKE "%/clang%/%" 
)
""")

conn.commit()
