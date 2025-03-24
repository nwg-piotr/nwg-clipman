#!/usr/bin/env bash

PROGRAM_NAME="nwg-clipman"
MODULE_NAME="nwg_clipman"
SITE_PACKAGES="$(python3 -c "import sysconfig; print(sysconfig.get_paths()['purelib'])")"
PATTERN="$SITE_PACKAGES/$MODULE_NAME*"

# Remove from site_packages
for path in $PATTERN; do
    if [ -e "$path" ]; then
        echo "Removing $path"
        rm -r "$path"
    fi
done

[ -d "./dist" ] && rm -rf ./dist

# Remove launcher script
if [ -f "/usr/bin/$PROGRAM_NAME" ]; then
  echo "Removing /usr/bin/$PROGRAM_NAME"
  rm "/usr/bin/nwg-clipman"
fi

echo "Removing icon, .desktop file, license and readme"
rm -f "/usr/share/pixmaps/$PROGRAM_NAME.svg"
rm -f "/usr/share/applications/$PROGRAM_NAME.desktop"
rm -f "/usr/share/licenses/$PROGRAM_NAME/LICENSE"
rm -f "/usr/share/doc/$PROGRAM_NAME/README.md"
