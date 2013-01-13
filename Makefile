COVERAGE=coverage-2.6

tests: pep8 pylint python_tests shell_tests

python_tests:
	$(COVERAGE) erase
	for i in src/test/python/dfr_test/Test*.py; do echo "=== Running $$i"; \
	PYTHONPATH=src/main/python:src/test/python:deps/python \
	$(COVERAGE) run -a "$$i"; done
	$(COVERAGE) report -m '--include=*/dfr/*' --fail-under=100

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
	./src/test/shell/verify_sig2.sh
