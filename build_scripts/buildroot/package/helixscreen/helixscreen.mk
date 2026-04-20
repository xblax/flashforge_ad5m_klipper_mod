################################################################################
#
# helixscreen
#
################################################################################

# Pinned to a commit SHA on prestonbrown/helixscreen main.
# Bump this to a release tag once HelixScreen cuts one.
HELIXSCREEN_VERSION = 846a6e35dd7d0ae53baab6605bd23a77956f17f3
HELIXSCREEN_SITE = https://github.com/prestonbrown/helixscreen.git
HELIXSCREEN_SITE_METHOD = git
HELIXSCREEN_GIT_SUBMODULES = yes
HELIXSCREEN_LICENSE = GPL-3.0-or-later
HELIXSCREEN_LICENSE_FILES = LICENSE
HELIXSCREEN_DEPENDENCIES = libevdev openssl tslib

define HELIXSCREEN_BUILD_CMDS
	$(MAKE) $(TARGET_CONFIGURE_OPTS) PLATFORM_TARGET=ad5m-br -C $(@D)
endef

define HELIXSCREEN_INSTALL_TARGET_CMDS
	$(MAKE) $(TARGET_CONFIGURE_OPTS) PLATFORM_TARGET=ad5m-br \
		install DESTDIR=$(TARGET_DIR) -C $(@D)
endef

$(eval $(generic-package))
