import logging
import gi
import os
import subprocess

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from ks_includes.screen_panel import ScreenPanel

logging.getLogger(__name__).setLevel(logging.INFO)

CONFIG_DIR = "/home/mks/printer_data/config"
PRINTER_CFG_PATH = os.path.join(CONFIG_DIR, "printer.cfg")


class Panel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        
        GRID_COLUMNS = 3
        BUTTON_SPACING = 25
        
        title_label = self._gtk.Label(_("Select Bed Mesh Grid Size"), "title")
        title_label.set_halign(Gtk.Align.CENTER)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        main_box.set_halign(Gtk.Align.CENTER)
        main_box.set_valign(Gtk.Align.CENTER)
        main_box.set_hexpand(True)
        main_box.set_vexpand(True)

        grid = Gtk.Grid()
        grid.set_column_spacing(BUTTON_SPACING)
        grid.set_row_spacing(BUTTON_SPACING)
        grid.set_halign(Gtk.Align.CENTER)

        grid.set_column_homogeneous(True)

        grid.set_row_homogeneous(True)

        buttons_data = [
            ("2x2", "color2"), ("3x3", "color3"), ("4x4", "color4"),
            ("5x5", "color1"), ("6x6", "color2"), ("7x7", "color3"),
            ("8x8", "color4"), ("9x9", "color1"), ("10x10", "color2"),
        ]

        for i, (grid_size, color) in enumerate(buttons_data):
            button = self._gtk.Button("adjust", _(f"{grid_size} Grid"), color, self.bts, Gtk.PositionType.LEFT, 1)
            button.set_hexpand(True)
            button.connect("clicked", self._update_probe_count, grid_size)
            
            col = i % GRID_COLUMNS
            row = i // GRID_COLUMNS
            grid.attach(button, col, row, 1, 1)

        button_custom = self._gtk.Button("edit", _("Custom Grid"), "color5", self.bts, Gtk.PositionType.LEFT, 1)
        button_custom.set_hexpand(True)
        button_custom.connect("clicked", self._on_custom_button_clicked)
        
        custom_button_row = (len(buttons_data) + GRID_COLUMNS - 1) // GRID_COLUMNS
        grid.attach(button_custom, 0, custom_button_row, GRID_COLUMNS, 1)

        main_box.pack_start(grid, False, False, 0)
        
        self.content.add(title_label)
        self.content.add(main_box)

    def _on_custom_button_clicked(self, widget):
        dialog = Gtk.Dialog(
            title=_("Custom Grid Size"),
            transient_for=self._screen,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL,
            _("OK"), Gtk.ResponseType.OK
        )
        dialog.get_content_area().set_spacing(15)

        label = Gtk.Label(label=_("Enter grid size (e.g., 11 for a 11x11 grid):"))
        entry = Gtk.Entry()
        entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
        
        entry.connect("activate", lambda e: dialog.response(Gtk.ResponseType.OK))

        dialog.get_content_area().add(label)
        dialog.get_content_area().add(entry)
        dialog.show_all()

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            text = entry.get_text()
            try:
                count = int(text)
                if count < 2:
                    self._screen.show_popup_message(_("Error: Grid size must be at least 2."), level=2)
                else:
                    self._update_probe_count(None, f"{count}x{count}")
            except ValueError:
                self._screen.show_popup_message(_("Error: Please enter a valid number."), level=2)
        
        dialog.destroy()

    def _get_active_config_file(self):
        try:
            with open(PRINTER_CFG_PATH, 'r') as f:
                for line in f:
                    line = line.strip()
                    if "[include EECAN1.cfg]" in line:
                        logging.info("Found active config: EECAN1.cfg")
                        return "EECAN1.cfg"
                    if "[include EECAN.cfg]" in line:
                        logging.info("Found active config: EECAN.cfg")
                        return "EECAN.cfg"
            return None
        except FileNotFoundError:
            logging.error(f"Main config file not found: {PRINTER_CFG_PATH}")
            self._screen.show_popup_message(_("Error: printer.cfg not found."), level=2)
            return None

    def _update_probe_count(self, widget, grid_size):       
        target_filename = self._get_active_config_file()
        if not target_filename:
            logging.error("Could not determine the active EECAN config file from printer.cfg.")
            self._screen.show_popup_message(_("Error: Active config not found in printer.cfg."), level=2)
            return
            
        target_config_path = os.path.join(CONFIG_DIR, target_filename)
        logging.info(f"Attempting to set probe_count to {grid_size} in {target_config_path}")

        try:
            if not os.path.exists(target_config_path):
                logging.error(f"Target config file does not exist: {target_config_path}")
                self._screen.show_popup_message(_("Error: Target config file does not exist."), level=2)
                return

            count = grid_size.split('x')[0]
            sed_command = f"s/^probe_count:.*/probe_count: {count}, {count}/"
            command_list = ["sed", "-i", sed_command, target_config_path]
            
            logging.info(f"Executing command: {' '.join(command_list)}")
            subprocess.run(command_list, capture_output=True, text=True, check=True)

            os.system("sync")
            logging.info(f"Sync command executed after updating {target_filename}.")
            logging.info(f"Successfully updated {target_filename}.")
            
            success_message = _(f"Probe count in {target_filename} set to {grid_size}.\n\nA Klipper firmware restart is required.")
            self._screen.show_popup_message(success_message, level=1)

        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to execute sed command on {target_filename}. Stderr: {e.stderr}")
            self._screen.show_popup_message(_("Error: Failed to update config file."), level=2)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            self._screen.show_popup_message(_("Error: An unknown error occurred."), level=2)
        finally:
            self.on_back()

    def activate(self):
        pass

    def on_back(self):
        self._screen.remove_panel(self)
        self._screen.update_panels()
        return True