################################################################################
#
# Guppyscreen mkfile
#
################################################################################

GUPPYSCREEN_VERSION = origin/flashforge_ad5m 
GUPPYSCREEN_SITE = "git@github.com:consp/guppyscreen.git"
GUPPYSCREEN_SITE_METHOD = git
GUPPYSCREEN_GIT_SUBMODULES = yes
GUPPYSCREEN_LICENSE = GPL-3.0+
GUPPYSCREEN_LICENSE_FILES = COPYING
GUPPYSCREEN_DEPENDENCIES = libevdev

define GUPPYSCREEN_BUILD_CMDS
$(BASH) pushd $(@D)/lv_drivers; patch --forward -p1 < ../patches/0001-lv_driver_fb_ioctls_flashforge_ad5m.patch; popd;
$(BASH) pushd $(@D)/spdlog; patch --forward -p1 < ../patches/0002-spdlog_fmt_initializer_list.patch; popd;
GUPPY_FF5M_SCREEN=1 $(MAKE) $(TARGET_CONFIGURE_OPTS) -C $(@D) libhv.a
GUPPY_FF5M_SCREEN=1 $(MAKE) $(TARGET_CONFIGURE_OPTS) -C $(@D) libspdlog.a
GUPPY_FF5M_SCREEN=1 $(MAKE) $(TARGET_CONFIGURE_OPTS) -C $(@D) wpaclient
GUPPY_FF5M_SCREEN=1 $(MAKE) $(TARGET_CONFIGURE_OPTS) -C $(@D)
endef

# GUPPY_FF5M_SCREEN=1 $(MAKE) $(TARGET_CONFIGURE_OPTS) -C $(@D) libhvclean
# GUPPY_FF5M_SCREEN=1 $(MAKE) $(TARGET_CONFIGURE_OPTS) -C $(@D) spdlogclean
# GUPPY_FF5M_SCREEN=1 $(MAKE) $(TARGET_CONFIGURE_OPTS) -C $(@D) wpaclean
# GUPPY_FF5M_SCREEN=1 $(MAKE) $(TARGET_CONFIGURE_OPTS) -C $(@D) clean
#
define GUPPYSCREEN_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/build/bin/guppyscreen $(TARGET_DIR)/root/printer_software/guppyscreen/guppyscreen
endef

$(eval $(generic-package))
