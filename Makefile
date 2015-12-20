.PHONY: clean build install dist test_venv
VERSION=0.1

build:
	python3 setup.py build

install:
	python3 setup.py install

clean_pyc:
	find ./ -name '*.pyc' -delete
	find ./ -name __pycache__ -delete
clean_build:
	rm -rf build policyd_rate-limit.egg-info dist
clean_tox:
	rm -rf .tox
clean_test_venv:
	rm -rf test_venv
clean: clean_pyc clean_build
	find ./ -name '*~' -delete
clean_all: clean_pyc clean_build clean_tox clean_test_venv

dist:
	python3 setup.py sdist

test_venv: dist
	mkdir -p test_venv
	virtualenv test_venv
	test_venv/bin/pip install -U policyd-rate-limit -f ./dist/policyd-rate-limit-${VERSION}.tar.gz
