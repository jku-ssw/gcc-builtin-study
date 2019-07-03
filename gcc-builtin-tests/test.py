import glob, subprocess
for cfile in glob.glob('tests/test-cases/*.c'):
    subprocess.check_call(['gcc', cfile, '-lm'])
    subprocess.check_call(['./a.out'])
