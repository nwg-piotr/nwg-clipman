#!/usr/bin/env bash

python3 setup.py install --optimize=1

cp nwg-clipman.svg /usr/share/pixmaps/
cp nwg-clipman.desktop /usr/share/applications/

install -Dm 644 -t "/usr/share/licenses/nwg-clipman" LICENSE
install -Dm 644 -t "/usr/share/doc/nwg-clipman" README.md