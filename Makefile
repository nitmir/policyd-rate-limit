.PHONY: clean build install dist uninstall
VERSION=`python3 setup.py -V`

build:
	python3 setup.py build

install: dist
	pip3 -V
	[ ! -f /etc/policyd-rate-limit.conf ] && cp -n policyd_rate_limit/policyd-rate-limit.conf /etc/ || true
	cp -n init/policyd-rate-limit /etc/init.d
	cp -n init/policyd-rate-limit.service /etc/systemd/system/ || true
	pip3 install policyd-rate-limit -U -f ./dist/policyd-rate-limit-${VERSION}.tar.gz
	systemctl daemon-reload
uninstall:
	pip3 uninstall policyd-rate-limit || true
reinstall: uninstall install
purge: uninstall
	rm -f /etc/policyd-rate-limit.conf /etc/init.d/policyd-rate-limit /etc/systemd/system/policyd-rate-limit.service

clean_pyc:
	find ./ -name '*.pyc' -delete
	find ./ -name __pycache__ -delete
clean_build:
	rm -rf build policyd_rate_limit.egg-info dist
clean: clean_pyc clean_build
	find ./ -name '*~' -delete

dist:
	python3 setup.py sdist
