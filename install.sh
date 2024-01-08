#!/usr/bin/env bash

python3 setup.py install --optimize=1

cp nwg-clipman.svg /usr/share/pixmaps/
cp nwg-clipman.desktop /usr/share/applications/
