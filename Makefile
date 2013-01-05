tests: python_tests

python_tests:
	PYTHONPATH=src/main/python:deps/python ls src/test/python/Test*.py | xargs -n1 python

pylint:
	PYTHONPATH=src/main/python pylint --rcfile=src/test/resources/pylint.rc -E dfr
