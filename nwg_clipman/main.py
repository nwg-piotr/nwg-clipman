#!/usr/bin/env python

"""
nwg-shell clipboard manager (GUI for cliphist by Senan Kelly)
Copyright (c) 2024 Piotr Miller
e-mail: nwg.piotr@gmail.com
Project: https://github.com/nwg-piotr/nwg-clipman
License: MIT
"""

import argparse
import os.path
import signal
import sys
import gi

gi.require_version('Gtk', '3.0')
try:
    gi.require_version('GtkLayerShell', '0.1')
except ValueError:
    raise RuntimeError('\n\n' +
                       'If you haven\'t installed GTK Layer Shell, you need to point Python to the\n' +
                       'library by setting GI_TYPELIB_PATH and LD_LIBRARY_PATH to <build-dir>/src/.\n' +
                       'For example you might need to run:\n\n' +
                       'GI_TYPELIB_PATH=build/src LD_LIBRARY_PATH=build/src python3 ' + ' '.join(sys.argv))

from nwg_clipman.tools import *
from nwg_clipman.__about__ import __version__
from gi.repository import Gtk, Gdk, GtkLayerShell

dir_name = os.path.dirname(__file__)
pid = os.getpid()
args = None
voc = {}
search_entry = None
flowbox_wrapper = None
flowbox = None

if not is_command("cliphist") or not is_command("wl-copy"):
    eprint("Dependencies (cliphist, wl-clipboard) check failed, terminating")
    sys.exit(1)


def list_cliphist():
    try:
        output = subprocess.check_output("cliphist list", shell=True)
        # convert to string, regardless of disallowed chars
        o = ''.join(map(chr, output))
        return o
    except subprocess.CalledProcessError:
        return ""


def signal_handler(sig, frame):
    # gentle handle termination
    desc = {2: "SIGINT", 15: "SIGTERM"}
    if sig == 2 or sig == 15:
        eprint("Terminated with {}".format(desc[sig]))
        Gtk.main_quit()


def terminate_old_instance():
    pid_file = os.path.join(temp_dir(), "nwg-clipman-pid")
    if os.path.isfile(pid_file):
        try:
            old_pid = int(load_text_file(pid_file))
            # if old_pid != pid:
            eprint(f"Attempting to kill the old instance in case it's still running, pid: {old_pid}")
            os.kill(old_pid, 15)
            print("terminating")
            sys.exit(0)
        except:
            pass
    # save new pid
    save_string(str(pid), pid_file)


def handle_keyboard(win, event):
    global search_entry
    # exit on Esc key, but...
    if event.type == Gdk.EventType.KEY_RELEASE and event.keyval == Gdk.KEY_Escape:
        # ...if search_entry not empty, clear it first
        if search_entry.get_text():
            search_entry.set_text("")
        else:
            Gtk.main_quit()


def load_vocabulary():
    global voc
    # basic vocabulary (en_US)
    voc = load_json(os.path.join(dir_name, "langs", "en_US"))
    if not voc:
        eprint("Failed loading vocabulary, terminating")
        sys.exit(1)

    # check "interface-locale" forced in nwg-shell data file, if forced, and the file exists
    shell_data = load_shell_data()

    lang = os.getenv("LANG")
    if lang is None:
        lang = "en_US"
    else:
        lang = lang.split(".")[0] if not shell_data["interface-locale"] else shell_data["interface-locale"]

    # translate if translation available
    if lang != "en_US":
        loc_file = os.path.join(dir_name, "langs", "{}".format(lang))
        if os.path.isfile(loc_file):
            # localized vocabulary
            loc = load_json(loc_file)
            if not loc:
                eprint("Failed loading translation into '{}'".format(lang))
            else:
                for key in loc:
                    voc[key] = loc[key]


def on_enter_notify_event(widget, event):
    # highlight item
    widget.set_state_flags(Gtk.StateFlags.DROP_ACTIVE, clear=False)
    widget.set_state_flags(Gtk.StateFlags.SELECTED, clear=False)


def on_leave_notify_event(widget, event):
    # clear highlight
    widget.unset_state_flags(Gtk.StateFlags.DROP_ACTIVE)
    widget.unset_state_flags(Gtk.StateFlags.SELECTED)


def flowbox_filter(_search_entry):
    # filter flowbox visibility by search_entry content
    def filter_func(fb_child, _text):
        if _text in fb_child.get_name():
            return True
        else:
            return False

    text = _search_entry.get_text()
    flowbox.set_filter_func(filter_func, text)


def on_child_activated(fb, child):
    # copy and terminate
    eprint(f"Copying: '{child.get_name()}'")
    subprocess.Popen(f'echo "{child.get_name()}" | cliphist decode | wl-copy', shell=True)
    Gtk.main_quit()


