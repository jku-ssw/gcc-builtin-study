#!/usr/bin/env python3

import sys
sys.path.append("..")
from src.include.common import *

builtin_projects = []

query = """
    SELECT GITHUB_OWNER_NAME, GITHUB_PROJECT_NAME FROM GithubProject
    """
for row in c.execute(query):
    builtin_projects.append(str(row[0]) + '/' + str(row[1]))

import pandas as pd

keep_col = ['repository', 'architecture','community','continuous_integration','documentation', 'history', 'issues', 'license', 'size', 'unit_test', 'scorebased_org']
dataset = pd.read_csv("dataset.csv")
crows = dataset.loc[dataset['language'] == 'C']
crows[keep_col].to_csv("cprojects.csv", index=False)

builtin_projects_rows = crows.loc[crows['repository'].isin(builtin_projects)]
builtin_projects_rows[keep_col].to_csv("builtinprojects.csv", index=False)
