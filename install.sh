#!/usr/bin/env bash

# Make sure you have 'python-build' 'python-installer' 'python-wheel' and 'python-setuptools' installed.
# Before reinstalling, delete '/usr/lib/python3.xx/site-packages/nwg_clipman*' (change to match your python version).

install -Dm 644 -t "/usr/share/pixmaps" nwg-clipman.svg
install -Dm 644 -t "/usr/share/applications" nwg-clipman.desktop
install -Dm 644 -t "/usr/share/licenses/nwg-clipman" LICENSE
install -Dm 644 -t "/usr/share/doc/nwg-clipman" README.md


python -m build --wheel --no-isolation
[ -f /usr/bin/nwg-clipman ] && sudo rm /usr/bin/nwg-clipman
python -m installer dist/*.whl
