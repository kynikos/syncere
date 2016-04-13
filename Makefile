BASEDIR=$(CURDIR)

SYNCERE=$(BASEDIR)/syncere.py

.PHONY: help
help:
	@echo 'make serve           serve the git repo with git-daemon        '
	@echo 'make test            run the tests                             '

.PHONY: serve
serve:
	git daemon --base-path=.. --export-all --reuseaddr --informative-errors --verbose

.PHONY: test
test:
	cd $(BASEDIR)/test; py.test -svx --basetemp=$(BASEDIR)/test/tmpdir/
