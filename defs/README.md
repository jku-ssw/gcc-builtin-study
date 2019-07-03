This directory contains the builtin names that we derived from the [GCC documentation](https://gcc.gnu.org/onlinedocs/gcc-7.2.0/gcc/). The builtin names are specified in separate files so that new builtins that GCC might introduce can be easily added.

The builtin names are specified using a custom file format. Each `.def` file contains a list of attributes (starting with a `%`) holding metadata about the builtins contained in the file such as the documentation URL. The attributes are followed by a list of builtin names.

The builtin names can be imported into the database using the `src/reset.py` script, which also resets the database (except for deleting the projects table).

To verify that this part of the artifact works as expected, a new GCC builtin can be added. Below, this is explained assuming a Linux OS.

First add a `.def` file with a new builtin that you then import into the database:

```
cd $ARTIFACT_ROOT
echo "%url=https://esec-fse19.ut.ee/calls/research-papers/" > defs/test.def
echo "%header=A dummy builtin to test the artifact" >> defs/test.def
echo "builtin__artifact_test" >> defs/test.def
cp database.db database.backup # back up the database to restore it later
src/reset.py # deletes the old builtin definitions and imports the new ones
```

Check the `Builtins` table, either using DB Browser for SQLite or on the command line, to verify that the builtin name was imported:

```
echo "SELECT * FROM BUILTINS WHERE BUILTIN_NAME = 'builtin__artifact_test'" | sqlite3 database.db
# the output should be similar to this: 70|builtin__artifact_test|test|0|https://esec-fse19.ut.ee/calls/research-papers/|A dummy builtin to test the artifact|1|
```


Restore the database and remove the builtin definition:

```
rm defs/test.def
mv database.backup database.db
```

To obtain the total number of builtin names specified in a `.def` file, execute the following:

```
echo "SELECT COUNT(*) FROM Builtins WHERE FROM_DEF" | sqlite3 database.db
```

The expected result is `6039`.

Note that the `$ARTIFACT_ROOT/src/helper-gcc-doc-extraction` directory contains helper scripts to extract builtin names from the GCC documentation.
