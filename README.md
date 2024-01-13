# nwg-clipman

This program is a part of the [nwg-shell](https://nwg-piotr.github.io/nwg-shell) project.

Nwg-clipman is a GTK3-based GUI for Senan Kelly's [cliphist](https://github.com/sentriz/cliphist). It provides access to previously copied items, as well 
as management of the clipboard history from a window opened on gtk-layer-shell. The program is intended for use with
sway, Hyprland and other wlroots-based Wayland compositors.

![nwg-clipman-0 2 0](https://github.com/nwg-piotr/nwg-clipman/assets/20579136/03fa6649-4a56-42f8-a473-504cb169bc53)

## Features

- image & text history item preview;
- searching clipboard history by a textual phrase;
- deleting selected history item;
- clearing clipboard history.

## Dependencies

- python >= 3.6;
- python-gobject;
- gtk3;
- gtk-layer-shell;
- wl-clipboard;
- cliphist;
- xdg-utils.

## Installation

[![Packaging status](https://repology.org/badge/vertical-allrepos/nwg-clipman.svg)](https://repology.org/project/nwg-clipman/versions)

The program may be installed by cloning this repository and executing the `install.sh` script (make sure you installed
dependencies first). Then you need to edit your compositor config file, to enable storing clipboard history to cliphist.

Example for sway:

```text
exec wl-paste --type text --watch cliphist store
exec wl-paste --type image --watch cliphist store
```

Example for Hyprland:

```text
exec-once = wl-paste --type text --watch cliphist store
exec-once = wl-paste --type image --watch cliphist store
```

You may omit the second line if you don't want images to be remembered.

Then create a key binding to launch nwg-clipman:

Example for sway:

```text
bindsym Mod1+C exec nwg-clipman
```

Example for Hyprland:

```text
bind = ALT, C, exec, nwg-clipman
```

## Options

```text
❯ nwg-clipman -h
usage: nwg-clipman [-h] [-v] [-n] [-w]

options:
  -h, --help     show this help message and exit
  -v, --version  display Version information
  -n, --numbers  show item Numbers in the list
  -w, --window   run in regular Window, w/o layer shell
```

## Hints

- To see numbers in the cliboard history use the `nwg-clipman -n` command.
- If you'd like the window to open normally, not on the layer shell, use the `nwg-clipman -w` command.
- You may clear the search entry / close the program window with the `Esc` key.
