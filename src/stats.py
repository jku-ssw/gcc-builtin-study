#!/usr/bin/env python3

# This file generates various latex commands used in the paper as well as two CSV files used to create Figure 2.

from include.common import *
import os

builtin_template = """
SELECT DOCUMENTATION_SECTION_HEADER, COUNT(BUILTIN_NAME), 100-not_found * 100.0 / COUNT(BUILTIN_NAME) as found_percentage
    FROM Builtins LEFT JOIN (
        SELECT BUILTIN_CATEGORY, COUNT(ID) as not_found FROM Builtins
            WHERE Builtins.ID NOT IN (SELECT ID FROM UniqueBuiltinCounts) AND FROM_DEF=1 GROUP BY Builtins.BUILTIN_CATEGORY
    )
    t1 ON t1.BUILTIN_CATEGORY = Builtins.BUILTIN_CATEGORY WHERE MACHINE_SPECIFIC=%s GROUP BY Builtins.BUILTIN_CATEGORY, DOCUMENTATION_SECTION_HEADER ORDER BY DOCUMENTATION_SECTION_HEADER"""

def minimizeCategoryHeader(s):
    """
    6.60.1 AArch64 Built-in Functions -> 6.60.1 AArch64
    """
    to_remove = [
        "through Built-in Functions",
        "Built-in Functions",
        "Intrinsics"
    ]
    result = escape_latex(s)
    for remove in to_remove:
        result = result.replace(remove, "")
    return result

def create_platform_dependent_builtins_csv(file_path, platform_dependent):
    query = """SELECT BUILTIN_CATEGORY, count FROM UniqueCategoryCounts WHERE MACHINE_SPECIFIC=%d""" % (1 if platform_dependent else 0, )
    csv_file = open(file_path, 'w')
    csv_file.write('category;projects\n')
    for entry in c.execute(query):
        csv_file.write("%s;%s\n" % (entry[0], entry[1]))
    csv_file.close()

def print_projects_with_most_unique_builtins_table(limit = 15):
    print_tabular_start(name="builtintablemostbuiltins", columns=3, caption="Projects with most unique builtins")
    print("URL (starting with https://github.com/) & KLOC & unique builtins \\\\")
    print("\\midrule{}%")
    for row in c.execute("SELECT GITHUB_URL, (CLOC_LOC_C + CLOC_LOC_H)/1000 AS LOC, count FROM DistinctBuiltinCountPerProject LIMIT %d" % (limit,)):
        print("\\href{http://github.com/%s}{%s} & %d & %d \\\\" % (escape_latex(row[0].replace("https://github.com/", "")), escape_latex(row[0].replace("https://github.com/", "")), row[1], row[2]))
    print_tabular_end(label="tbl:mostbuiltins")

def print_projects_with_most_builtins_table(limit = 15):
    print_tabular_start(name="builtintablemostnonuniquebuiltins", columns=3, caption="Projects with most builtins")
    print("URL (starting with https://github.com/) & KLOC & unique builtins \\\\")
    print("\\midrule{}%")
    for row in c.execute("SELECT GITHUB_URL, (CLOC_LOC_C + CLOC_LOC_H)/1000 AS LOC, COUNT(BUILTIN_ID) as count FROM BuiltinsInGithubProject GROUP BY GITHUB_PROJECT_ID ORDER BY count desc  LIMIT %d" % (limit,)):
        print("\\href{http://github.com/%s}{%s} & %d & %d \\\\" % (escape_latex(row[0].replace("https://github.com/", "")), escape_latex(row[0].replace("https://github.com/", "")), row[1], row[2]))
    print_tabular_end(label="tbl:mostnonuniquebuiltins")

def print_machine_specific_builtin_table():
    print_tabular_start(name="builtintablemachinespecific", columns=3, caption="Architecture-specific builtins")
    print("category & \# builtins & \% used \\\\")
    print("\\midrule{}%")
    for row in c.execute(builtin_template % (1,)):
        print("%s & %d & %.1f \\\\" % (minimizeCategoryHeader(row[0]), row[1], 100 if row[2] is None else row[2]))
    print_tabular_end(label="tbl:machinespecificbuiltins")

def print_machine_independent_builtin_table():
    print_tabular_start(name="builtintablemachineindependent", columns=3, caption="Architecture-independent builtins")
    print("category & \# builtins & \% used \\\\")
    print("\\midrule{}%")
    for row in c.execute(builtin_template % (0,)):
        print("%s & %d & %.1f \\\\" % (minimizeCategoryHeader(row[0]), row[1], 100 if row[2] is None else row[2]))
    print_tabular_end(label="tbl:machineindependentbuiltins")

def print_trend_table():
    print_tabular_start(name="trendtable", columns=2, caption="Builtin trends in projects")
    print("trend & \# builtins\\\\")
    print("\\midrule{}%")
    for row in c.execute("SELECT TREND, COUNT(*) as count FROM BuiltinTrendInGithubProjectUnfiltered GROUP BY TREND ORDER BY count DESC"):
        print("%s & %d \\\\" % (row[0], row[1]))
    print_tabular_end(label="tbl:trendtable")

def unused_builtins_table():
    print_tabular_start(name="unusedbuiltintable", columns=2, caption="Builtins explained in the GCC docs but not found in projects")
    print("category & number of unused instructions \\\\")
    print("\\midrule{}%")
    for row in c.execute("SELECT BUILTIN_CATEGORY, COUNT(ID) FROM Builtins WHERE Builtins.ID NOT IN (SELECT ID FROM UniqueBuiltinCounts) AND FROM_DEF=1 GROUP BY BUILTIN_CATEGORY"):
        print("%s & %d \\\\" % (minimizeCategoryHeader(row[0]), row[1]))
    print_tabular_end(label="tbl:unusedbuiltins")

