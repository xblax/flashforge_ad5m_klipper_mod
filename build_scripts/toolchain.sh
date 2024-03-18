#!/bin/bash
# Activate the Klipper Mod Cross Toolchain - sourced by build scripts

ENV_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $ENV_DIR/../env.sh
