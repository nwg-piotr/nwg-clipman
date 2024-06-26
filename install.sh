#!/usr/bin/env bash

install -Dm 644 -t "/usr/share/pixmaps" nwg-clipman.svg
install -Dm 644 -t "/usr/share/applications" nwg-clipman.desktop
install -Dm 644 -t "/usr/share/licenses/nwg-clipman" LICENSE
install -Dm 644 -t "/usr/share/doc/nwg-clipman" README.md


python -m build --wheel --no-isolation
[ -f /usr/bin/nwg-clipman ] && sudo rm /usr/bin/nwg-hello
python -m installer dist/*.whl
