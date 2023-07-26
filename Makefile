.PHONY: clean build install dist uninstall
VERSION=`python3 setup.py -V`

WHL_FILES := $(wildcard dist/*.whl)
WHL_ASC := $(WHL_FILES:=.asc)
DIST_FILE := $(wildcard dist/*.tar.gz)
DIST_ASC := $(DIST_FILE:=.asc)

build:
	python3 setup.py build

install: dist
	pip3 -V
	[ ! -f /etc/policyd-rate-limit.yaml ] && cp -n policyd_rate_limit/policyd-rate-limit.yaml /etc/ || true
	cp -n init/policyd-rate-limit /etc/init.d
	cp -n init/policyd-rate-limit.service /etc/systemd/system/ || true
	cp -n init/policyd-rate-limit-clean.service /etc/systemd/system/policyd-rate-limit-clean.service
	cp -n init/policyd-rate-limit-clean.timer /etc/systemd/system/policyd-rate-limit-clean.timer
	pip3 install policyd-rate-limit --no-cache-dir -U --force-reinstall --no-deps --no-binary :all -f ./dist/policyd-rate-limit-${VERSION}.tar.gz
	systemctl daemon-reload
	systemctl enable policyd-rate-limit-clean.timer
	systemctl start policyd-rate-limit-clean.timer
uninstall:
	pip3 uninstall policyd-rate-limit || true
reinstall: uninstall install
purge: uninstall
	rm -f /etc/policyd-rate-limit.conf /etc/policyd-rate-limit.yaml
	rm -f /etc/init.d/policyd-rate-limit /etc/systemd/system/policyd-rate-limit.service
	rm -f /etc/systemd/system/policyd-rate-limit-clean.service /etc/systemd/system/policyd-rate-limit-clean.timer
	rm -rf /var/lib/policyd-rate-limit/

clean_pyc:
	find ./ -name '*.pyc' -delete
	find ./ -name __pycache__ -delete
clean_build:
	rm -rf build policyd_rate_limit.egg-info dist
clean_coverage:
	rm -rf htmlcov .coverage coverage.xml
clean_tox:
	rm -rf .tox tox_logs
clean_test_venv:
	rm -rf test_venv
clean: clean_pyc clean_build clean_coverage
	find ./ -name '*~' -delete
clean_all: clean clean_tox clean_test_venv

man_files:
	mkdir -p build/man/
	rst2man  docs/policyd-rate-limit.8.rst | sed 's/)(/(/g' > build/man/policyd-rate-limit.8
	rst2man  docs/policyd-rate-limit.yaml.5.rst | sed 's/)(/(/g' > build/man/policyd-rate-limit.yaml.5

dist:
	python3 setup.py sdist

test_venv/bin/python:
	python3 -m venv test_venv
	test_venv/bin/pip3 install -U -r requirements-dev.txt

test_venv: test_venv/bin/python


coverage: clean_coverage test_venv
	export PATH=test_venv/bin/:$$PATH; echo $$PATH; pytest
	test_venv/bin/coverage html
	test_venv/bin/coverage report

sign_release: $(WHL_ASC) $(DIST_ASC)

dist/%.asc:
	gpg --detach-sign -a $(@:.asc=)

test_venv/bin/twine: test_venv
	test_venv/bin/pip install twine

publish_pypi_release: test_venv test_venv/bin/twine dist sign_release
	test_venv/bin/twine upload --sign dist/*
