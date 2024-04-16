################################################################################
#
# libparserutils
#
################################################################################

LIBPARSERUTILS_SITE = http://git.netsurf-browser.org/libparserutils.git
LIBPARSERUTILS_SITE_METHOD = git
LIBPARSERUTILS_VERSION = release/0.2.5
LIBPARSERUTILS_INSTALL_STAGING = YES
LIBPARSERUTILS_DEPENDENCIES = \
	host-netsurf-buildsystem
LIBPARSERUTILS_LICENSE = MIT
LIBPARSERUTILS_LICENSE_FILES = README

# The build system cannot build both the shared and static
# libraries. So when the Buildroot configuration requests to build
# both the shared and static variants, we build only the shared one.
ifeq ($(BR2_SHARED_LIBS)$(BR2_SHARED_STATIC_LIBS),y)
LIBPARSERUTILS_COMPONENT_TYPE = lib-shared
else
LIBPARSERUTILS_COMPONENT_TYPE = lib-static
endif

LIBPARSERUTILS_MAKE_OPTS = \
    PREFIX=/usr \
    NSSHARED=$(HOST_DIR)/share/netsurf-buildsystem

# Use $(MAKE1) since parallel build fails
define LIBPARSERUTILS_BUILD_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE1) -C $(@D) $(LIBPARSERUTILS_MAKE_OPTS) \
		COMPONENT_TYPE=$(LIBPARSERUTILS_COMPONENT_TYPE)
endef

define LIBPARSERUTILS_INSTALL_STAGING_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE1) -C $(@D) $(LIBPARSERUTILS_MAKE_OPTS) \
		DESTDIR=$(STAGING_DIR) COMPONENT_TYPE=$(LIBPARSERUTILS_COMPONENT_TYPE) install
endef

define LIBPARSERUTILS_INSTALL_TARGET_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE1) -C $(@D) $(LIBPARSERUTILS_MAKE_OPTS) \
		DESTDIR=$(TARGET_DIR) COMPONENT_TYPE=$(LIBPARSERUTILS_COMPONENT_TYPE) install
endef

$(eval $(generic-package))
