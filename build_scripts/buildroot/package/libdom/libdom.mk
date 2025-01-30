################################################################################
#
# libdom
#
################################################################################

LIBDOM_SITE = http://git.netsurf-browser.org/libdom.git
LIBDOM_SITE_METHOD = git
LIBDOM_VERSION = release/0.4.2
LIBDOM_INSTALL_STAGING = YES
LIBDOM_DEPENDENCIES = \
	libwapcaplet libhubbub libparserutils host-netsurf-buildsystem
LIBDOM_LICENSE = MIT
LIBDOM_LICENSE_FILES = README

# The build system cannot build both the shared and static
# libraries. So when the Buildroot configuration requests to build
# both the shared and static variants, we build only the shared one.
ifeq ($(BR2_SHARED_LIBS)$(BR2_SHARED_STATIC_LIBS),y)
LIBDOM_COMPONENT_TYPE = lib-shared
else
LIBDOM_COMPONENT_TYPE = lib-static
endif

LIBDOM_MAKE_OPTS = \
    PREFIX=/usr \
    NSSHARED=$(HOST_DIR)/share/netsurf-buildsystem

# Use $(MAKE1) since parallel build fails
define LIBDOM_BUILD_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE1) -C $(@D) $(LIBDOM_MAKE_OPTS) \
		COMPONENT_TYPE=$(LIBDOM_COMPONENT_TYPE)
endef

define LIBDOM_INSTALL_STAGING_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE1) -C $(@D) $(LIBDOM_MAKE_OPTS) \
		DESTDIR=$(STAGING_DIR) COMPONENT_TYPE=$(LIBDOM_COMPONENT_TYPE) install
endef

define LIBDOM_INSTALL_TARGET_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE1) -C $(@D) $(LIBDOM_MAKE_OPTS) \
		DESTDIR=$(TARGET_DIR) COMPONENT_TYPE=$(LIBDOM_COMPONENT_TYPE) install
endef

$(eval $(generic-package))
