all: sync

sync: requirements.txt
	@echo pip-sync $^
	@venv/bin/pip-sync $^

%.txt: %.in venv
	@echo pip-compile $<
	@env CUSTOM_COMPILE_COMMAND="make $@" venv/bin/pip-compile $<

venv:
	[ -d venv ] || {      \
	    virtualenv venv;  \
	    venv/bin/pip install --upgrade pip;       \
	    venv/bin/python -m pip install pip-tools; \
	}

.PHONY: all sync
