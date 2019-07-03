#!/usr/bin/env python3

from include.common import *

analyze_up_to = 5000
print_table_up_to = 10

def print_builtin_decision(csv_file, id, ids, i, print_latex_table, decision):
    query = "SELECT ID, BUILTIN_NAME, count FROM UniqueBuiltinCounts WHERE ID = ?"
    result = c.execute(query, (id,)).fetchone()
    total_count_percentage_query = "SELECT 100-COUNT(DISTINCT GITHUB_PROJECT_ID) * 100.0 / (SELECT COUNT(DISTINCT GITHUB_PROJECT_ID) FROM TempUniqueBuiltinsPerProject), (SELECT COUNT(DISTINCT GITHUB_PROJECT_ID) FROM TempUniqueBuiltinsPerProject) - COUNT(DISTINCT GITHUB_PROJECT_ID) FROM TempUniqueBuiltinsPerProject WHERE ID NOT IN (" + "?," * (len(ids)-1) + "?)"
    total_count_percentage = c.execute(total_count_percentage_query, ids).fetchone()
    if i <= print_table_up_to and print_latex_table:
        print("%s & %0.2f & %d \\\\" % (escape_latex(result[1]), total_count_percentage[0], total_count_percentage[1]))
    csv_file.write("%d;%0.2f;%s;%s\n" % (i, total_count_percentage[0], decision, result[1]))
    csv_file.flush()

def get_nr_unsupported_projects_temp(project_ids):
    if len(project_ids) == 0:
        count_unsupported_projects_query = "SELECT COUNT(DISTINCT GITHUB_PROJECT_ID) FROM TempUniqueBuiltinsPerProject"
    else:
        count_unsupported_projects_query = "SELECT COUNT(DISTINCT GITHUB_PROJECT_ID) FROM TempUniqueBuiltinsPerProject WHERE ID NOT IN (" + "?," * (len(project_ids)-1) + "?)"
    count_unsupported_projects = c.execute(count_unsupported_projects_query, project_ids).fetchone()[0]
    return count_unsupported_projects

def create_temp_table():
    c.execute("""
    DROP TABLE IF EXISTS TempUniqueBuiltinsPerProject
    """)
    c.execute("""
    CREATE TABLE TempUniqueBuiltinsPerProject AS
    SELECT * FROM UniqueBuiltinsPerProject WHERE BUILTIN_CATEGORY IS NOT 'Unknown'
    """)
    conn.commit()

def drop_temp_table():
    c.execute("""
    DROP TABLE TempUniqueBuiltinsPerProject
    """)
    conn.commit()

def compute(file_name, assume_libc_builtins_to_already_be_implemented, assume_platform_specific_builtins_to_already_be_implemented, print_latex_table=False):
    csv_file = open(file_name, 'w')
    csv_file.write('nr_builtins;perc_projects;decision;name\n')
    create_temp_table()
    builtin_ids, selected_ids = get_start_configuration(assume_libc_builtins_to_already_be_implemented, assume_platform_specific_builtins_to_already_be_implemented)
    if print_latex_table:
        print_tabular_start(name="implementationordertable", columns=3, caption="Greedy order of implementing builtins and cumulative percentage and number of supported projects")
        print("Builtin & \% projects & \# projects \\\\")
        print("\\midrule{}%")
    min_progress = 1
    for i in range(1, analyze_up_to+1):
        if len(builtin_ids) == 0:
            break
        min_unsupported_projects_count = None
        min_unsupported_projects_id = None
        unsupported_without_new_project = get_nr_unsupported_projects_temp(selected_ids)
        for builtin_id in builtin_ids:
            test_selected_ids = selected_ids + [builtin_id]
            count_unsupported_projects = get_nr_unsupported_projects_temp(test_selected_ids)
            if (min_unsupported_projects_count is None or count_unsupported_projects < min_unsupported_projects_count) and (unsupported_without_new_project >= count_unsupported_projects - min_progress):
                min_unsupported_projects_id = builtin_id
                min_unsupported_projects_count = count_unsupported_projects
        no_greedy_candidate = min_unsupported_projects_id is None
        if no_greedy_candidate:
            min_unsupported_projects_id = c.execute("SELECT ID FROM TempUniqueBuiltinsPerProject WHERE ID NOT IN (" + "?," * (len(selected_ids)-1) + "?) ORDER BY github_project_count DESC LIMIT 1 ", selected_ids).fetchone()[0]
        selected_ids += [min_unsupported_projects_id]
        print_builtin_decision(csv_file, min_unsupported_projects_id, selected_ids, i, print_latex_table, 'most-frequent' if no_greedy_candidate else 'greedy')
        builtin_ids.remove(min_unsupported_projects_id)
    if print_latex_table:
        print_tabular_end(label="tbl:implementationorder")
    csv_file.close()
    drop_temp_table()

