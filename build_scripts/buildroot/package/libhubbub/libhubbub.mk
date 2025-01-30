################################################################################
#
# libhubbub
#
################################################################################

LIBHUBBUB_SITE = http://git.netsurf-browser.org/libhubbub.git
LIBHUBBUB_SITE_METHOD = git
LIBHUBBUB_VERSION = release/0.3.8
LIBHUBBUB_INSTALL_STAGING = YES
LIBHUBBUB_DEPENDENCIES = \
	libparserutils host-netsurf-buildsystem
LIBHUBBUB_LICENSE = MIT
LIBHUBBUB_LICENSE_FILES = README

# The build system cannot build both the shared and static
# libraries. So when the Buildroot configuration requests to build
# both the shared and static variants, we build only the shared one.
ifeq ($(BR2_SHARED_LIBS)$(BR2_SHARED_STATIC_LIBS),y)
LIBHUBBUB_COMPONENT_TYPE = lib-shared
else
LIBHUBBUB_COMPONENT_TYPE = lib-static
endif

LIBHUBBUB_MAKE_OPTS = \
    PREFIX=/usr \
    NSSHARED=$(HOST_DIR)/share/netsurf-buildsystem

# Use $(MAKE1) since parallel build fails
define LIBHUBBUB_BUILD_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE1) -C $(@D) $(LIBHUBBUB_MAKE_OPTS) \
		COMPONENT_TYPE=$(LIBHUBBUB_COMPONENT_TYPE)
endef

define LIBHUBBUB_INSTALL_STAGING_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE1) -C $(@D) $(LIBHUBBUB_MAKE_OPTS) \
		DESTDIR=$(STAGING_DIR) COMPONENT_TYPE=$(LIBHUBBUB_COMPONENT_TYPE) install
endef

define LIBHUBBUB_INSTALL_TARGET_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE1) -C $(@D) $(LIBHUBBUB_MAKE_OPTS) \
		DESTDIR=$(TARGET_DIR) COMPONENT_TYPE=$(LIBHUBBUB_COMPONENT_TYPE) install
endef

$(eval $(generic-package))
