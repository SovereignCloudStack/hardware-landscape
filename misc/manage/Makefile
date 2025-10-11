SHELL = bash

activate = source venv/bin/activate
python = python3

check:
	@# run sequentially so the output is easier to read
	${MAKE} --no-print-directory lint
	${MAKE} --no-print-directory type-check
	${MAKE} --no-print-directory test
.PHONY: check


venv/bin/activate: requirements.txt
	../../landscape_ctl deps

deps: venv/bin/activate
.PHONY: deps

lint: deps
	${activate} && ${python} -m flake8 lib *_ctl.py
.PHONY: lint

type-check: deps
	${activate} && ${python} -m mypy --no-color-output --pretty  lib *_ctl.py
.PHONY: type-check

test: deps
	${activate} && ${python} -m pytest test
.PHONY: test

