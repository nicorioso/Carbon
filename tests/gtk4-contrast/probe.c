#include <adwaita.h>
#include <gtk/gtk.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static GtkWidget *window, *header, *title, *heading, *details, *entry, *button, *disabled, *row;
static GtkWidget *menu_button, *popover, *dialog;
static gboolean adwaita;
static const char *output;
static GtkInterfaceColorScheme portal_scheme;

static GtkInterfaceColorScheme read_portal(void) {
    GError *error = NULL;
    GDBusConnection *bus = g_bus_get_sync(G_BUS_TYPE_SESSION, NULL, &error);
    if (bus == NULL) g_error("%s", error->message);
    GVariant *reply = g_dbus_connection_call_sync(bus, "org.freedesktop.portal.Desktop",
        "/org/freedesktop/portal/desktop", "org.freedesktop.portal.Settings", "Read",
        g_variant_new("(ss)", "org.freedesktop.appearance", "color-scheme"),
        G_VARIANT_TYPE("(v)"), G_DBUS_CALL_FLAGS_NO_AUTO_START, 2000, NULL, &error);
    if (reply == NULL) g_error("%s", error->message);
    GVariant *outer = g_variant_get_child_value(reply, 0);
    GVariant *inner = g_variant_get_variant(outer);
    if (g_variant_is_of_type(inner, G_VARIANT_TYPE_VARIANT)) {
        GVariant *value = g_variant_get_variant(inner);
        g_variant_unref(inner);
        inner = value;
    }
    guint code = g_variant_get_uint32(inner);
    g_print("portal=%u\n", code);
    g_variant_unref(inner);
    g_variant_unref(outer);
    g_variant_unref(reply);
    g_object_unref(bus);
    switch (code) {
    case 0: return GTK_INTERFACE_COLOR_SCHEME_DEFAULT;
    case 1: return GTK_INTERFACE_COLOR_SCHEME_DARK;
    case 2: return GTK_INTERFACE_COLOR_SCHEME_LIGHT;
    default: g_error("Unexpected portal scheme %u", code);
    }
}

static void compare_widget(const char *name, GtkWidget *widget) {
    GdkRGBA color;
    graphene_rect_t bounds;
    gtk_widget_get_color(widget, &color);
    if (gtk_widget_compute_bounds(widget, window, &bounds))
        g_print("%s color=#%02x%02x%02x alpha=%.3f x=%.0f y=%.0f w=%.0f h=%.0f flags=%u\n", name,
                (unsigned)(color.red * 255 + .5), (unsigned)(color.green * 255 + .5),
                (unsigned)(color.blue * 255 + .5), color.alpha, bounds.origin.x, bounds.origin.y,
                bounds.size.width, bounds.size.height, gtk_widget_get_state_flags(widget));
}

static void render(GtkWidget *widget, const char *state) {
    int width = gtk_widget_get_width(widget), height = gtk_widget_get_height(widget);
    GtkSnapshot *snap = gtk_snapshot_new();
    gtk_snapshot_render_background(snap, gtk_widget_get_style_context(widget), 0, 0, width, height);
    GTK_WIDGET_GET_CLASS(widget)->snapshot(widget, snap);
    GskRenderNode *node = gtk_snapshot_free_to_node(snap);
    if (node == NULL) g_error("Widget snapshot is empty");
    GskRenderer *renderer = gsk_cairo_renderer_new();
    GError *error = NULL;
    if (!gsk_renderer_realize_for_display(renderer, gtk_widget_get_display(widget), &error))
        g_error("%s", error->message);
    GdkTexture *texture = gsk_renderer_render_texture(renderer, node,
        &GRAPHENE_RECT_INIT(0, 0, width, height));
    char *filename = g_strdup_printf("%s-%s.png", output, state);
    if (!gdk_texture_save_to_png(texture, filename)) g_error("Cannot save %s", filename);
    g_free(filename);
    g_object_unref(texture);
    gsk_render_node_unref(node);
    gsk_renderer_unrealize(renderer);
    g_object_unref(renderer);
}

static gboolean capture(gpointer arg) {
    const char *state = arg;
    g_print("[%s]\n", state);
    compare_widget("header", header);
    compare_widget("title", title);
    compare_widget("heading", heading);
    compare_widget("secondary", details);
    compare_widget("entry", entry);
    compare_widget("button", button);
    compare_widget("disabled", disabled);
    compare_widget("row", row);

    render(window, state);
    return G_SOURCE_REMOVE;
}

