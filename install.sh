#!/usr/bin/env bash

# Make sure you have 'python-build' 'python-installer' 'python-wheel' and 'python-setuptools' installed.

# Check if removed from site_packages
PROG_NAME="nwg_clipman"
SITE_PACKAGES="$(python3 -c "import sysconfig; print(sysconfig.get_paths()['purelib'])")"
PATTERN="$SITE_PACKAGES/$PROG_NAME*"

for path in $PATTERN; do
    if [ -e "$path" ]; then
        echo "WARNING: you need to remove '$PATTERN' first, terminating."
        exit 1
    fi
done

# Remove launcher script
[ -f "/usr/bin/$PROG_NAME" ] && sudo rm "/usr/bin/$PROG_NAME"

install -Dm 644 -t "/usr/share/pixmaps" nwg-clipman.svg
install -Dm 644 -t "/usr/share/applications" nwg-clipman.desktop
install -Dm 644 -t "/usr/share/licenses/nwg-clipman" LICENSE
install -Dm 644 -t "/usr/share/doc/nwg-clipman" README.md


python -m build --wheel --no-isolation
python -m installer dist/*.whl
