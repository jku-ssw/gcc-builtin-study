As mentioned in Section 2 of the paper, we wanted to determine whether our project data set is representative and diverse. To this end, we computed Nagappan et al.'s coverage score based on the manually validated GitHub project metadata of Munaiah et al.'s RepoReapers data set.

# Computing the coverage score

You can compute the coverage score of 0.966 mentioned in the paper as follows:

```
cd $ARTIFACT_ROOT/coverage/sampling_software_projects/
Rscript compute_coverage.R
```

The expected output is the following:
```
[1] 0.9662066
 [1] 1.0000000 0.9999931 1.0000000 1.0000000 0.9999656 1.0000000 1.0000000
 [8] 0.9680711 0.9999931 1.0000000
```

Note that the script takes 3 minutes to execute on our machine.
For details on the the overall approach see the links below.
Here, the coverage is computed based on an universe (contained in the `cprojects.csv` file) and a subset of the universe (contained in the `builtinprojects.csv` file). These files can be produced as follows:

```
cd $ARTIFACT_ROOT/coverage/
./extract.py
```

# Files

* dataset.csv: This is the RepoReapers data set obtained from [https://reporeapers.github.io](https://reporeapers.github.io).
* cprojects.csv: The content of dataset.csv, but only including C projects
* builtinprojects.csv: The content of cprojects.csv, but only including projects that are also contained in the `GithubProject` table. 

# Links

* coverage score: [Diversity in Software Engineering Research](https://www.microsoft.com/en-us/research/publication/diversity-in-software-engineering-research/)
* [Repo Reapers](https://github.com/RepoReapers/reaper)
