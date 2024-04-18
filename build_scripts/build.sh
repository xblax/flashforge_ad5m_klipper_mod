# !/bin/bash
# Build Wrapper Script for AD5M Klipper Mod
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $SCRIPT_DIR/env.sh

MULTICORE=-j$(nproc)
#####################################################
###### Buildroot Common Build Helper Functions ######
#####################################################

# initialize a buildroot build dir with config
buildroot_prepare() # args: path config_generator variant_name
{
	br_path="$1";
	br_name=$(basename "$1")
	br_config_generator="$2"
	mod_variant_name="$3"

	mkdir -p "$br_path"
	pushd "$br_path" > /dev/null

	# setup make environment, use external tree
    if [ ! -f Makefile ]; then
  		make O="$PWD" BR2_EXTERNAL="$BUILDROOT_EXT" -C "$BUILDROOT_GIT" $MULTICORE allnoconfig
  		echo "MOD_VARIANT=\"$variant\"" > .mod_env
    fi

	# backup old config
  	if [ -f .config ]; then
	    mv .config .config_old
    fi

	# generate new config from defconfigs
    $br_config_generator
    make $MULTICORE olddefconfig

	# restore old config if unchanged (keep timestamp)
    if [ -f .config_old ] && cmp --silent .config .config_old
    then
  	    mv -f .config_old .config
  	    log_info "$br_name: config up to date"
    else
        rm -f .config_old
        log_info "$br_name: config initialized"
    fi

    popd > /dev/null
}

# (re-)build a buildroot project
buildroot_build_always() # args: path make_command
{
	br_path="$1";
	br_name=$(basename "$1")
	br_make="$2 $MULTICORE"

	pushd "$br_path" > /dev/null

	if [ -e "host" ] || [ -e "images" ] || [ -e "target" ] || \
	   find build/ -mindepth 1 -maxdepth 1 ! -name buildroot-config 2> /dev/null | read; then
	   log_warn "unclean build of $br_name"
	fi

	if $br_make
	then
		log_info "$br_name: build done"
	else
		log_error "$br_name: build failed"
		exit 1
	fi

	popd > /dev/null
}


# (re-)build a buildroot build dir if not uptodate
buildroot_build_if_needed() # args: path make_command target_file
{
	br_path="$1";
	br_name=$(basename "$1")
	br_make="$2 $MULTICORE"
	br_target_file="$3"

	pushd "$br_path" > /dev/null

	if [ -f "$br_target_file" ] && [ "$br_target_file" -nt .config ]
	then
		log_info "$br_name: target up to date"
	else
		buildroot_build_always "$br_path" "$br_make"
	fi

	popd > /dev/null
}

###########################################
###### Buildroot Mod SDK Build Steps ######
###########################################

defconfig_sdk() {
    cp "$BUILDROOT_CONFIGS/sdk" "$BUILDROOT_SDK/.config"
}

prepare_sdk() {
	buildroot_prepare "$BUILDROOT_SDK" "defconfig_sdk" "sdk"
}

build_sdk() {
	br_image=( "$BUILDROOT_SDK"/images/*sdk-buildroot.tar.gz )
	buildroot_build_if_needed "$BUILDROOT_SDK" "make sdk"  "$br_image"
}

rebuild_sdk() {
	buildroot_build_always "$BUILDROOT_SDK" "make sdk"
}

clean_sdk() {
  rm -rf "$BUILDROOT_SDK"
}

package_sdk()
{
	br_image=( "$BUILDROOT_SDK"/images/*sdk-buildroot.tar.gz )
	sdk_name="KlipperMod-SDK-$GIT_VERSION.tar.xz"
	mkdir -p $BUILD_PACKAGE
	gzip -dc "$br_image" | xz -T`nproc` > $BUILD_PACKAGE/$sdk_name
	log_info "sdk: created $sdk_name"
}

###############################################
###### Buildroot Mod Variant Build Steps ######
###############################################

variant_env()
{
	variant=$1
    br_builddir="$BUILDROOT_OUT/variant-$variant"
	br_image="$br_builddir/images/rootfs.tar"
	br_chroot="$br_builddir/images/chroot.tar.xz"
}

defconfig_variant() {
    variant_env $1
    pushd $br_builddir
  	# merge config fragments to .config
  	"$BUILDROOT_GIT"/support/kconfig/merge_config.sh "$BUILDROOT_CONFIGS/sdk" "$BUILDROOT_CONFIGS/base" "$BUILDROOT_CONFIGS/variant-$variant"
    popd > /dev/null
}

prepare_variant() {
	variant_env $1
	buildroot_prepare "$br_builddir" "defconfig_variant $variant" "$variant"
}

build_variant() {
	variant_env $1
	buildroot_build_if_needed "$br_builddir" "make" "$br_image"
}

rebuild_variant() {
	variant_env $1
	buildroot_build_always "$br_builddir" "make"
}

clean_variant() {
	variant_env $1
	rm -rf "$br_builddir"
}

package_variant() {
	variant_env $1
	rm -f "$br_chroot"
	xz -cT`nproc` "$br_image" > "$br_chroot"
	package_name="Adventurer5M-KlipperMod-$GIT_VERSION-$variant.tgz"
	package_name_pro="Adventurer5MPro-KlipperMod-$GIT_VERSION-$variant.tgz"
	mkdir -p $BUILD_PACKAGE
	tar -cf "$BUILD_PACKAGE/$package_name" -C "$GIT_ROOT/device_files/install" . -C "$br_builddir/images/" ./chroot.tar.xz
	cp "$BUILD_PACKAGE/$package_name" "$BUILD_PACKAGE/$package_name_pro"
	log_info "variant-$variant: created $package_name"
}

##############################
###### Misc Build Steps ######
##############################

package_uninstall()
{
	package_name="Adventurer5M-KlipperMod-uninstall.tgz"
	tar -cf "$BUILD_PACKAGE/$package_name" -C "$GIT_ROOT/device_files/uninstall" .
	log_info "uninstall: created $package_name"
}

checksums()
{
	pushd $BUILD_PACKAGE > /dev/null
	rm -f md5sums
	md5sum * > md5sums
	log_info "created checksums:"
	cat md5sums
	popd > /dev/null
}

cd $GIT_ROOT
GIT_VERSION=$(git describe)

# run command
$@