def print_commit_most_influenced_builtins_table(added, consider_first_commit=True, limit=15):
    prefix = "added" if added else "removed"
    postfix = "" if consider_first_commit else "withoutfirstcommit"
    print_tabular_start(name="commitmost" + prefix + "builtintable" + postfix, columns=4, caption="Commit that " + prefix + " most builtins" + ("" if consider_first_commit else " (without the first five commits)"))
    print("github project & commit message & " + prefix + " builtins & commit nr \\\\")
    print("\\midrule{}%")
    order = "DESC" if added else "ASC"
    for row in c.execute("SELECT GITHUB_PROJECT_NAME, COMMIT_MESSAGE, CUR_NUMBER_BUILTINS, COMMIT_NR FROM CommitHistoryAccumulated WHERE CUR_NUMBER_BUILTINS IS NOT NULL " + ("" if consider_first_commit else "AND COMMIT_NR > 5") + " ORDER BY CUR_NUMBER_BUILTINS " + order + " LIMIT " + str(limit)):
        print("%s & %s & %d & %d \\\\" % (escape_latex(row[0]), escape_latex(row[1].split('\n', 1)[0]), row[2], row[3]))
    print_tabular_end(label="tbl:commitmost" + prefix + postfix)   

def print_users_with_most_builtin_commits(positive, negative, limit=20):
    if positive and negative:
        postfix = "positivenegative"
        captionadd = ""
        where_condition = ""
    elif positive:
        postfix = "positive"
        captionadd = " (additions only)"
        where_condition = "WHERE CUR_NUMBER_BUILTINS > 0"
    elif negative:
        postfix = "negative"
        captionadd = " (deletions only)"
        where_condition = "WHERE CUR_NUMBER_BUILTINS < 0"
    else:
        error()
    query = "SELECT COMMITTER_NAME, COMMITTER_EMAIL, COUNT(CUR_NUMBER_BUILTINS) as sum, COUNT(DISTINCT GITHUB_PROJECT_ID) nr_projects FROM CommitHistoryAccumulated " + where_condition + " GROUP BY COMMITTER_NAME, COMMITTER_EMAIL ORDER BY sum DESC LIMIT " + str(limit)
    print_tabular_start(name="userswithmostcommits" + postfix, columns=4, caption="Committers with the highest number of builtin-related commits" + captionadd)
    print("name & email & nr builtin-related commits & nr projects \\\\")
    print("\\midrule{}%")
    for row in c.execute(query):
        print("%s & %s & %d & %d \\\\" % (escape_latex(row[0]), escape_latex(row[1].split('\n', 1)[0]), row[2], row[3]))
    print_tabular_end(label="tbl:userswithmostcommits" + postfix)           

def most_frequent_file_names(limit=10):
    print_tabular_start(name="mostfrequentfilestable", columnstext="p{1.0cm} p{0.5cm} p{0.5cm} p{0.5cm} p{4.5cm}", caption="The %s most frequent file names and their average number of builtins" % (limit,))
    print("file name & average \# of builtins & \# builtins sets & \# projects & most frequent builtin set (stripped the \code{\_\_builtin\_} prefix) \\\\")
    print("\\midrule{}%")
    for row in c.execute("SELECT file_name, AVG(builtin_count), COUNT(DISTINCT GITHUB_PROJECT_ID) as count FROM (select replace(FILE_PATH, rtrim(FILE_PATH, replace(FILE_PATH, '/', '')), '') as file_name, GITHUB_PROJECT_ID, COUNT(DISTINCT BUILTIN_ID) as builtin_count, group_concat(DISTINCT BUILTIN_NAME) as builtin_names from BuiltinsInGithubProject, Builtins WHERE Builtins.ID = BuiltinsInGithubProject.BUILTIN_ID GROUP BY GITHUB_PROJECT_ID, file_name) GROUP BY file_name ORDER BY count DESC LIMIT " + str(limit)).fetchall():
        inner_result = c.execute("SELECT BUILTIN_NAMES, COUNT(*) FROM UniqueFileWithUniqueBuiltinNames WHERE file_name = ? ORDER BY COUNT LIMIT 1", (row[0],)).fetchone()
        builtin_names = ', '.join(escape_latex(inner_result[0].replace('__builtin_', '')).split(','))
        nr_different_builtin_names = inner_result[1]
        print("%s & %.1f & %d & %d & %s \\\\" % (escape_latex(row[0]), row[1], nr_different_builtin_names, row[2], builtin_names))
    print_tabular_end(label="tbl:mostfrequentfiles")
    
