#!/usr/bin/env python3
import sqlite3
import argparse
import urllib.request, json
import math
import os
import time
import sys
import datetime
import re
import subprocess
dir = os.path.dirname(os.path.realpath(__file__))
project_dir = os.path.join(dir, '../projects')

conn = sqlite3.connect(os.path.join(dir, "../database.db"))
conn.execute("PRAGMA journal_mode=WAL")
c = conn.cursor()


per_page = 100
github_login_user = os.environ.get('GITHUB_CLIENT_ID', None)
github_login_password = os.environ.get('GITHUB_CLIENT_PASSWORD', None)
if github_login_user is None or github_login_password is None:
    print('Please set up the Github credentials (environment variables GITHUB_CLIENT_ID and GITHUB_CLIENT_PASSWORD) due to the rate limit (see https://developer.github.com/v3/#authentication)!')
    credentials_set = False
    github_template = "https://api.github.com/search/repositories?q=+language:c+stars:%d&page=%d&per_page=" + str(per_page)
else:
    credentials_set = True
    github_template = "https://api.github.com/search/repositories?q=+language:c+stars:%d&page=%d&per_page=" + str(per_page) + "&client_id=%s&client_secret=%s"


def get_last_commit_hash(path):
    process = subprocess.Popen(['git', 'rev-parse', 'HEAD'], cwd=path, stdout=subprocess.PIPE)
    stdout, _ = process.communicate()
    hash = stdout.decode().strip('\n')
    return hash

def get_git_commit_count(path):
    """ Gets the number of commits without merges from a Git repository. """
    process = subprocess.Popen(['git', 'rev-list', 'HEAD', '--count', '--no-merges'], cwd=path, stdout=subprocess.PIPE)
    stdout, _ = process.communicate()
    number = stdout.decode().strip("\n")
    return int(number)

def get_git_commiter_count(path):
    """ Gets the number of committers from a Git repository. """
    process = subprocess.Popen(['git', 'shortlog', '-sn'], cwd=path, stdout=subprocess.PIPE)
    stdout, _ = process.communicate()
    committers = stdout.decode("ISO-8859-1")
    return len(committers.split('\n'))

def get_first_last_commit_date(path):
    """ Gets the first and repository commit as a timestamp. """
    # %at specifies a UNIX time stamp
    process = subprocess.Popen(['git', 'log', '--format=%at'], cwd=path, stdout=subprocess.PIPE)
    stdout, _ = process.communicate()
    log = stdout.decode().strip('\n').split('\n')
    last = int(log[0])
    first = int(log[-1])
    return (first, last)

def get_c_cpp_h_assembly_loc(path):
    """ Gets the LOC of header and C files using cloc. """
    try:
        process = subprocess.Popen(['cloc', '.'], cwd=path, stdout=subprocess.PIPE)
    except FileNotFoundError:
        print("Failed to call cloc (see https://github.com/AlDanial/cloc), please install.")
        exit(-1)
    stdout, _ = process.communicate()
    lines = stdout.decode().split('\n')
    c_lines = 0
    h_lines = 0
    cpp_lines = 0
    assembly_lines = 0
    for line in lines:
        c_match = re.match(r'C \s+\d+\s+\d+\s+\d+\s+(\d+)', line, re.X)
        if c_match:
            c_lines = int(c_match.groups()[0])
        h_match = re.match(r'C/C\+\+\sHeader\s+\d+\s+\d+\s+\d+\s+(\d+)', line, re.X)
        if h_match:
            h_lines = int(h_match.groups()[0])
        cpp_match = re.match(r'C\+\+\s+\d+\s+\d+\s+\d+\s+(\d+)', line, re.X)
        if cpp_match:
            cpp_lines = int(cpp_match.groups()[0])
        assembly_match = re.match(r'Assembly\s+\d+\s+\d+\s+\d+\s+(\d+)', line, re.X)
        if assembly_match:
            assembly_lines = int(assembly_match.groups()[0])
    return (c_lines, cpp_lines, h_lines, assembly_lines)

