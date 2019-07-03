#!/usr/bin/env python3
"""
Reads the def files, and inserts the definitions into the database
"""


import os
from .common import *

all_builtins = set()

def find_files(directory, endings):
    """
    Find all files in the given directory (recursively) that end in one of the extensions.
    """
    for root, dirs, files in os.walk(directory):
        for basename in files:
            for ending in endings:
                if basename.endswith(ending):
                    filename = os.path.join(root, basename)
                    yield filename
for deffile in find_files(os.path.join(os.path.dirname(__file__), '../../defs'), ['.def']):
        category = os.path.basename(deffile.rstrip('.def'))
        machine_specific = "architecture-specific" in deffile
        with open(deffile) as f:
            url = None
            header = None
            lines = [line.rstrip('\n') for line in f.readlines()]
            for line in lines:
                if line.startswith('#'):
                    pass # comment
                elif line.startswith('%'):
                    (key, value) = line.split('=')
                    key = key.strip('%')
                    if key == 'url':
                        url = value
                    elif key == 'header':
                        header = value
                    else:
                        print(line + " is unknown!")
                        exit(-1)
                else:
                    if url is None:
                        print(deffile + " did not define url")
                        exit(-1)
                    elif header is None:
                        print(deffile + " did not define header")
                        exit(-1)
                    if line in all_builtins:
                        print("duplicate " + line + "!")
                        exit(-1)
                    all_builtins.add(line)
                    query = """insert into BuiltinsUnfiltered(
                                    BUILTIN_NAME,
                                    BUILTIN_CATEGORY,
                                    MACHINE_SPECIFIC,
                                    DOCUMENTATION_URL,
                                    DOCUMENTATION_SECTION_HEADER,
                                    FROM_DEF
                                    )

                                    VALUES(?, ?, ?, ?, ?, 1)
                                    """
                    c.execute(query, (line, category, 1 if machine_specific else 0, url, header))
                    print("builtin: " + line)
                    print("category: " + category)
                    print("machine-specific: " + str(machine_specific))
                    print("url: " + url)
                    print("header: " + header)



for deffile in find_files(os.path.join(os.path.dirname(__file__), '../../excludes'), ['.def']):
    category = os.path.basename(deffile.rstrip('.def'))
    with open(deffile) as f:
        url = None
        lines = [line.rstrip('\n') for line in f.readlines()]
        for line in lines:
            if line.startswith('#'):
                pass # comment
            else:
                query = """insert into ExcludedBuiltins(
                                NAME,
                                REASON
                            )
                            VALUES(?, ?)
                        """
                c.execute(query, (line, category))

conn.commit()