def print_project_stats_table():
    print_tabular_start(name="projectstatstable", columns=5, caption="Overview of the projects obtained (after filtering); the first commit in 1984 stems from a project that was converted from another version-control system.")
    print("Metric & Minimum & Maximum & Average & Median \\\\")
    print("\\midrule{}%")
    result = conn.execute('SELECT "C LOC", MIN(CLOC), MAX(CLOC)/1000000, AVG(CLOC)/1000, (SELECT CLOC/1000 FROM GithubProject ORDER BY CLOC ASC LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM GithubProject)) FROM GithubProject').fetchone()
    print("%s & %s & %sM & %dk & %sk \\\\" % result)
    result = conn.execute('SELECT "\# commits", MIN(GIT_NR_COMMITS), MAX(GIT_NR_COMMITS)/1000, AVG(GIT_NR_COMMITS), (SELECT GIT_NR_COMMITS FROM GithubProject ORDER BY CLOC ASC LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM GithubProject)) FROM GithubProject').fetchone()
    print("%s & %s & %dk & %d & %s \\\\" % result)
    # it seems that there is an off-by-one error
    result = conn.execute('SELECT "\# committers", MIN(GIT_NR_COMMITTERS-1), MAX(GIT_NR_COMMITTERS-1)/1000, AVG(GIT_NR_COMMITTERS-1), (SELECT GIT_NR_COMMITTERS-1 FROM GithubProject ORDER BY CLOC ASC LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM GithubProject)) FROM GithubProject').fetchone()
    print("%s & %s & %dk & %d & %s \\\\" % result)
    result = conn.execute('SELECT "first commit", MIN(GIT_FIRST_COMMIT_DATE), MAX(GIT_FIRST_COMMIT_DATE), "-", (SELECT GIT_FIRST_COMMIT_DATE FROM GithubProject ORDER BY CLOC ASC LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM GithubProject)) FROM GithubProject WHERE GIT_FIRST_COMMIT_DATE > 1971').fetchone()
    print("%s & %s & %s & %s & %s \\\\" % result)
    result = conn.execute('SELECT "last commit", MIN(GIT_LAST_COMMIT_DATE), MAX(GIT_LAST_COMMIT_DATE), "-", (SELECT GIT_LAST_COMMIT_DATE FROM GithubProject ORDER BY CLOC ASC LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM GithubProject)) FROM GithubProject').fetchone()
    print("%s & %s & %s & %s & %s \\\\" % result)
    print_tabular_end(label="tbl:projectstatstable")

def disk_usage(path):
    st = os.statvfs(path)
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    return used

def print_unused_builtins():
    template = """
        SELECT group_concat(BUILTIN_NAME)
            FROM Builtins t1
                WHERE t1.ID NOT IN (SELECT ID FROM UniqueBuiltinCounts) AND BUILTIN_CATEGORY=? GROUP BY t1.BUILTIN_CATEGORY
    """
    def join_builtins(builtins):
        escaped = escape_latex(builtins).split(',')
        return ', '.join(escaped[:-1]) + ', and ' + escaped[-1]
    
    not_used_overflow_builtins = conn.execute(template, ('overflow',)).fetchone()[0]
    not_used_other_libc_builtins = conn.execute(template, ('other-libc',)).fetchone()[0]
    not_used_other_builtins = conn.execute(template, ('other',)).fetchone()[0]
    #not_used_object_size_builtins = conn.execute(template, ('object-size',)).fetchone()[0]
    print_as_command('unusedOverflowBuiltins', join_builtins(not_used_overflow_builtins))
    print_as_command('unusedOtherLibcBuiltins', join_builtins(not_used_other_libc_builtins))
    print_as_command('unusedOtherBuiltins', join_builtins(not_used_other_builtins))
    print_as_command('nrUnusedOverflowBuiltins', len(not_used_overflow_builtins))
    print_as_command('nrUnusedOtherLibcBuiltins', len(not_used_other_libc_builtins))
    print_as_command('nrUnusedOtherBuiltins', len(not_used_other_builtins))
    #print_as_command('unusedOBjectSizeBuiltins', join_builtins(not_used_object_size_builtins))

def print_unused_commands():
    query = """
    SELECT BUILTIN_CATEGORY, COUNT(ID) as not_found, (COUNT(ID) * 100.0 / (SELECT COUNT(*) FROM Builtins as t2 WHERE t1.BUILTIN_CATEGORY = t2.BUILTIN_CATEGORY)) as not_found_percentage 
        FROM Builtins t1
            WHERE t1.ID NOT IN (SELECT ID FROM UniqueBuiltinCounts) AND FROM_DEF=1 GROUP BY t1.BUILTIN_CATEGORY ORDER BY not_found_percentage DESC
    """
    for row in c.execute(query):
        strippedString = ''.join(i for i in row[0].replace('-', '') if not i.isdigit())
        nrCommand = "nrUnused" + strippedString
        percentageCommand = "percentageUnused" + strippedString
        print_as_command(nrCommand, row[1])
        print_as_command(percentageCommand, row[2], percentage=True)

def print_trend_counts():
    for row in c.execute("""
SELECT * FROM BuiltinTrendsFinalDecisionSummaryView
UNION
SELECT TREND, COUNT(*), (COUNT(*) * 100.0)/(SELECT COUNT(*) FROM GithubProject WHERE CHECKED_HISTORY = 1) FROM BuiltinTrendInGithubProjectUnfiltered WHERE user='automatic'
UNION
SELECT "not automatic", COUNT(*), (COUNT(*) * 100.0)/(SELECT COUNT(*) FROM GithubProject WHERE CHECKED_HISTORY = 1) FROM BuiltinTrendInGithubProjectUnfiltered WHERE USER = 'manuel'
UNION
SELECT 'increasing', SUM(count), SUM(perc) FROM BuiltinTrendsFinalDecisionSummaryView WHERE decision in ("mostly increasing", "stable, then increasing")
UNION
SELECT 'stagnant', SUM(count), SUM(perc) FROM BuiltinTrendsFinalDecisionSummaryView WHERE decision in ("increasing, then stable", "spike, then stable", "mostly stable")
"""):
        command = row[0].replace(' ', '').replace(',', '').replace('5', 'five')
        print_as_command('nr' + command, row[1])
        print_as_command('percentage' + command, row[2], percentage=True)