def on_del_button(btn, name):
    # delete entry from cliphist
    eprint(f"Delete '{name}'")
    name = bytes(name, 'utf-8')
    subprocess.run("cliphist delete", shell=True, input=name)
    search_entry.set_text("")
    build_flowbox()


def on_wipe_button(btn):
    # wipe cliphist
    eprint("Wipe cliphist")
    subprocess.run("cliphist wipe", shell=True)

    Gtk.main_quit()


class FlowboxItem(Gtk.Box):
    def __init__(self, parts):
        Gtk.EventBox.__init__(self, orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        if not args.numbers:
            label = Gtk.Label.new(parts[0])
            self.add(label)

        eb = Gtk.EventBox()
        self.pack_start(eb, True, True, 0)
        name = parts[1]
        label = Gtk.Label.new(name)
        label.set_property("halign", Gtk.Align.START)
        eb.add(label)

        button = Gtk.Button.new_from_icon_name("edit-clear", Gtk.IconSize.MENU)
        button.set_property("name", "del-btn")
        button.set_property("margin-right", 9)
        button.connect("clicked", on_del_button, "\t".join(parts))
        self.pack_end(button, False, False, 0)

        eb.connect('enter-notify-event', on_enter_notify_event)
        eb.connect('leave-notify-event', on_leave_notify_event)


def build_flowbox():
    global flowbox_wrapper
    global flowbox
    # destroy flowbox wrapper content, if any
    for item in flowbox_wrapper.get_children():
        item.destroy()

    # build from scratch
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_min_content_height(400)
    scrolled.set_propagate_natural_height(True)
    flowbox_wrapper.add(scrolled)

    flowbox = Gtk.FlowBox()
    flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
    flowbox.connect("child-activated", on_child_activated)
    flowbox.set_valign(Gtk.Align.START)
    flowbox.set_max_children_per_line(1)
    scrolled.add(flowbox)

    # query cliphist
    clip_hist = list_cliphist().splitlines()

    for line in clip_hist:
        parts = line.split("\t")
        _name = parts[1]

        item = FlowboxItem(parts)

        child = Gtk.FlowBoxChild()
        # we will be filtering by _name
        child.set_name(_name)
        child.add(item)
        flowbox.add(child)

    flowbox_wrapper.show_all()


def main():
    # handle signals
    catchable_sigs = set(signal.Signals) - {signal.SIGKILL, signal.SIGSTOP}
    for sig in catchable_sigs:
        signal.signal(sig, signal_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="version",
                        version="%(prog)s version {}".format(__version__),
                        help="display Version information")
    parser.add_argument("-n", "--numbers", action="store_true", help="hide item Numbers in the list")
    parser.add_argument("-w", "--window", action="store_true", help="run in regular Window, w/o layer shell")

    global args
    args = parser.parse_args()

    # kill running instance, if any
    terminate_old_instance()

    global search_entry
    global flowbox_wrapper
    global search_entry

    load_vocabulary()

    window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)

    if not args.window:
        # attach to gtk-layer-shell
        GtkLayerShell.init_for_window(window)
        GtkLayerShell.set_layer(window, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_exclusive_zone(window, 0)
        GtkLayerShell.set_keyboard_mode(window, GtkLayerShell.KeyboardMode.ON_DEMAND)

    window.connect('destroy', Gtk.main_quit)
    window.connect("key-release-event", handle_keyboard)

    vbox = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    window.add(vbox)

    search_entry = Gtk.SearchEntry()
    search_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "edit-clear-symbolic")
    search_entry.set_property("hexpand", True)
    search_entry.set_property("margin", 12)
    search_entry.set_size_request(750, 0)
    search_entry.connect('search_changed', flowbox_filter)
    vbox.pack_start(search_entry, False, True, 0)

    # wrapper for the flowbox (global)
    flowbox_wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    flowbox_wrapper.set_property("margin-left", 12)
    flowbox_wrapper.set_property("margin-right", 12)
    vbox.pack_start(flowbox_wrapper, False, False, 0)

    # clear flowbox wrapper, build content
    build_flowbox()

    # "Clear" and "Close" buttons
    hbox = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    hbox.set_property("margin", 12)
    vbox.pack_end(hbox, False, False, 0)
    btn = Gtk.Button.new_with_label(voc["close"])
    btn.connect("clicked", Gtk.main_quit)
    hbox.pack_end(btn, False, False, 0)
    btn = Gtk.Button.new_with_label(voc["clear"])
    btn.connect("clicked", on_wipe_button)
    hbox.pack_end(btn, False, False, 0)

    window.show_all()

    # customize buttons' look
    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    style_context = Gtk.StyleContext()
    style_context.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    css = b""" 
    #del-btn { background: none; border: none; margin: 0; padding: 0 } 
    #del-btn:hover { background-color: rgba(255, 255, 255, 0.1) } 
    """
    provider.load_from_data(css)

    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())
