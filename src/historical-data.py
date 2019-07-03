#!/usr/bin/env python3
from include.common import *

data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'generated', 'historical-data', 'csv')

min_nr_commits = 5
select_project_data = 'SELECT GITHUB_PROJECT_ID, GITHUB_OWNER_NAME, GITHUB_PROJECT_NAME FROM CommitHistoryAccumulated WHERE CUR_NUMBER_BUILTINS != 0 AND GITHUB_PROJECT_ID IN (SELECT ID FROM GithubProject WHERE CHECKED_HISTORY=1) GROUP BY GITHUB_PROJECT_ID, GITHUB_OWNER_NAME, GITHUB_PROJECT_NAME'
analyzed_projects = c.execute(select_project_data).fetchall()
project_to_builtin_development = dict()
for analyzed_project in analyzed_projects:
    project_id = analyzed_project[0]
    builtins_development = []
    data = c.execute('SELECT COMMIT_TIME_UNIX, CUR_NUMBER_BUILTINS FROM CommitHistoryAccumulated WHERE GITHUB_PROJECT_ID = ' + str(project_id) + ' AND CUR_NUMBER_BUILTINS IS NOT NULL ORDER BY COMMIT_TIME_UNIX').fetchall()
    accumulated_nr_builtins = 0
    for entry in data:
        if entry[1] != 0:
            accumulated_nr_builtins += int(entry[1])
            time_unix = entry[0]
            builtins_development.append((accumulated_nr_builtins, time_unix))
    project_to_builtin_development[project_id] = builtins_development

def analyze_increasing_trend_only():
    for analyzed_project in analyzed_projects:
        project_id = analyzed_project[0]
        project_name = analyzed_project[2]
        removals = c.execute('SELECT COUNT(*) FROM CommitHistoryAccumulated WHERE GITHUB_PROJECT_ID = ' + str(project_id) + ' AND CUR_NUMBER_BUILTINS < 0 ORDER BY COMMIT_TIME_UNIX').fetchall()[0]
        if int(removals[0]) == 0:
            query = "insert or ignore into BuiltinTrendInGithubProjectUnfiltered(GITHUB_PROJECT_ID, TREND, USER) VALUES(?, 'monotonically increasing', 'automatic')"
            c.execute(query, (project_id,))

def analyze_less_than_min_commits_trend():
    data = c.execute(select_project_data + ' HAVING COUNT(COMMIT_NR) < ' + str(min_nr_commits))
    project_ids = [project[0] for project in data]
    for project_id in project_ids:
        query = "insert or replace into BuiltinTrendInGithubProjectUnfiltered(GITHUB_PROJECT_ID, TREND, USER) VALUES(?, 'less than " + str(min_nr_commits) + " commits', 'automatic')"
        c.execute(query, (project_id,))

def analyze_mostly_stable_trend_only():
    for analyzed_project in analyzed_projects:
        project_id = analyzed_project[0]
        project_name = analyzed_project[2]
        builtin_commit_count = nr_builtins = c.execute('SELECT COUNT(*) FROM CommitHistoryAccumulated WHERE GITHUB_PROJECT_ID = ' + str(project_id) +' AND CUR_NUMBER_BUILTINS != 0').fetchall()[0][0]
        data = c.execute('SELECT COMMIT_TIME_UNIX, CUR_NUMBER_BUILTINS FROM CommitHistoryAccumulated WHERE GITHUB_PROJECT_ID = ' + str(project_id) + ' AND CUR_NUMBER_BUILTINS IS NOT NULL ORDER BY COMMIT_TIME_UNIX').fetchall()
        
        # determine the median number of builtins in a project
        builtins = project_to_builtin_development[project_id]
        median_nr_builtins = builtins[len(builtins) // 2][0]
        lower_limit = median_nr_builtins * 0.9
        upper_limit = median_nr_builtins * 1.1
        outliers = [accumulated_nr_builtins for accumulated_nr_builtins in builtins if accumulated_nr_builtins[0] > upper_limit or accumulated_nr_builtins[0] < lower_limit ]
        if len(outliers) < builtin_commit_count * 0.15:
            query = "insert or ignore into BuiltinTrendInGithubProjectUnfiltered(GITHUB_PROJECT_ID, TREND, USER) VALUES(?, 'mostly stable', 'automatic')"
            c.execute(query, (project_id,))
            # print("median: %d upper_limit: %f lower_limit: %f nr_outliers: %d builtin commits: %d" % (median_nr_builtins, lower_limit, upper_limit, len(outliers), builtin_commit_count))

def analyze_mostly_increasing_trend_only():
    for analyzed_project in analyzed_projects:
        project_id = analyzed_project[0]
        project_name = analyzed_project[2]
        builtin_commit_count = nr_builtins = c.execute('SELECT COUNT(*) FROM CommitHistoryAccumulated WHERE GITHUB_PROJECT_ID = ' + str(project_id) +' AND CUR_NUMBER_BUILTINS != 0').fetchall()[0][0]
        data = c.execute('SELECT COMMIT_TIME_UNIX, CUR_NUMBER_BUILTINS FROM CommitHistoryAccumulated WHERE GITHUB_PROJECT_ID = ' + str(project_id) + ' AND CUR_NUMBER_BUILTINS IS NOT NULL ORDER BY COMMIT_TIME_UNIX').fetchall()
        
        # determine the median number of builtins in a project
        builtins = project_to_builtin_development[project_id]
        last_ones = builtins[-1 * max(1, int(len(builtins) * 0.10)):]
        max_value = max([nr_builtins for (nr_builtins, time) in last_ones])
        outliers = 0
        prev = 0
        last_ones_maximal = True
        for (cur, _) in builtins:
            if cur < prev:
                outliers += 1
            if cur > max_value:
                last_ones_maximal = False
                break
            prev = cur
        if (outliers < builtin_commit_count * 0.20) and last_ones_maximal:
            query = "insert or ignore into BuiltinTrendInGithubProjectUnfiltered(GITHUB_PROJECT_ID, TREND, USER) VALUES(?, 'mostly increasing', 'automatic')"
            c.execute(query, (project_id,))


# Automatically classify projects with less than a certain number of commits.
# We also tried other, commented out classification schemes, which did not work well, so we didn't use them.
analyze_less_than_min_commits_trend()
#analyze_increasing_trend_only()
#analyze_mostly_stable_trend_only()
#analyze_mostly_increasing_trend_only()

conn.commit()

import datetime

for analyzed_project in analyzed_projects:
    project_id = analyzed_project[0]
    project_owner = analyzed_project[1]
    project_name = analyzed_project[2]
    file_name = "%d-%s-%s.csv" % (project_id, project_owner, project_name)
    csv_file = open(os.path.join(data_dir, file_name), 'w')
    csv_file.write('date;nr_builtins\n')
    dates = c.execute('SELECT GIT_FIRST_COMMIT_DATE, GIT_LAST_COMMIT_DATE FROM GithubProject WHERE ID = ' + str(project_id)).fetchall()[0]
    first_commit_date = datetime.datetime.strptime(dates[0], "%Y-%m-%d").timestamp()
    last_commit_date = datetime.datetime.strptime(dates[1], "%Y-%m-%d").timestamp()
    csv_file.write('%s;%s\n' % (first_commit_date, 0))
    for entry in project_to_builtin_development[project_id]:
        accumulated_nr_builtins = entry[0]
        time_unix = entry[1]
        csv_file.write('%s;%s\n' % (time_unix, accumulated_nr_builtins))
    csv_file.write('%s;%s\n' % (last_commit_date, accumulated_nr_builtins))
    csv_file.close()
