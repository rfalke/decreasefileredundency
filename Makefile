tests: pylint python_tests 

python_tests:
	for i in src/test/python/dfr_test/Test*.py; do echo "=== Running $$i"; \
	PYTHONPATH=src/main/python:src/test/python:deps/python \
	python "$$i"; done

pylint:
	PYTHONPATH=src/main/python pylint --rcfile=src/test/resources/pylint.rc -r n dfr
	PYTHONPATH=src/main/python:src/test/python:deps/python pylint --rcfile=src/test/resources/pylint.rc -r n -d C0301,R0904 dfr_test
