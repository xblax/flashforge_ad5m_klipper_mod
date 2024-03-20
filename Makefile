# Top Level Makefile for Flashfore ADM5 Klipper Mod
SHELL := /bin/bash
BUILD := build_scripts/build.sh
VARIANTS = lite klipperscreen

all: sdk lite klipperscreen uninstall checksums

# SDK targets
sdk: sdk_package

sdk_prepare:
	$(BUILD) prepare_sdk

sdk_build: sdk_prepare
	$(BUILD) build_sdk

sdk_rebuild: sdk_prepare
	$(BUILD) rebuild_sdk

sdk_package: sdk_build
	$(BUILD) package_sdk

sdk_clean:
	$(BUILD) clean_sdk

# Variant targets
define VARIANT_RULES

$(1): $(1)_package

$(1)_prepare:
	$(BUILD) prepare_variant $(1)

$(1)_build: sdk_build $(1)_prepare
	$(BUILD) build_variant $(1)

$(1)_rebuild: sdk_build $(1)_prepare
	$(BUILD) rebuild_variant $(1)

$(1)_package: $(1)_build
	$(BUILD) package_variant $(1)

$(1)_clean:
	$(BUILD) clean_variant $(1)

endef

$(foreach variant,$(VARIANTS),$(eval $(call VARIANT_RULES,$(variant))))

# Misc targets
uninstall: uninstall_package

uninstall_package:
	$(BUILD) package_uninstall

checksums:
	$(BUILD) checksums
