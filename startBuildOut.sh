#!/bin/bash
#
# start a virtual screen buffer to run unittests against
#
ELEXIR_LIB_PATH=""
SQLALCHEMY_LIB_PATH=""
XVFB_DISPLAY=":99"
XVFB_SCREEN="0"
set -e
if [ "$(id -u)" != "0" ]; then
        echo "Not running as root user. Good."
else   
        echo "This script must be run as a normal user (uid>=1000)";
        exit 1
fi
echo "Checking if Xvfb is running..."
if [ -n "`ps -e | grep Xvfb`" ]; then
        echo "Xvfb is running. Good."
else
        echo "Xvfb is not running."
        echo "Checking if Xvfb is installed..."
        if which Xvfb >/dev/null; then
                echo "Xvfb is installed. Good."
                echo "Staring Xvfb on DISPLAY $XVFB_DISPLAY on screen $XVFB_SCREEN".
                Xvfb "$XVFB_DISPLAY" -ac -screen "$XVFB_SCREEN" 1024x768x24&
        else
                echo "Xvfb is not installed or this script was unable to find it."
                exit 1
        fi
fi
export DISPLAY="$XVFB_DISPLAY"
export PYTHONPATH=".:../libraries"