def print_manual_classification_counts():
    for row in c.execute("SELECT * FROM BuiltinTrendsFinalDecisionSummaryView"):
        command = row[0].replace(' ', '').replace(',', '').replace('5', 'five')
        print_as_command('nr' + command, row[1])
        print_as_command('percentage' + command, row[2], percentage=True)

from statistics import median
def print_median_values():
    for trend in c.execute("SELECT DISTINCT TREND FROM BuiltinTrendInGithubProjectUnfiltered").fetchall():
        values = c.execute("SELECT COUNT(*) FROM CommitHistoryAccumulated, BuiltinTrendInGithubProjectUnfiltered WHERE CommitHistoryAccumulated.GITHUB_PROJECT_ID = BuiltinTrendInGithubProjectUnfiltered.GITHUB_PROJECT_ID AND CommitHistoryAccumulated.CUR_NUMBER_BUILTINS != 0 AND TREND IS ? GROUP BY TREND, CommitHistoryAccumulated.GITHUB_PROJECT_ID", (trend[0],)).fetchall()
        counts = [value[0] for value in values]
        med = median(counts)
        print_as_command('median' + trend[0].replace(' ', '').replace(',', '').replace('5', 'five'), med)

def print_small_builtin_table(limit=10):
    print_tabular_start(name="smallbuiltintable", columns=3, caption="The " + str(limit) + " most frequent builtins.")
    print("builtin & category & projects\\\\")
    print("\\midrule{}%")
    for row in conn.execute('SELECT UniqueBuiltinCounts.BUILTIN_NAME, BUILTIN_CATEGORY, count, count*100.0/(SELECT COUNT(DISTINCT GITHUB_PROJECT_ID) FROM BuiltinsInGithubProject), CATEGORY_SYNONYM FROM UniqueBuiltinCounts LEFT JOIN BuiltinCategorySynonyms ON UniqueBuiltinCounts.BUILTIN_NAME = BuiltinCategorySynonyms.BUILTIN_NAME ORDER BY count desc LIMIT ?;', (limit,)):
        if row[4] != None:
            category = escape_latex(row[1]).rstrip('-libc') + ' (' + row[4] + ')'
        else:
            category = escape_latex(row[1])
        print("%s & %s & %d / %.1f\%%\\\\" % (escape_latex(row[0]), category, row[2], row[3]))
    print_tabular_end(label="tbl:smallbuiltintable")


def print_builtin_table(limit=100):
    # print latex table
    nr_entries = limit
    columns = 2
    max_column_entries = int((nr_entries+ nr_entries%columns) / columns)
    entries = [''] * max_column_entries
    print("""\\newcommand{\\builtintable}{
\\begin{table*}
\\footnotesize
\\caption{The """ + str(limit) + """ most frequent builtins}
\\label{tbl:common-instructions}
\\begin{tabular}{l l r r """ + ("|l l r r" * (columns-1)) + """}
\\toprule{}
builtin & category & \\# projects & \\% projects""" + (' & builtin & category & \\# projects & \\% projects' * (columns-1)) + """ \\\\
\\midrule{}
""")
    i = 0
    for row in conn.execute('SELECT UniqueBuiltinCounts.BUILTIN_NAME, BUILTIN_CATEGORY, count, count*100.0/(SELECT COUNT(DISTINCT GITHUB_PROJECT_ID) FROM BuiltinsInGithubProject), CATEGORY_SYNONYM FROM UniqueBuiltinCounts LEFT JOIN BuiltinCategorySynonyms ON UniqueBuiltinCounts.BUILTIN_NAME = BuiltinCategorySynonyms.BUILTIN_NAME ORDER BY count desc LIMIT ?;', (limit,)):
        if i >= max_column_entries:
            entries[i % max_column_entries] += ' & '
        if row[4] != None:
            category = escape_latex(row[1]).rstrip('-libc') + ' (' + row[4] + ')'
        else:
            category = escape_latex(row[1])
        entries[i % max_column_entries] += "%s & %s & %s & %.1f" % (escape_latex(row[0]), category, row[2], row[3])
        i += 1
    j = 1
    for entry in entries:
        print(entry + '\\\\')
        if j != len(entries):
            print('\cmidrule(lr){1-' + str(columns*4) +'}')
        j += 1
    print("""\\bottomrule{}
\\end{tabular}
\\label{tbl:common-builtins}
\\end{table*}}""")

create_platform_dependent_builtins_csv(os.path.join(current_dir, '..', '..', 'generated', 'platform-specific-builtins-in-projects.csv'), True)
create_platform_dependent_builtins_csv(os.path.join(current_dir, '..', '..', 'generated', 'platform-independent-builtins-in-projects.csv'), False)

print('% number of search terms')
#print_query_as_command('nrDefTerms', 'SELECT COUNT(*) FROM Builtins WHERE FROM_DEF=1')
print_query_as_command('nrTotalTerms', 'SELECT COUNT(*) FROM BuiltinsUnfiltered WHERE BUILTIN_CATEGORY IS NOT "Unknown" AND BUILTIN_NAME NOT IN (SELECT NAME FROM ExcludedBuiltins)')

