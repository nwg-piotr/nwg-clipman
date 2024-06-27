#!/usr/bin/env bash

# Make sure you have 'python-build' 'python-installer' 'python-wheel' and 'python-setuptools' installed.

# Check if removed from site_packages
PROGRAM_NAME="nwg-clipman"
MODULE_NAME="nwg_clipman"
SITE_PACKAGES="$(python3 -c "import sysconfig; print(sysconfig.get_paths()['purelib'])")"
PATTERN="$SITE_PACKAGES/$MODULE_NAME*"

for path in $PATTERN; do
    if [ -e "$path" ]; then
        echo "WARNING: you need to remove '$PATTERN' first, terminating."
        exit 1
    fi
done

# Remove launcher script
[ -f "/usr/bin/$PROGRAM_NAME" ] && sudo rm "/usr/bin/$PROGRAM_NAME"

install -Dm 644 -t "/usr/share/pixmaps" "$PROGRAM_NAME.svg"
install -Dm 644 -t "/usr/share/applications" "$PROGRAM_NAME.desktop"
install -Dm 644 -t "/usr/share/licenses/$PROGRAM_NAME" LICENSE
install -Dm 644 -t "/usr/share/doc/$PROGRAM_NAME" README.md


python -m build --wheel --no-isolation
python -m installer dist/*.whl
