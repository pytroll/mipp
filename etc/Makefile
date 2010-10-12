#
#
prefix = $(DESTDIR)/opt
config_files = ../etc/setup.sh $(wildcard ../etc/*.cfg)

build:
	@echo "Nothing to do for build"

clean:
	@echo "Nothing to do for clean"

install:
	@echo "Installing MIPP configuration files"
	@mkdir -p $(prefix)/etc/mipp;
	@list='$(config_files)'; \
	for f in $$list; do test ! -h $$f && install -m644 $$f $(prefix)/etc/mipp; done; \
	test -f $(prefix)/etc/mipp/meteosat07.cfg && (cd $(prefix)/etc/mipp && ln -s meteosat07.cfg met7.cfg); \
	test -f $(prefix)/etc/mipp/meteosat09.cfg && (cd $(prefix)/etc/mipp && ln -s meteosat09.cfg msg2.cfg);