print('% number of builtins')
print_query_as_command('nrBuiltins', 'SELECT COUNT(*) FROM Builtins')
print('% number of architecture-specific builtins')
print_query_as_command('nrArchitectureSpecificBuiltins', 'SELECT COUNT(*), BUILTIN_NAME FROM BuiltinsUnfiltered WHERE MACHINE_SPECIFIC=1 AND FROM_DEF=1 AND BUILTIN_NAME NOT IN (SELECT NAME FROM ExcludedBuiltins)')
print('% number of machine-independent builtins')
print_query_as_command('nrArchitectureIndependentBuiltins', 'SELECT COUNT(*), BUILTIN_NAME FROM BuiltinsUnfiltered WHERE MACHINE_SPECIFIC=0 AND FROM_DEF=1 AND BUILTIN_NAME NOT IN (SELECT NAME FROM ExcludedBuiltins)')
print_query_as_command('nrGCCInternalBuiltins', 'SELECT COUNT(*) FROM BuiltinsUnfiltered WHERE BUILTIN_CATEGORY = "GCC internal" AND BUILTIN_NAME NOT IN (SELECT NAME FROM ExcludedBuiltins)')
print_query_as_command('nrNotDefBuiltins', 'SELECT COUNT(*) FROM Builtins WHERE FROM_DEF=0 AND BUILTIN_NAME NOT IN (SELECT NAME FROM ExcludedBuiltins)')
print_query_as_command('nrUnknownBuiltins', 'SELECT COUNT(*) FROM BuiltinsUnfiltered WHERE BUILTIN_CATEGORY = "Unknown"')
print_query_as_command('nrDefBuiltins', 'SELECT COUNT(*) FROM BuiltinsUnfiltered WHERE FROM_DEF=1 AND BUILTIN_NAME NOT IN (SELECT NAME FROM ExcludedBuiltins)')
print_query_as_command('nrUsedBuiltins', 'SELECT COUNT(*) FROM UniqueBuiltinCounts')

print('% number of unfiltered projects')
print_query_as_command('nrProjectsUnfiltered', 'SELECT COUNT(*) FROM GithubProjectUnfiltered WHERE PROCESSED=1')
print('% number of total projects')
print_query_as_command('nrProjects', 'SELECT COUNT(*) FROM GithubProject')
print('% project with fewest stars')
print_query_as_command('nrFromStars', 'SELECT MIN(GITHUB_NR_STARGAZERS) FROM GithubProject')
print('% project with most stars')
print_query_as_command('nrToStars', 'SELECT MAX(GITHUB_NR_STARGAZERS) FROM GithubProject')
print('% total million lines of C code')
print_query_as_command('totalMLoc', 'SELECT SUM(CLOC_LOC_H+CLOC_LOC_C)/1000000 FROM GithubProject')
print_as_command('diskSpaceOccupiedGB', disk_usage('../projects') / 1073741824, roundn=True)

print('% max number of builtins per project')
print_query_as_command('maxNrBuiltinsPerProject', 'SELECT MAX(count) FROM (SELECT COUNT(BUILTIN_ID) count FROM BuiltinsInGithubProject GROUP BY GITHUB_PROJECT_ID ORDER BY count)')
print('% avg number of builtins per project')
print_query_as_command('avgNrBuiltinsPerProject', 'SELECT AVG(count) FROM (SELECT COUNT(BUILTIN_ID) count FROM BuiltinsInGithubProject GROUP BY GITHUB_PROJECT_ID ORDER BY count)', roundn=True)
print_query_as_command('medianNrBuiltinsPerProject', 'SELECT COUNT(BUILTIN_ID) count FROM BuiltinsInGithubProject GROUP BY GITHUB_PROJECT_ID ORDER BY count LIMIT 1 OFFSET (SELECT COUNT(DISTINCT GITHUB_PROJECT_ID)/2 FROM BuiltinsInGithubProject)')
print_query_as_command('medianNrMachineSpecificBuiltinsPerProject', 'SELECT COUNT(BUILTIN_ID) count FROM BuiltinsInGithubProject LEFT JOIN Builtins ON BuiltinsInGithubProject.BUILTIN_ID = Builtins.ID WHERE MACHINE_SPECIFIC=1 GROUP BY GITHUB_PROJECT_ID ORDER BY count LIMIT 1 OFFSET (SELECT COUNT(DISTINCT GITHUB_PROJECT_ID)/2 FROM BuiltinsInGithubProject LEFT JOIN Builtins ON BuiltinsInGithubProject.BUILTIN_ID = Builtins.ID WHERE MACHINE_SPECIFIC=1)')
print_query_as_command('medianNrMachineIndependentBuiltinsPerProject', 'SELECT COUNT(BUILTIN_ID) count FROM BuiltinsInGithubProject LEFT JOIN Builtins ON BuiltinsInGithubProject.BUILTIN_ID = Builtins.ID WHERE MACHINE_SPECIFIC=0 GROUP BY GITHUB_PROJECT_ID ORDER BY count LIMIT 1 OFFSET (SELECT COUNT(DISTINCT GITHUB_PROJECT_ID)/2 FROM BuiltinsInGithubProject LEFT JOIN Builtins ON BuiltinsInGithubProject.BUILTIN_ID = Builtins.ID WHERE MACHINE_SPECIFIC=0)')


print('% total number of k builtins')
print_query_as_command('kBuiltins', 'SELECT COUNT(*)/1000 FROM BuiltinsInGithubProject')
print('% number of project-unique builtins')
print_query_as_command('kProjectUniqueBuiltins', 'SELECT COUNT(*)/1000 FROM UniqueBuiltinsPerProject')

print('% number of projects with builtins')
print_query_as_command('nrProjectsWithBuiltins', 'SELECT COUNT(DISTINCT GITHUB_PROJECT_ID) FROM BuiltinsInGithubProject')
print('% percentage of projects with builtins')
print_query_as_command('percentageProjectsWithBuiltins', 'SELECT COUNT(DISTINCT GITHUB_PROJECT_ID) * 100.0 / (SELECT COUNT(*) FROM GithubProject) FROM BuiltinsInGithubProject', percentage=True)