static gboolean set_active(gpointer unused) {
    gtk_widget_unset_state_flags(window, GTK_STATE_FLAG_BACKDROP);
    gtk_widget_unset_state_flags(header, GTK_STATE_FLAG_BACKDROP);
    gtk_widget_grab_focus(entry);
    gtk_editable_select_region(GTK_EDITABLE(entry), 0, 5);
    gtk_widget_set_state_flags(entry, GTK_STATE_FLAG_FOCUSED | GTK_STATE_FLAG_FOCUS_VISIBLE, FALSE);
    return G_SOURCE_REMOVE;
}
static gboolean set_inactive(gpointer unused) {
    gtk_window_set_focus(GTK_WINDOW(window), NULL);
    gtk_widget_unset_state_flags(entry, GTK_STATE_FLAG_FOCUSED | GTK_STATE_FLAG_FOCUS_VISIBLE);
    gtk_widget_set_state_flags(window, GTK_STATE_FLAG_BACKDROP, FALSE);
    gtk_widget_set_state_flags(header, GTK_STATE_FLAG_BACKDROP, FALSE);
    return G_SOURCE_REMOVE;
}
static gboolean show_menu(gpointer unused) {
    set_active(unused);
    gtk_menu_button_popup(GTK_MENU_BUTTON(menu_button));
    return G_SOURCE_REMOVE;
}
static gboolean capture_menu(gpointer unused) {
    render(popover, "menu");
    gtk_menu_button_popdown(GTK_MENU_BUTTON(menu_button));
    return G_SOURCE_REMOVE;
}
static gboolean show_dialog(gpointer unused) {
    dialog = gtk_dialog_new_with_buttons("Vista previa", GTK_WINDOW(window),
        GTK_DIALOG_MODAL, "_Cerrar", GTK_RESPONSE_CLOSE, NULL);
    GtkWidget *message = gtk_label_new("Diálogo con contenido ficticio");
    gtk_widget_set_margin_top(message, 24);
    gtk_widget_set_margin_bottom(message, 24);
    gtk_box_append(GTK_BOX(gtk_dialog_get_content_area(GTK_DIALOG(dialog))), message);
    gtk_window_set_default_size(GTK_WINDOW(dialog), 350, 140);
    gtk_window_present(GTK_WINDOW(dialog));
    return G_SOURCE_REMOVE;
}
static gboolean capture_dialog(gpointer unused) {
    render(dialog, "dialog");
    gtk_window_destroy(GTK_WINDOW(dialog));
    return G_SOURCE_REMOVE;
}
static gboolean quit(gpointer loop) { g_main_loop_quit(loop); return G_SOURCE_REMOVE; }

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    adwaita = strcmp(argv[1], "adw") == 0;
    output = argv[2];
    gtk_init();
    if (adwaita) adw_init();
    GtkSettings *settings = gtk_settings_get_default();
    portal_scheme = read_portal();
    int native;
    g_object_get(settings, "gtk-interface-color-scheme", &native, NULL);
    g_print("native-setting=%d\n", native);
    if (!adwaita) {
        /* Broadway lacks the Wayland Settings mapping. Feed the same enum
           read from the real private portal into the GtkSettings property. */
        if (native != GTK_INTERFACE_COLOR_SCHEME_UNSUPPORTED)
            g_error("Unexpected Broadway provider for the interface scheme");
        g_object_set(settings, "gtk-interface-color-scheme", portal_scheme, NULL);
    }
    g_object_set(settings, "gtk-enable-animations", FALSE,
                 "gtk-font-name", "Adwaita Sans 11", NULL);
    int scheme;
    char *theme, *font;
    g_object_get(settings, "gtk-interface-color-scheme", &scheme,
                 "gtk-theme-name", &theme, "gtk-font-name", &font, NULL);
    g_print("theme=%s font=%s interface=%d\n", theme, font, scheme);
    g_free(theme);
    g_free(font);
    if (adwaita) {
        AdwStyleManager *style = adw_style_manager_get_default();
        g_print("adw-dark=%d policy=%d platform-support=%d\n", adw_style_manager_get_dark(style),
                adw_style_manager_get_color_scheme(style), adw_style_manager_get_system_supports_color_schemes(style));
    }

    window = adwaita ? adw_window_new() : gtk_window_new();
    gtk_window_set_default_size(GTK_WINDOW(window), 610, 390);
    gtk_window_set_title(GTK_WINDOW(window), "Carbon: título de prueba");
    title = gtk_label_new("Carbon: título de prueba");
    gtk_widget_add_css_class(title, "title");
    header = adwaita ? adw_header_bar_new() : gtk_header_bar_new();
    if (adwaita) adw_header_bar_set_title_widget(ADW_HEADER_BAR(header), title);
    else gtk_header_bar_set_title_widget(GTK_HEADER_BAR(header), title);

    GtkWidget *body = gtk_box_new(GTK_ORIENTATION_VERTICAL, 10);
    gtk_widget_set_margin_start(body, 20);
    gtk_widget_set_margin_end(body, 20);
    gtk_widget_set_margin_top(body, 16);
    gtk_widget_set_margin_bottom(body, 16);
    heading = gtk_label_new("Muestra de interfaz");
    gtk_widget_add_css_class(heading, "heading");
    gtk_label_set_xalign(GTK_LABEL(heading), 0);
    details = gtk_label_new("Texto secundario de prueba");
    gtk_widget_add_css_class(details, "dim-label");
    gtk_label_set_xalign(GTK_LABEL(details), 0);
    entry = gtk_entry_new();
    gtk_editable_set_text(GTK_EDITABLE(entry), "Texto seleccionado");
    button = gtk_button_new_with_label("Acción disponible");
    disabled = gtk_button_new_with_label("Acción deshabilitada");
    gtk_widget_set_sensitive(disabled, FALSE);
    GtkWidget *tools = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
    gtk_box_append(GTK_BOX(tools), gtk_image_new_from_icon_name("folder-symbolic"));
    gtk_box_append(GTK_BOX(tools), button);
    gtk_box_append(GTK_BOX(tools), disabled);
    menu_button = gtk_menu_button_new();
    gtk_menu_button_set_label(GTK_MENU_BUTTON(menu_button), "Menú");
    popover = gtk_popover_new();
    GtkWidget *menu = gtk_box_new(GTK_ORIENTATION_VERTICAL, 4);
    gtk_box_append(GTK_BOX(menu), gtk_button_new_with_label("Vista de ejemplo"));
    GtkWidget *disabled_item = gtk_button_new_with_label("Opción deshabilitada");
    gtk_widget_set_sensitive(disabled_item, FALSE);
    gtk_box_append(GTK_BOX(menu), disabled_item);
    gtk_popover_set_child(GTK_POPOVER(popover), menu);
    gtk_menu_button_set_popover(GTK_MENU_BUTTON(menu_button), popover);
    gtk_box_append(GTK_BOX(tools), menu_button);
    GtkWidget *list = gtk_list_box_new();
    row = gtk_label_new("01. Documento ficticio");
    gtk_label_set_xalign(GTK_LABEL(row), 0);
    GtkWidget *second = gtk_label_new("02. Carpeta de prueba");
    gtk_label_set_xalign(GTK_LABEL(second), 0);
    gtk_widget_set_size_request(row, -1, 30);
    gtk_widget_set_size_request(second, -1, 30);
    gtk_list_box_append(GTK_LIST_BOX(list), row);
    gtk_list_box_append(GTK_LIST_BOX(list), second);
    gtk_list_box_select_row(GTK_LIST_BOX(list), gtk_list_box_get_row_at_index(GTK_LIST_BOX(list), 0));
    for (GtkWidget **item = (GtkWidget *[]){heading, details, entry, tools, list, NULL}; *item; ++item)
        gtk_box_append(GTK_BOX(body), *item);

    if (adwaita) {
        GtkWidget *layout = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
        gtk_box_append(GTK_BOX(layout), header);
        gtk_box_append(GTK_BOX(layout), body);
        adw_window_set_content(ADW_WINDOW(window), layout);
    } else {
        gtk_window_set_titlebar(GTK_WINDOW(window), header);
        gtk_window_set_child(GTK_WINDOW(window), body);
    }
    gtk_window_present(GTK_WINDOW(window));
    GMainLoop *loop = g_main_loop_new(NULL, FALSE);
    g_timeout_add(150, set_active, NULL);
    g_timeout_add(330, capture, "focus");
    g_timeout_add(410, set_inactive, NULL);
    g_timeout_add(600, capture, "backdrop");
    g_timeout_add(680, show_menu, NULL);
    g_timeout_add(880, capture_menu, NULL);
    g_timeout_add(940, show_dialog, NULL);
    g_timeout_add(1140, capture_dialog, NULL);
    g_timeout_add(1220, quit, loop);
    g_main_loop_run(loop);
    g_main_loop_unref(loop);
    gtk_window_destroy(GTK_WINDOW(window));
    return 0;
}
