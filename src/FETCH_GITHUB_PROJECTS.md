# Fetching projects

The `fetch_github_projects.py` file fetches projects from GitHub and stores them along with metadata obtained from GitHub, `git`, and `cloc` in the `$ARTIFACT_ROOT/projects` folder.

As stated in the main `README.md`, the artifact does not include the source code of the 5000 GitHub projects, since the space to store the code would occupy several hundreds of GB. Thus, the `$ARTIFACT_ROOT/projects` folder is empty.

Note that GitHub imposes rate limits on users of its API that the script uses. GitHub login credentials can be provided to increase these limits. To this end, set `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_PASSWORD` to your GitHub username and password. If you do not supply credentials, the script still works, but prints a warning.

Also note that the fetching of GitHub projects should not be interrupted, as no clean up logic is implemented to delete incompletely downloaded projects. If you interrupt the download, it is advised to delete the most recently downloaded project from the `$ARTIFACT_ROOT/projects` folder and from the `GithubProjectUnfiltered` table in the database, and manually invoke the `$ARTIFACT_ROOT/src/include/sync_views_to_tables.py` script.

This part of the artifact could be tested by downloading a number of projects from GitHub, and checking the metadata stored in the database for them.

First, choose how many GitHub stars the projects downloaded should have. To this end, vary the integer (currently set to 400) in the following URL and open the URL in your browser so that `total_count` field is not zero and not too high:

```
https://api.github.com/search/repositories?q=+language:c+stars:400
```

At the time of writing, 3 GitHub projects had 400 GitHub stars and were thus selected. The page in the browser started like this:

```
{
  "total_count": 3,
  "incomplete_results": false,
  "items": [
...
```


Then, modify the script to download the projects having this amount of GitHub stars by replacing the `<placeholder>` by a call to the `download_projects` function. Before that, back up the database and drop the existing GitHub projects data:


```
cd $ARTIFACT_ROOT
cp database.db database.db.backup
cp src/fetch_github_projects.py src/fetch_github_projects.py.backup
echo "DELETE FROM GithubProjectUnfiltered" | sqlite3 database.db
sed -i 's/# <placeholder>/download_projects(400, 400)/g' src/fetch_github_projects.py # download GitHub projects within a star range of 400 to 400
```

Finally, execute the script to download the projects:

```
src/fetch_github_projects.py # GITHUB_CLIENT_ID=<username> GITHUB_CLIENT_PASSWORD=<password> src/fetch_github_projects.py to use credentials
```

At the time of writing, the 3 GitHub projects were downloaded:

```
Please set up the Github credentials (environment variables GITHUB_CLIENT_ID and GITHUB_CLIENT_PASSWORD) due to the rate limit (see https://developer.github.com/v3/#authentication)!
parsing projects with 400 stars
starting to process 3 items
Cloning into '/home/manuel/research/esecfse19-artifact/latest/src/../projects/facebook-openbmc'...
remote: Enumerating objects: 867, done.
remote: Counting objects: 100% (867/867), done.
remote: Compressing objects: 100% (642/642), done.
remote: Total 49257 (delta 352), reused 490 (delta 188), pack-reused 48390
Receiving objects: 100% (49257/49257), 13.02 MiB | 4.27 MiB/s, done.
Resolving deltas: 100% (32413/32413), done.
Cloning into '/home/manuel/research/esecfse19-artifact/latest/src/../projects/ossrs-state-threads'...
remote: Enumerating objects: 214, done.
remote: Total 214 (delta 0), reused 0 (delta 0), pack-reused 214
Receiving objects: 100% (214/214), 177.24 KiB | 876.00 KiB/s, done.
Resolving deltas: 100% (108/108), done.
Cloning into '/home/manuel/research/esecfse19-artifact/latest/src/../projects/pygraphviz-pygraphviz'...
remote: Enumerating objects: 15, done.
remote: Counting objects: 100% (15/15), done.
remote: Compressing objects: 100% (11/11), done.
remote: Total 2001 (delta 4), reused 12 (delta 4), pack-reused 1986
Receiving objects: 100% (2001/2001), 605.82 KiB | 1.77 MiB/s, done.
Resolving deltas: 100% (1208/1208), done.
GithubProject
Builtins
UniqueBuiltinsPerProject
UniqueCategoriesPerProject
UniqueCategoryCounts
UniqueFileWithUniqueBuiltinNames
UniqueBuiltinsGroupedByMachineSpecificPerProject
UniqueBuiltinCounts
FileNames
DistinctBuiltinCountPerProject
BuiltinsInGithubProject
BuiltinFrequencyInGithubProjects
CommitHistoryDiffEntry
CommitHistory
CommitHistoryAccumulated
```

You can check the rows in the `GithubProjectUnfiltered` table to verify the projects' metadata. Note that some columns are empty. These are updated when running the `BuiltinAnalyzer` (which then sets the column `PROCESSED` to 1):

```
echo "SELECT * FROM GithubProjectUnfiltered" | sqlite3 database.db
```

To restore the database and script, execute the following commands:

```
mv src/fetch_github_projects.py.backup src/fetch_github_projects.py
mv database.db.backup database.db
```

Alternatively, you can proceed by analyzing the builtin usages of the projects downloaded. In this case, you need to also download projects in a star range so that the [GCC mirror](https://github.com/gcc-mirror/gcc) is included, which we analyze to infer builtin names.