print('% ############################## filtering')
print_query_as_command('percentageRemovedByDoubleQuotes', """SELECT COUNT(*)*100.0/(SELECT COUNT(*) FROM BuiltinsInGithubProjectUnfiltered) FROM BuiltinsInGithubProjectUnfiltered JOIN ExcludedFragments ON BuiltinsInGithubProjectUnfiltered.CODE_FRAGMENT = ExcludedFragments.CODE_FRAGMENT AND CATEGORY = "QUOTES"  AND FILE_PATH NOT LIKE "%/gcc%/%" AND FILE_PATH NOT LIKE "%/llvm%/%" AND FILE_PATH NOT LIKE "%/clang%/%" """, percentage=True)
print_query_as_command('nrKRemovedByDoubleQuotes', """SELECT COUNT(*)*1000.0 FROM BuiltinsInGithubProjectUnfiltered JOIN ExcludedFragments ON BuiltinsInGithubProjectUnfiltered.CODE_FRAGMENT = ExcludedFragments.CODE_FRAGMENT AND CATEGORY = "QUOTES"  AND FILE_PATH NOT LIKE "%/gcc%/%" AND FILE_PATH NOT LIKE "%/llvm%/%" AND FILE_PATH NOT LIKE "%/clang%/%" """)
print_query_as_command('percentageBuiltinFilteredByComments', """ SELECT COUNT(*)*100.0/(SELECT COUNT(*) FROM BuiltinsInGithubProjectUnfiltered) FROM BuiltinsInGithubProjectUnfiltered JOIN ExcludedFragments ON BuiltinsInGithubProjectUnfiltered.CODE_FRAGMENT = ExcludedFragments.CODE_FRAGMENT AND CATEGORY = "COMMENT"  AND FILE_PATH NOT LIKE "%/gcc%/%" AND FILE_PATH NOT LIKE "%/llvm%/%" AND FILE_PATH NOT LIKE "%/clang%/%" """, percentage=True)
print_query_as_command('percentageFilteredByCompilerDirectories', 'SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM BuiltinsInGithubProjectUnfiltered) FROM BuiltinsInGithubProjectUnfiltered WHERE FILE_PATH LIKE "%/gcc%/%" OR FILE_PATH LIKE "%/llvm%/%" OR FILE_PATH LIKE "%/clang%/%"', percentage=True)
print_query_as_command('builtinsWithLessThanTwoOccurrences', """SELECT COUNT(*) FROM BuiltinsUnfiltered
LEFT JOIN (
	SELECT BUILTIN_ID, COUNT(DISTINCT GITHUB_PROJECT_ID) as github_project_count
	FROM BuiltinsInGithubProject t2
	GROUP BY BUILTIN_ID
) c on c.BUILTIN_ID = BuiltinsUnfiltered.ID
WHERE FROM_DEF = 0 AND github_project_count <= 1
ORDER BY github_project_count DESC
""")
#print_query_as_command('builtinsFilteredByBlacklist', """SELECT COUNT(*) FROM BuiltinsInGithubProjectUnfiltered WHERE CODE_FRAGMENT IN (SELECT CODE_FRAGMENT FROM ExcludedFragments)""")
print_query_as_command('percentageFilteredByBlacklist', """SELECT COUNT(*)*100.0/(SELECT COUNT(*) FROM BuiltinsInGithubProjectUnfiltered) FROM BuiltinsInGithubProjectUnfiltered JOIN ExcludedFragments ON BuiltinsInGithubProjectUnfiltered.CODE_FRAGMENT = ExcludedFragments.CODE_FRAGMENT AND CATEGORY = "MANUAL"  AND FILE_PATH NOT LIKE "%/gcc%/%" AND FILE_PATH NOT LIKE "%/llvm%/%" AND FILE_PATH NOT LIKE "%/clang%/%" """, percentage=True)
print_query_as_command('percentageFilteredBuiltins', """SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM BuiltinsInGithubProjectUnfiltered) FROM BuiltinsInGithubProject""", percentage=True)
print_query_as_command('kBuiltinsUnfiltered', """SELECT COUNT(*)/1000 FROM BuiltinsInGithubProjectUnfiltered""")
print_query_as_command('nrBlacklist', 'SELECT COUNT(*) FROM ExcludedFragments WHERE CATEGORY = "MANUAL"')

print('% ############################## builtins')
print('% max number of unique builtins per project')
print_query_as_command('maxNumberUniqueBuiltinsPerProject', 'SELECT COUNT(ID) as count FROM UniqueBuiltinsPerProject GROUP BY GITHUB_PROJECT_ID ORDER BY count desc LIMIT 1')
print_query_as_command('avgNumberUniqueBuiltinsPerProject', 'SELECT AVG(count) FROM (SELECT COUNT(ID) as count FROM UniqueBuiltinsPerProject GROUP BY GITHUB_PROJECT_ID ORDER BY count)', roundn=True)
print_query_as_command('medianNumberUniqueBuiltinsPerProject', 'SELECT COUNT(ID) as count FROM UniqueBuiltinsPerProject GROUP BY GITHUB_PROJECT_ID ORDER BY count LIMIT 1 OFFSET (SELECT COUNT(DISTINCT GITHUB_PROJECT_ID)/2 FROM UniqueBuiltinsPerProject)')
print_query_as_command('medianNumberMachineSpecificUniqueBuiltinsPerProject', 'SELECT COUNT(ID) as count FROM UniqueBuiltinsPerProject WHERE MACHINE_SPECIFIC=1 GROUP BY GITHUB_PROJECT_ID ORDER BY count LIMIT 1 OFFSET (SELECT COUNT(DISTINCT GITHUB_PROJECT_ID)/2 FROM UniqueBuiltinsPerProject WHERE MACHINE_SPECIFIC=1)')
print_query_as_command('medianNumberMachineIndependentUniqueBuiltinsPerProject', 'SELECT COUNT(ID) as count FROM UniqueBuiltinsPerProject WHERE MACHINE_SPECIFIC=0 GROUP BY GITHUB_PROJECT_ID ORDER BY count LIMIT 1 OFFSET (SELECT COUNT(DISTINCT GITHUB_PROJECT_ID)/2 FROM UniqueBuiltinsPerProject WHERE MACHINE_SPECIFIC=0)')


