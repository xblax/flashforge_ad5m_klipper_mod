################################################################################
#
# libsvgtiny
#
################################################################################

LIBSVGTINY_SITE = http://git.netsurf-browser.org/libsvgtiny.git
LIBSVGTINY_SITE_METHOD = git
LIBSVGTINY_VERSION = release/0.1.8
LIBSVGTINY_INSTALL_STAGING = YES
LIBSVGTINY_DEPENDENCIES = \
	libdom libwapcaplet host-gperf host-pkgconf host-netsurf-buildsystem
LIBSVGTINY_LICENSE = MIT
LIBSVGTINY_LICENSE_FILES = README

# The build system cannot build both the shared and static
# libraries. So when the Buildroot configuration requests to build
# both the shared and static variants, we build only the shared one.
ifeq ($(BR2_SHARED_LIBS)$(BR2_SHARED_STATIC_LIBS),y)
LIBSVGTINY_COMPONENT_TYPE = lib-shared
else
LIBSVGTINY_COMPONENT_TYPE = lib-static
endif

LIBSVGTINY_MAKE_OPTS = \
    PREFIX=/usr \
    NSSHARED=$(HOST_DIR)/share/netsurf-buildsystem

# Use $(MAKE1) since parallel build fails
define LIBSVGTINY_BUILD_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE1) -C $(@D) $(LIBSVGTINY_MAKE_OPTS) \
		COMPONENT_TYPE=$(LIBSVGTINY_COMPONENT_TYPE)
endef

define LIBSVGTINY_INSTALL_STAGING_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE1) -C $(@D) $(LIBSVGTINY_MAKE_OPTS) \
		DESTDIR=$(STAGING_DIR) COMPONENT_TYPE=$(LIBSVGTINY_COMPONENT_TYPE) install
endef

define LIBSVGTINY_INSTALL_TARGET_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE1) -C $(@D) $(LIBSVGTINY_MAKE_OPTS) \
		DESTDIR=$(TARGET_DIR) COMPONENT_TYPE=$(LIBSVGTINY_COMPONENT_TYPE) install
endef

$(eval $(generic-package))
