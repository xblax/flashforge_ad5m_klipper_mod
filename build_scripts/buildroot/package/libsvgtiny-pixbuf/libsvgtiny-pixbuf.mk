################################################################################
#
# Libsvgtiny-pixbuf
#
################################################################################

LIBSVGTINY_PIXBUF_VERSION = 0.0.2
LIBSVGTINY_PIXBUF_SITE = https://michael.orlitzky.com/code/releases
LIBSVGTINY_PIXBUF_SOURCE = libsvgtiny-pixbuf-0.0.2.tar.xz
LIBSVGTINY_PIXBUF_LICENSE = AGPL
LIBSVGTINY_PIXBUF_LICENSE_FILES = LICENSE
LIBSVGTINY_PIXBUF_INSTALL_TARGET = YES
LIBSVGTINY_PIXBUF_DEPENDENCIES = libsvgtiny cairo libxml2 gdk-pixbuf

$(eval $(autotools-package))