def owner_project_from_github_url(url):
    """ Extracts owner and project name from a Github URL. For example, for
        https://github.com/graalvm/sulong it returns the tuple (graalvm, sulong). """
    if not re.match('https://github.com/([a-zA-Z0-9-_]*)/[a-zA-Z0-9-_]*', url):
        print(str(url) + "is not a valid url!")
        exit(-1)
    elements = url.split('/')
    project_name = elements[-1]
    organization_name = elements[-2]
    return (organization_name, project_name)

def get_project_dir(url):
    """ Map a Github URL to the local Github project directory. """
    (project_owner, project_name) = owner_project_from_github_url(url)
    project_dir_name = project_owner + '-' + project_name
    project_dir_name = os.path.join(project_dir, project_dir_name)
    return project_dir_name

def download_project(url):
    project_dir_name = get_project_dir(url)
    process = subprocess.Popen(['git', 'clone', url, project_dir_name], cwd=project_dir)
    process.communicate()
    return project_dir_name

def exists(url):
    query = """select COUNT(*) FROM GithubProjectUnfiltered WHERE GITHUB_URL = ? """
    return c.execute(query, (url,)).fetchone()[0] == 1

def insert_project_entry(data):
        github_url = data[str("html_url")]
        dirname = download_project(github_url)
        dirs = dirname.rstrip(os.sep).split(os.sep)
        commit_count = get_git_commit_count(dirname)
        committers_count = get_git_commiter_count(dirname)
        (first_date, last_date) = get_first_last_commit_date(dirname)
        (organization_name, project_name) = owner_project_from_github_url(github_url)
        (c_loc, cpp_loc, h_loc, assembly_loc) = get_c_cpp_h_assembly_loc(dirname)
        last_hash = get_last_commit_hash(dirname)
        project_name = data['name']

        owner_name = data['owner']['login']
        stargazers = data['stargazers_count']
        forks = data['forks_count']
        open_issues = data['open_issues_count']
        description = data['description']
        watchers = data['watchers_count']
        fork = data['fork']
        creation_date = datetime.datetime.strptime(data['created_at'], "%Y-%m-%dT%H:%M:%SZ").timestamp()
        language = data['language']
        query = """insert into GithubProjectUnfiltered(
                GITHUB_OWNER_NAME,
                GITHUB_PROJECT_NAME,
                GITHUB_URL,
                GITHUB_DESCRIPTION,
                GITHUB_NR_STARGAZERS,
                GITHUB_NR_WATCHERS,
                GITHUB_NR_FORKS,
                GITHUB_NR_OPEN_ISSUES,
                GITHUB_REPO_CREATION_DATE,
                GITHUB_LANGUAGE,
                GITHUB_FORK,

                PULL_HASH,
                PULL_DATE,

                CLOC_LOC_C,
                CLOC_LOC_H,
                CLOC_LOC_ASSEMBLY,
                CLOC_LOC_CPP,

                GIT_NR_COMMITS,
                GIT_NR_COMMITTERS,
                GIT_FIRST_COMMIT_DATE,
                GIT_LAST_COMMIT_DATE,

                PROCESSED
                )

                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)

                """
        try:
            c.execute(query,
                    (owner_name,
                    project_name,
                    github_url,
                    description,
                    stargazers,
                    watchers,
                    forks,
                    open_issues,
                    datetime.datetime.fromtimestamp(creation_date).strftime('%Y-%m-%d'),
                    language,
                    fork,

                    last_hash,
                    datetime.datetime.now().strftime('%Y-%m-%d'),

                    c_loc,
                    h_loc,
                    assembly_loc,
                    cpp_loc,

                    commit_count,
                    committers_count,
                    datetime.datetime.fromtimestamp(first_date).strftime('%Y-%m-%d'),
                    datetime.datetime.fromtimestamp(last_date).strftime('%Y-%m-%d'))
                    )
            conn.commit()
        except sqlite3.IntegrityError as e:
            print(github_url + " is a duplicate!")

