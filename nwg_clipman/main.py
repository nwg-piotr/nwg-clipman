#!/usr/bin/env python

"""
nwg-shell clipboard manager (GUI for cliphist by Senan Kelly)
Copyright (c) 2024-2025 Piotr Miller & Contributors
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
from gi.repository import Gtk, Gdk, GtkLayerShell, GdkPixbuf, Pango

dir_name = os.path.dirname(__file__)
pid = os.getpid()
args = None
voc = {}
tmp_file = os.path.join(temp_dir(), "clipman.dump")
window = None
search_entry = None
flowbox_wrapper = None
flowbox = None
preview_frame = None
btn_copy = None
selected_item = None
exit_code = None

if not is_command("cliphist") or not is_command("wl-copy"):
    # die if dependencies check failed
    eprint("Dependencies (cliphist, wl-clipboard) check failed, terminating")
    sys.exit(1)


def list_cliphist():
    # query cliphist
    try:
        output = subprocess.check_output("cliphist list", shell=True).decode('utf-8', errors="ignore").splitlines()
        return output
    except subprocess.CalledProcessError:
        return []


def quit_with_exit_code(ec):
    global exit_code
    exit_code = ec
    Gtk.main_quit()


def signal_handler(sig, frame):
    # gentle handle termination
    desc = {2: "SIGINT", 15: "SIGTERM"}
    if sig == 2 or sig == 15:
        eprint("Terminated with {}".format(desc[sig]))
        quit_with_exit_code(128 + sig)


def terminate_old_instance():
    pid_file = os.path.join(temp_dir(), "nwg-clipman-pid")
    if os.path.isfile(pid_file):
        try:
            old_pid = int(load_text_file(pid_file))
            if old_pid != pid:
                print(f"Attempting to kill the old instance in case it's still running, pid: {old_pid}")
                os.kill(old_pid, signal.SIGINT)
        except:
            pass
    # save new pid
    save_string(str(pid), pid_file)


def handle_keyboard(win, event):
    # on Esc key first search entry if not empty, else terminate
    global search_entry
    if event.type == Gdk.EventType.KEY_RELEASE and event.keyval == Gdk.KEY_Escape:
        if search_entry.get_text():
            search_entry.set_text("")
        else:
            quit_with_exit_code(1)


def load_vocabulary():
    # translate UI
    global voc
    # basic vocabulary (en_US)
    voc = load_json(os.path.join(dir_name, "langs", "en_US.json"))
    if not voc:
        eprint("Failed loading vocabulary, terminating")
        sys.exit(1)

    # check "interface-locale" forced in nwg-shell data file - if forced, and the file exists
    shell_data = load_shell_data()

    lang = os.getenv("LANG")
    if lang is None:
        lang = "en_US"
    else:
        lang = lang.split(".")[0] if not shell_data["interface-locale"] else shell_data["interface-locale"]

    # translate if translation available
    if lang != "en_US":
        loc_file = os.path.join(dir_name, "langs", "{}.json".format(lang))
        if os.path.isfile(loc_file):
            # localized vocabulary
            loc = load_json(loc_file)
            if not loc:
                eprint(f"Failed loading translation '{loc_file}'")
            else:
                print(f"Loaded translation file: '{loc_file}'")
                for key in loc:
                    voc[key] = loc[key]
        else:
            eprint(f"Translation into {lang} not found")


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
    # on flowbox item clicked
    global selected_item
    selected_item = child.get_name()
    name = bytes(child.get_name(), 'utf-8')
    subprocess.run(f"cliphist decode > {tmp_file}", shell=True, input=name)
    preview()


def preview():
    # create preview frame content
    pixbuf = None
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(tmp_file, 256, 256)
    except Exception as e:
        pass

    for child in preview_frame.get_children():
        child.destroy()
    preview_frame.set_label(voc["preview"])

    if pixbuf:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(256)
        preview_frame.add(scrolled)

        image = Gtk.Image.new_from_pixbuf(pixbuf)
        scrolled.add(image)
    else:
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(256)
        preview_frame.add(scrolled)

        text = load_text_file(tmp_file)
        if not text:
            text = voc["preview-unavailable"]
        label = Gtk.Label.new(text)
        label.set_max_width_chars(80)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.CHAR)

        scrolled.add(label)
    scrolled.set_property("name", "preview-window")

    btn_copy.set_sensitive(True)
    preview_frame.show_all()


def on_del_button(btn, name):
    # delete entry from cliphist
    eprint(f"Delete '{name}'")
    name = bytes(name, 'utf-8')
    subprocess.run("cliphist delete", shell=True, input=name)
    search_entry.set_text("")
    build_flowbox()


def on_copy_button(btn):
    eprint(f"Copying: '{selected_item}'")
    name = bytes(selected_item, 'utf-8')
    subprocess.run("cliphist decode | wl-copy", shell=True, input=name)
    Gtk.main_quit()


def on_wipe_button(btn):
    win = ConfirmationWindow()


class ConfirmationWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, type=Gtk.WindowType.POPUP)
        self.set_modal(True)
        self.set_destroy_with_parent(True)

        self.connect("key-release-event", self.handle_keyboard)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)

        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        vbox.set_property("name", "warning")
        self.add(vbox)
        lbl = Gtk.Label.new(f'{voc["clear-clipboard-history"]}?')
        vbox.pack_start(lbl, False, False, 6)
        hbox = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        vbox.pack_start(hbox, False, False, 6)
        btn = Gtk.Button.new_with_label(voc["clear"])
        btn.connect("clicked", self.clear_history)
        hbox.pack_start(btn, False, False, 0)

        btn = Gtk.Button.new_with_label(voc["close"])
        btn.connect("clicked", self.quit)
        hbox.pack_start(btn, False, False, 0)

        self.show_all()

    def quit(self, btn):
        self.destroy()

    def handle_keyboard(self, win, event):
        if event.type == Gdk.EventType.KEY_RELEASE and event.keyval == Gdk.KEY_Escape:
            self.destroy()

    def clear_history(self, btn):
        eprint("Wipe cliphist")
        subprocess.run("cliphist wipe", shell=True)

        quit_with_exit_code(2)


class FlowboxItem(Gtk.Box):
    def __init__(self, parts):
        Gtk.EventBox.__init__(self, orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        if args.numbers:
            label = Gtk.Label.new(parts[0])
            self.add(label)

        eb = Gtk.EventBox()
        self.pack_start(eb, True, True, 0)
        name = parts[1]
        label = Gtk.Label.new(name)
        label.set_max_width_chars(80)
        label.set_line_wrap(True)
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
    scrolled.set_min_content_height(300)
    scrolled.set_propagate_natural_height(True)
    flowbox_wrapper.add(scrolled)

    flowbox = Gtk.FlowBox()
    flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
    flowbox.connect("child-activated", on_child_activated)
    flowbox.set_valign(Gtk.Align.START)
    flowbox.set_max_children_per_line(1)
    scrolled.add(flowbox)

    # query cliphist
    clip_hist = list_cliphist()

    for line in clip_hist:
        try:
            parts = line.split("\t")
            _name = parts[1]

            item = FlowboxItem(parts)
            child = Gtk.FlowBoxChild()
            # we will be filtering by _name
            child.set_name(line)
            child.add(item)
            flowbox.add(child)
        except IndexError:
            eprint(f"Error parsing line: {line}")

    flowbox_wrapper.show_all()


def main():
    # handle signals
    catchable_sigs = set(signal.Signals) - {signal.SIGKILL, signal.SIGSTOP}
    for sig in catchable_sigs:
        signal.signal(sig, signal_handler)

    # arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="version",
                        version="%(prog)s version {}".format(__version__),
                        help="display Version information")
    parser.add_argument("-n", "--numbers", action="store_true", help="show item Numbers in the list")
    parser.add_argument("-w", "--window", action="store_true", help="run in regular Window, w/o layer shell")

    global args
    args = parser.parse_args()

    # kill running instance, if any
    terminate_old_instance()

    global search_entry

    # UI strings localization
    load_vocabulary()

    global window
    window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)

    def exit_1(widget):
        quit_with_exit_code(1)

    if not args.window:
        # attach to gtk-layer-shell
        GtkLayerShell.init_for_window(window)
        GtkLayerShell.set_layer(window, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_exclusive_zone(window, 0)
        GtkLayerShell.set_keyboard_mode(window, GtkLayerShell.KeyboardMode.ON_DEMAND)

    window.connect('destroy', exit_1)
    window.connect("key-release-event", handle_keyboard)

    vbox = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    vbox.set_property("name", "main-wrapper")
    window.add(vbox)

    hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
    vbox.pack_start(hbox, False, False, 0)

    # search entry
    search_entry = Gtk.SearchEntry()
    search_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "edit-clear-symbolic")
    search_entry.set_property("hexpand", True)
    search_entry.set_property("margin", 12)
    search_entry.set_size_request(700, 0)
    search_entry.connect('search_changed', flowbox_filter)
    hbox.pack_start(search_entry, False, True, 0)

    # "Clear" button next to search entry
    btn = Gtk.Button.new_with_label(voc["clear"])
    btn.set_property("valign", Gtk.Align.CENTER)
    btn.connect("clicked", on_wipe_button)
    hbox.pack_start(btn, False, False, 6)

    # wrapper for the flowbox
    global flowbox_wrapper
    flowbox_wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    flowbox_wrapper.set_property("margin-left", 12)
    flowbox_wrapper.set_property("margin-right", 12)
    vbox.pack_start(flowbox_wrapper, False, False, 0)

    # clear flowbox wrapper, build content
    build_flowbox()

    hbox = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    hbox.set_property("margin", 12)
    vbox.pack_end(hbox, False, False, 0)

    global preview_frame
    preview_frame = Gtk.Frame.new(voc["preview"])
    hbox.pack_start(preview_frame, True, True, 0)

    # temporary placeholder for future content preview
    placeholder_box = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    preview_frame.add(placeholder_box)
    placeholder_box.set_size_request(0, 256)
    preview_frame.show_all()

    # "Clear" and "Close" buttons
    ibox = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    ibox.set_homogeneous(True)
    hbox.pack_end(ibox, False, False, 0)

    # "Copy" button
    global btn_copy
    btn_copy = Gtk.Button.new_with_label(voc["copy"])
    btn_copy.set_property("valign", Gtk.Align.END)
    btn_copy.connect("clicked", on_copy_button)
    btn_copy.set_sensitive(False)
    ibox.pack_start(btn_copy, True, True, 0)

    # "Close" button
    btn = Gtk.Button.new_with_label(voc["close"])
    btn.set_property("valign", Gtk.Align.END)
    btn.connect("clicked", exit_1)
    ibox.pack_start(btn, True, True, 0)

    window.show_all()

    # customize styling
    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    style_context = Gtk.StyleContext()
    style_context.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    css = b""" 
    #main-wrapper { background-color: rgba(0, 0, 0, 0.1) }
    #preview-window { padding: 0 6px 0 6px }
    #del-btn { background: none; border: none; margin: 0; padding: 0 } 
    #del-btn:hover { background-color: rgba(255, 255, 255, 0.1) } 
    #warning { border: solid 1px; padding: 24px; margin: 6px}
    """
    provider.load_from_data(css)

    Gtk.main()


if __name__ == "__main__":
    main()
    sys.exit(exit_code)
