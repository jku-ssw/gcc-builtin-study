#!/usr/bin/env python3
from .common import *

"""
Create tables to speed up queries.

SQLite3 executes views on demand (i.e., the results cannot be stored). For many views, accessing them takes a very long time. To speed up the computations, views are persisted in a table using the code in this file.
"""
tables = [
    'GithubProject', 'Builtins', 'UniqueBuiltinsPerProject',
    'UniqueCategoriesPerProject', 'UniqueCategoryCounts',
    'UniqueFileWithUniqueBuiltinNames', 'UniqueBuiltinsGroupedByMachineSpecificPerProject',
    'UniqueBuiltinCounts', 'FileNames', 'DistinctBuiltinCountPerProject',
    'BuiltinsInGithubProject', 'BuiltinFrequencyInGithubProjects',
    'CommitHistoryDiffEntry', 'CommitHistory', 'CommitHistoryAccumulated'
]
for table in tables:
    print(table)
    c.execute('DROP TABLE IF EXISTS ' + table)
    c.execute('CREATE TABLE ' + table + ' AS SELECT * FROM ' + table + 'View')
conn.commit()