def download_projects(stars_from, stars_to):
    minutes = 5
    current_stars = stars_from
    while current_stars <= stars_to:
        page = 1
        hasResults = True
        while hasResults:
            if credentials_set:
                github_url = github_template % (current_stars, page, github_login_user, github_login_password)
            else:
                github_url = github_template % (current_stars, page)
            print("parsing projects with %d stars" % (current_stars, ))
            try:
                req = urllib.request.Request(github_url)
                req.add_header('Cache-Control', 'max-age=0')
                resp = urllib.request.urlopen(req)
                json_file = json.loads(resp.read().decode())
                #data = json.loads(url.read().decode())
                projects = json_file['items']
                count = json_file['total_count']
                hasResults = count != 0
                if hasResults:
                    print("starting to process " + str(count) + " items")
                    for project in projects:
                        if not exists(project[str("html_url")]):
                            insert_project_entry(project)
                    if count < per_page:
                        hasResults = False
            except urllib.error.HTTPError as e:
                #if e.code == 422:
                #    print('reached page limit ' + str(page))
                #    hasResults = False
                if e.code == 403:
                    print('exceeded rate limit!')
                    print('waiting for ' + str(minutes) + 'minutes...')
                    for minute in range(minutes):
                        print('.', end="")
                        sys.stdout.flush()
                        time.sleep(60)
                    print()
                    continue
                else:
                    print(github_url + " " + str(e))
                    exit(-1)
            page += 1
        current_stars += 1
        if hasResults:
            print("...waiting for one minute before continuing with " + str(current_stars) + " stars")
            for minute in range(4):
                print(".", end="")
                time.sleep(15)

#download_projects(140, 145)
#download_projects(145, 150)
#download_projects(150, 155)
#download_projects(155, 160)
#download_projects(160, 170)
#download_projects(170, 175)
#download_projects(175, 180)
#download_projects(180, 185)
#download_projects(85, 190)
#download_projects(185, 220)
#download_projects(210, 230)
#download_projects(220, 250)
#download_projects(245, 255)
#download_projects(250, 260)
#download_projects(260, 270)
#download_projects(270, 290)
#download_projects(290, 300)
#download_projects(300, 310)
#download_projects(310, 320)
#download_projects(320, 330)
#download_projects(330, 340)
#download_projects(340, 360)
#download_projects(360, 400)
#download_projects(400, 410)
#download_projects(410, 420)
#download_projects(420, 430)
#download_projects(430, 450)
#download_projects(450, 490)
#download_projects(490, 495)
#download_projects(495, 500)
#download_projects(500, 520)
#download_projects(521, 550)
#download_projects(551, 600)
#download_projects(601, 650)
#download_projects(651, 700)
#download_projects(701, 750)
#download_projects(751, 800)
#download_projects(800, 820)
#download_projects(821, 850)
#download_projects(850, 900)
#download_projects(900, 920)
#download_projects(920, 940)
#download_projects(940, 960)
#download_projects(960, 1000)
#download_projects(1000, 1100)
#download_projects(1100, 1300)
#download_projects(1300, 1500)
#download_projects(1500, 1600)
#download_projects(1600, 1700)
#download_projects(1700, 1800)
#download_projects(1800, 1900)
#download_projects(1900, 1950)
#download_projects(1950, 2000)
#download_projects(2000, 2100)
#download_projects(2100, 2200)
#download_projects(2200, 2300)
#download_projects(2300, 2330)
#download_projects(2330, 3000)
#download_projects(3000, 3670)
#download_projects(3670, 5000)
#download_projects(5000, 8000)

# <placeholder>

from include.sync_views_to_tables import *
