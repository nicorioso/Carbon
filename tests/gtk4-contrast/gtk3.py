import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

Gtk.init([])
settings = Gtk.Settings.get_default()
settings.set_property("gtk-font-name", "Adwaita Sans 11")
settings.set_property("gtk-enable-animations", False)
window = Gtk.OffscreenWindow()
window.set_default_size(610, 250)
body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=20)
entry = Gtk.Entry(text="Texto de prueba")
button = Gtk.Button(label="Acción disponible")
disabled = Gtk.Button(label="Acción deshabilitada", sensitive=False)
for widget in (Gtk.Label(label="GTK 3 · muestra de regresión"), entry, button, disabled):
    body.pack_start(widget, False, False, 0)
window.add(body)
window.show_all()
entry.grab_focus()
loop = GLib.MainLoop()


def capture():
    image = window.get_pixbuf()
    if image is None:
        raise RuntimeError("GTK 3 did not render the offscreen window")
    image.savev(sys.argv[1], "png", [], [])
    print("font", settings.get_property("gtk-font-name"))
    print("dark", settings.get_property("gtk-application-prefer-dark-theme"))
    loop.quit()
    return GLib.SOURCE_REMOVE


GLib.timeout_add(250, capture)
loop.run()
window.destroy()