def get_start_configuration(assume_libc_builtins_to_already_be_implemented, assume_platform_specific_builtins_to_already_be_implemented):
    if assume_platform_specific_builtins_to_already_be_implemented and assume_libc_builtins_to_already_be_implemented:
        builtin_candidates = 'SELECT ID FROM UniqueBuiltinCounts WHERE BUILTIN_CATEGORY IS NOT "Unknown" AND MACHINE_SPECIFIC IS NOT 1 AND BUILTIN_CATEGORY IS NOT "other-libc"'
        start_ids = [row[0] for row in c.execute('SELECT ID FROM UniqueBuiltinCounts WHERE MACHINE_SPECIFIC IS NOT 1 OR BUILTIN_CATEGORY IS "other-libc"').fetchall()]
    elif assume_platform_specific_builtins_to_already_be_implemented:
        builtin_candidates = 'SELECT ID FROM UniqueBuiltinCounts WHERE BUILTIN_CATEGORY IS NOT "Unknown" AND MACHINE_SPECIFIC IS NOT 1'
        start_ids = [row[0] for row in c.execute('SELECT ID FROM UniqueBuiltinCounts WHERE MACHINE_SPECIFIC IS 1').fetchall()]
    elif assume_libc_builtins_to_already_be_implemented:
        builtin_candidates = 'SELECT ID FROM UniqueBuiltinCounts WHERE BUILTIN_CATEGORY IS NOT "Unknown" AND BUILTIN_CATEGORY IS NOT "other-libc"'
        start_ids = [row[0] for row in c.execute('SELECT ID FROM UniqueBuiltinCounts WHERE BUILTIN_CATEGORY IS "other-libc"').fetchall()]
    else:
        builtin_candidates = 'SELECT ID FROM UniqueBuiltinCounts WHERE BUILTIN_CATEGORY IS NOT "Unknown"'
        start_ids = []
    builtin_candidate_ids = [row[0] for row in c.execute(builtin_candidates).fetchall()]
    return (builtin_candidate_ids, start_ids)

# Selects the implementation order by choosing the most frequent builtin
def by_frequency(file_name, assume_libc_builtins_to_already_be_implemented, assume_platform_specific_builtins_to_already_be_implemented):
    create_temp_table()
    csv_file = open(file_name, 'w')
    csv_file.write('nr_builtins;perc_projects;decision;name\n')
    builtin_ids, selected_ids = get_start_configuration(assume_libc_builtins_to_already_be_implemented, assume_platform_specific_builtins_to_already_be_implemented)
    for i in range(1, analyze_up_to+1):
        if len(builtin_ids) == 0:
            break
        current_id = builtin_ids.pop(0)
        selected_ids += [current_id]
        count_unsupported_projects = get_nr_unsupported_projects_temp(selected_ids)
        print_builtin_decision(csv_file, current_id, selected_ids, i, False, 'most-frequent')
    csv_file.close()
    drop_temp_table()

by_frequency(current_dir + '/../../generated/most-frequent-all.csv', False, False)
by_frequency(current_dir + '/../../generated/most-frequent-machine-independent.csv', False, True)
compute(current_dir + '/../../generated/greedy-all.csv', False, False, print_latex_table=True)
compute(current_dir + '/../../generated/greedy-machine-independent.csv', False, True)
