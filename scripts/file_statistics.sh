printf 'Total number of python source files found\n'
cd phoenix
ls -R | grep -E ".py$" | wc -l

printf '\nLines count on all python source files\n'
find . -name '*.py' -exec cat {} + | wc -l
