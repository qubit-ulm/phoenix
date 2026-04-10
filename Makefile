.PHONY: \
	welcome \
	doc \
	install-check \
	install-python \
	install-package \
	install-toolchain-help \
	install-configure \
	install-build \
	install-test \
	install-notes \
	install \
	release-dump \
	release-dump-dry \
	file-statistics

welcome:
	bash scripts/00_welcome.sh

doc:
	$(MAKE) -C doc html
	ln -sfn doc/_build/html/index.html documentation.html

install-check:
	bash scripts/01_system_check.sh

install-python:
	bash scripts/02_python_env.sh

install-package:
	bash scripts/03_install_package.sh

install-toolchain-help:
	bash scripts/04_suggest_toolchains.sh

install-configure:
	bash scripts/05_configure_backends.sh

install-build:
	bash scripts/06_build_support.sh

install-test:
	bash scripts/07_smoke_tests.sh

install-notes:
	bash scripts/08_post_install_notes.sh

install: \
	welcome \
	install-check \
	install-python \
	install-package \
	install-toolchain-help \
	install-configure \
	install-build \
	install-test \
	install-notes

release-dump:
	bash scripts/release_dump.sh

release-dump-dry:
	bash scripts/release_dump.sh --dry-run

file-statistics:
	bash scripts/file_statistics.sh
