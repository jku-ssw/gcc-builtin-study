#!/usr/bin/env python3

""" Set up the database to re-run the BuiltAnalyzer"""

from include.common import *

c.execute("UPDATE GithubProjectUnfiltered SET MAKEFILE_CONTAINS_FREESTANDING=NULL, MAKEFILE_CONTAINS_NO_PLUGIN=NULL, PROCESSED=0, NR_INLINE_ASSEMBLY_FRAGMENT=NULL, CONTAINS_MAKEFILE=NULL")
conn.commit()
c.execute("DELETE FROM BuiltinsInGithubProjectUnfiltered")
conn.commit()
c.execute("DELETE FROM BuiltinsUnfiltered")
c.execute("DELETE FROM sqlite_sequence where name='BuiltinsUnfiltered'")
conn.commit()
c.execute("DELETE FROM ExcludedBuiltins")
conn.commit()

from include.setupdefs import *
from include.setup_builtin_synonyms import *
from include.sync_views_to_tables import *