print_query_as_command('medianBuiltinEveryXLOC', 'SELECT builtin_every_x_line FROM BuiltinFrequencyInGithubProjects LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM BuiltinFrequencyInGithubProjects)')
print_query_as_command('avgBuiltinEveryXLOC', 'SELECT AVG(builtin_every_x_line) FROM BuiltinFrequencyInGithubProjects', roundn=True)
print_query_as_command('minBuiltinEveryXLOC', 'SELECT MIN(builtin_every_x_line) FROM BuiltinFrequencyInGithubProjects')
print_query_as_command('maxBuiltinEveryXLOC', 'SELECT MAX(builtin_every_x_line) FROM BuiltinFrequencyInGithubProjects')

print('% architecture-specific vs. architecture-independent builtins')
print_query_as_command('nrProjectsWithMachineIndependentBuiltins', 'SELECT COUNT(DISTINCT GITHUB_PROJECT_ID) as count FROM UniqueCategoriesPerProject WHERE MACHINE_SPECIFIC=0 GROUP BY MACHINE_SPECIFIC')
print_query_as_command('nrProjectsWithMachineSpecificBuiltins', 'SELECT COUNT(DISTINCT GITHUB_PROJECT_ID) as count FROM UniqueCategoriesPerProject WHERE MACHINE_SPECIFIC=1 GROUP BY MACHINE_SPECIFIC')
print_query_as_command('kMachineSpecificBuiltinsTotal', 'SELECT COUNT(BUILTIN_ID)/1000 FROM BuiltinsInGithubProject p LEFT JOIN Builtins b on p.BUILTIN_ID = b.ID WHERE MACHINE_SPECIFIC=1 GROUP BY MACHINE_SPECIFIC')
print_query_as_command('kMachineIndependentBuiltinsTotal', 'SELECT COUNT(BUILTIN_ID)/1000 FROM BuiltinsInGithubProject p LEFT JOIN Builtins b on p.BUILTIN_ID = b.ID WHERE MACHINE_SPECIFIC=0 GROUP BY MACHINE_SPECIFIC')
print_query_as_command('topOtherBuiltins', 'SELECT COUNT(*)  FROM (SELECT * FROM UniqueBuiltinCounts ORDER BY count DESC LIMIT 50) WHERE BUILTIN_CATEGORY="other"')
print_query_as_command('nrOtherBuiltins', 'SELECT COUNT(*)  FROM Builtins WHERE BUILTIN_CATEGORY="other"')
print_query_as_command('topSyncBuiltins', 'SELECT COUNT(*)  FROM (SELECT * FROM UniqueBuiltinCounts ORDER BY count DESC LIMIT 50) WHERE BUILTIN_CATEGORY="sync"')
print_query_as_command('topAtomicBuiltins', 'SELECT COUNT(*)  FROM (SELECT * FROM UniqueBuiltinCounts ORDER BY count DESC LIMIT 100) WHERE BUILTIN_CATEGORY="atomic"')
print_query_as_command('topOtherLibcBuiltins', 'SELECT COUNT(*)  FROM (SELECT * FROM UniqueBuiltinCounts ORDER BY count DESC LIMIT 100) WHERE BUILTIN_CATEGORY="other-libc"')
print_query_as_command('topInternalBuiltins', 'SELECT COUNT(*)  FROM (SELECT * FROM UniqueBuiltinCounts ORDER BY count DESC LIMIT 100) WHERE BUILTIN_CATEGORY="GCC internal"')
print_query_as_command('topAddressBuiltins', 'SELECT COUNT(*)  FROM (SELECT * FROM UniqueBuiltinCounts ORDER BY count DESC LIMIT 100) WHERE BUILTIN_CATEGORY="address"')
print_query_as_command('offsetofBuiltins', 'SELECT COUNT(*)  FROM (SELECT * FROM UniqueBuiltinCounts ORDER BY count DESC LIMIT 100) WHERE BUILTIN_CATEGORY="offsetof"')
print_query_as_command('objectSizeBuiltins', 'SELECT COUNT(*)  FROM (SELECT * FROM UniqueBuiltinCounts ORDER BY count DESC LIMIT 100) WHERE BUILTIN_CATEGORY="object-size"')
print_query_as_command('overflowBuiltins', 'SELECT COUNT(*)  FROM (SELECT * FROM UniqueBuiltinCounts ORDER BY count DESC LIMIT 100) WHERE BUILTIN_CATEGORY="overflow"')
print_query_as_command('topMachineSpecificBuiltins', 'SELECT COUNT(*)  FROM (SELECT * FROM UniqueBuiltinCounts ORDER BY count DESC LIMIT 100) WHERE MACHINE_SPECIFIC=1')
print_query_as_command('topPowerpcAltivecBuiltins', 'SELECT COUNT(*)  FROM (SELECT * FROM UniqueBuiltinCounts ORDER BY count DESC LIMIT 100) WHERE BUILTIN_CATEGORY="powerpc-altivec"')
print_query_as_command('topArmCBuiltins', 'SELECT COUNT(*)  FROM (SELECT * FROM UniqueBuiltinCounts ORDER BY count DESC LIMIT 100) WHERE BUILTIN_CATEGORY="arm-c-extensions"')


