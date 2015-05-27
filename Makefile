COVERAGE=coverage-2.7
CFLAGS=-std=c99 -march=amdfam10 -O2 -Wall -Werror -fno-strict-aliasing

tests: compile_c pep8 pylint python_tests shell_tests

compile_c: target/calc_hamming_distance target/calc_histogram_distance

target/calc_hamming_distance: Makefile src/main/c/calc_hamming_distance.c
	mkdir -p target
	gcc -g $(CFLAGS) src/main/c/calc_hamming_distance.c -o target/calc_hamming_distance
	-objdump -d target/calc_hamming_distance >target/calc_hamming_distance.s

target/calc_histogram_distance: Makefile src/main/c/calc_histogram_distance.c
	mkdir -p target
	gcc -g $(CFLAGS) src/main/c/calc_histogram_distance.c -o target/calc_histogram_distance
	-objdump -d target/calc_histogram_distance >target/calc_histogram_distance.s

indent_c:
	indent -linux src/main/c/calc_hamming_distance.c
	indent -linux src/main/c/calc_histogram_distance.c

python_tests:
	$(COVERAGE) erase
	for i in src/test/python/dfr_test/Test*.py; do echo "=== Running $$i"; \
	PYTHONPATH=src/main/python:src/test/python:deps/python \
	$(COVERAGE) run -a "$$i" || exit 1; done
	$(COVERAGE) report -m '--include=*/dfr/*' --fail-under=95

pylint:
	PYTHONPATH=src/main/python pylint --rcfile=src/test/resources/pylint.rc -r n dfr
	PYTHONPATH=src/main/python:src/test/python:deps/python pylint --rcfile=src/test/resources/pylint.rc -r n -d C0301,R0904 dfr_test

pep8:
	pep8 src/main/python/dfr/*.py
	pep8 --max-line-length=400 src/test/python/dfr_test/*.py

profile:
	rm -rf /tmp/files_profile.sdb
	time python -m cProfile src/main/python/dfr/f_index.py  --db-file /tmp/files_profile.sdb /etc

shell_tests:
	./src/test/shell/run.sh
	./src/test/shell/verify_hamming.sh
	./src/test/shell/verify_histogram.sh
	./src/test/shell/verify_sig2.sh
	./src/test/shell/test_image_signatures.sh
