################################################################################
#
# mainsail
#
################################################################################

MAINSAIL_VERSION = v2.14.0
MAINSAIL_SITE = https://github.com/mainsail-crew/mainsail/releases/download/$(MAINSAIL_VERSION)
MAINSAIL_SOURCE=mainsail.zip

define MAINSAIL_EXTRACT_CMDS 
	$(UNZIP) $(MAINSAIL_DL_DIR)/$(MAINSAIL_SOURCE) -d $(@D)/
endef

define MAINSAIL_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/opt/mainsail
	cp -a $(@D)/* $(TARGET_DIR)/opt/mainsail/
endef

$(eval $(generic-package))