print('% ############################### unused builtins')
print_query_as_command('numberDefBuiltinsUsed', 'SELECT COUNT(*) FROM Builtins where github_project_count > 0 AND FROM_DEF=1')
print_query_as_command('numberDefBuiltinsNotUsed', 'SELECT COUNT(*) FROM Builtins where (github_project_count = 0 or github_project_count is NULL) AND FROM_DEF=1')
print_query_as_command('percentageDefBuiltinsUsed', 'SELECT 100.0 * COUNT(*) / (SELECT COUNT(*) FROM Builtins WHERE FROM_DEF=1) FROM Builtins where github_project_count > 0 AND FROM_DEF=1', percentage=True)
print_query_as_command('percentageDefBuiltinsNotUsed', 'SELECT COUNT(*) * 100.0 / (SELECT COUNT(*)  FROM Builtins WHERE FROM_DEF=1) FROM Builtins where (github_project_count = 0 or github_project_count is NULL) AND FROM_DEF=1', percentage=True)
print_query_as_command('nrMachineSpecificBuiltinsUsed', 'SELECT COUNT(*) FROM Builtins where github_project_count > 0 AND FROM_DEF=1 AND MACHINE_SPECIFIC=1')
print_query_as_command('nrMachineIndependentBuiltinsUsed', 'SELECT COUNT(*) FROM Builtins where github_project_count > 0 AND FROM_DEF=1 AND MACHINE_SPECIFIC=0')
print_query_as_command('nrMachineSpecificBuiltinsUnused', 'SELECT COUNT(*) FROM Builtins where (github_project_count IS NULL or github_project_count = 0) AND FROM_DEF=1 AND MACHINE_SPECIFIC=1')
print_query_as_command('nrMachineIndependentBuiltinsUnused', 'SELECT COUNT(*) FROM Builtins where (github_project_count IS NULL or github_project_count = 0) AND FROM_DEF=1 AND MACHINE_SPECIFIC=0')
print_query_as_command('percentageUnusedMachineSpecificBuiltins', 'SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Builtins WHERE FROM_DEF=1 AND MACHINE_SPECIFIC=1) FROM Builtins where (github_project_count IS NULL or github_project_count = 0) AND FROM_DEF=1 AND MACHINE_SPECIFIC=1', percentage=True)
print_query_as_command('percentageUnusedMachineIndependetBuiltins', 'SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Builtins WHERE FROM_DEF=1 AND MACHINE_SPECIFIC=0) FROM Builtins where (github_project_count IS NULL or github_project_count = 0) AND FROM_DEF=1 AND MACHINE_SPECIFIC=0', percentage=True)

print('% ############################### classified historical trends')
print_query_as_command('numberProjectsGitHistoryProcessed', 'SELECT COUNT(*) FROM GithubProject WHERE CHECKED_HISTORY=1')
print_query_as_command('numberProjectsNotAnalyzed', 'SELECT COUNT(*) FROM GithubProject WHERE CHECKED_HISTORY IS NOT 1 AND ID IN (SELECT DISTINCT GITHUB_PROJECT_ID FROM BuiltinsInGithubProject)')
print_query_as_command('percentageProjectsGitHistoryProcessed', 'SELECT 100.0 * COUNT(*) / (SELECT COUNT(DISTINCT GITHUB_PROJECT_ID) FROM BuiltinsInGithubProject) FROM GithubProject WHERE CHECKED_HISTORY=1', percentage=True)
print_query_as_command('numberProjectsTrendAnalyzed', 'SELECT COUNT(*) FROM BuiltinTrendInGithubProjectUnfiltered')
query_classifications = "SELECT COUNT(*)*100.0/(SELECT COUNT(*) FROM BuiltinTrendsView WHERE nr_users=3) FROM BuiltinTrendsView WHERE nr_trends = %d and nr_users=3"
print_query_as_command('classificationsNrAgreed', query_classifications % (1, ), percentage=True)
print_query_as_command('classificationsNrTwoAgreed', query_classifications % (2, ), percentage=True)
print_query_as_command('classificationsAllDisagreed', query_classifications % (3, ), percentage=True)

print_unused_commands()
print_unused_builtins()

print_commit_most_influenced_builtins_table(added=True)
print_commit_most_influenced_builtins_table(added=True, consider_first_commit=False)
print_commit_most_influenced_builtins_table(added=False)
print_users_with_most_builtin_commits(positive=True, negative=True)
print_users_with_most_builtin_commits(positive=False, negative=True)
print_users_with_most_builtin_commits(positive=True, negative=False)

print_median_values()
print_trend_table()
print_project_stats_table()
print_machine_specific_builtin_table()
print_machine_independent_builtin_table()
print_projects_with_most_unique_builtins_table()
print_projects_with_most_builtins_table()
print_builtin_table()
print_small_builtin_table()
most_frequent_file_names()
#unused_builtins_table()
print_trend_counts()
