#!/usr/bin/env python3
from include.common import *

# Obtain the data used to plot Figure 1

def get_count(gid, machine_specific, unique):
    if unique:
        table = 'UniqueBuiltinsPerProjectMachineSpecific'
    else:
        table = 'BuiltinsPerProjectMachineSpecific'
    result = c.execute('SELECT usage_count FROM ' + table +' WHERE MACHINE_SPECIFIC=? AND GITHUB_PROJECT_ID=?', (1 if machine_specific else 0, gid)).fetchone()
    if result is None:
        return 0
    else:
        return result[0]

def compute(csvfile, unique=True):
    dir = os.path.dirname(os.path.realpath(__file__))
    csv_file = open(csvfile, 'w')
    csv_file.write('category;count\n')
    gids = (count[0] for count in c.execute('SELECT DISTINCT(GITHUB_PROJECT_ID) FROM BuiltinsPerProjectMachineSpecific').fetchall())
    for gid in gids:
        machine_specific_count = get_count(gid, True, unique)
        machine_independent_count = get_count(gid, False, unique)
        total_count = machine_specific_count + machine_independent_count
        if machine_specific_count != 0:
            csv_file.write('machine-specific;%d\n' % machine_specific_count)
        if machine_independent_count != 0:
            csv_file.write('machine-independent;%d\n' % machine_independent_count)
        csv_file.write('total;%d\n' % total_count)
    csv_file.close()

compute(os.path.join(current_dir, '..', '..', 'generated', 'unique_builtins_per_category.csv'), unique=True)
compute(os.path.join(current_dir, '..', '..', 'generated', 'builtins_per_category.csv'), unique=False)
