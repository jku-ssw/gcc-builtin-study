The GCC builtin test suite is [available on GitHub](https://github.com/gcc-builtins/tests) and has been cloned into this directory. It consists of 100 test cases used to test whether a tool (correctly) supports the most commonly used GCC builtins and was used to answer RQ5.

To test this part of the artifact, we recommend using a compiler or tool that is already present on the system and use it to execute the test cases. In this example, we use GCC to compile the test cases and then execute the resulting binaries:

```
cd $ARTIFACT_ROOT/gcc-builtin-tests
echo "import glob, subprocess" > test.py
echo "for cfile in glob.glob('tests/test-cases/*.c'):" >> test.py
echo "    subprocess.check_call(['gcc', cfile, '-lm'])" >> test.py
echo "    subprocess.check_call(['./a.out'])" >> test.py
python3 test.py
```

If no output appears on the command line, the test cases execute as expected, which is expected for GCC on Linux. If you use other compilers or operating systems, some of the tests might fail. On macOS we observed for instance that some Clang version do not provide `isinff` and `isnanf`.

Since we had to manually classify why a test case failed, the `$ARTIFACT_ROOT/gcc-builtin-tests/tool-evaluation.csv` file was created manually. The results could be reproduced by installing the versions of these tools specified in the .csv file and execute them as specified above.

Note that the `$ARTIFACT_ROOT/src/tool-evaluation.r` script is used to plot Figure 5 in the paper.
