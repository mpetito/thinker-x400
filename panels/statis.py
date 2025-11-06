# -*- coding: utf-8 -*-
import gi
import requests
import threading
import json
import logging
import math

gi.require_version("Gtk", "3.0")
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Pango, GLib, cairo, PangoCairo
from ks_includes.screen_panel import ScreenPanel

class Panel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        
        self.title = title
        self.labels = {}
        # API Endpoints
        self.totals_api_url = "http://127.0.0.1/server/history/totals"
        self.history_list_api_url = "http://127.0.0.1/server/history/list"
        
        self.chart_data = None
        
        screen_layout_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        title_box.set_margin_top(10)
        title_box.set_margin_bottom(5)
        main_title_label = Gtk.Label()
        main_title_label.set_markup(f"<span font_desc='Sans Bold 24'>{_('Statistics')}</span>")
        main_title_label.set_halign(Gtk.Align.START)
        title_box.pack_start(main_title_label, False, False, 0)
        screen_layout_box.pack_start(title_box, False, False, 0)
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_start(20)
        separator.set_margin_end(20)
        screen_layout_box.pack_start(separator, False, False, 0)
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        stats_grid = Gtk.Grid()
        stats_grid.set_column_spacing(20)
        stats_grid.set_row_spacing(20)
        stats_grid.set_halign(Gtk.Align.START)
        stats_grid.set_valign(Gtk.Align.START)
        self.create_stat_row(stats_grid, _("Total Print Time"), "Loading...", 0, 'total_print_time')
        self.create_stat_row(stats_grid, _("Longest Print Time"), "Loading...", 1, 'longest_print')
        self.create_stat_row(stats_grid, _("Average Print Time"), "Loading...", 2, 'average_print_time')
        self.create_stat_row(stats_grid, _("Total Filament Used"), "Loading...", 3, 'total_filament_used')
        self.create_stat_row(stats_grid, _("Job Count"), "Loading...", 4, 'total_jobs')
        chart_layout_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        chart_layout_box.set_hexpand(True)
        chart_layout_box.set_vexpand(True)
        chart_layout_box.set_halign(Gtk.Align.CENTER)
        chart_layout_box.set_valign(Gtk.Align.START)
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(350, 250)
        self.drawing_area.connect("draw", self.on_draw_chart)
        chart_layout_box.pack_start(self.drawing_area, False, False, 0)
        chart_label = Gtk.Label(label=_("CHART"))
        chart_label.set_halign(Gtk.Align.CENTER)
        chart_layout_box.pack_start(chart_label, False, False, 0)
        main_box.pack_start(stats_grid, False, False, 0)
        main_box.pack_start(chart_layout_box, False, False, 0)
        screen_layout_box.pack_start(main_box, False, False, 0)
        self.content.add(screen_layout_box)

    def activate(self):
        self.update_stats()

    def update_stats(self):
        self.chart_data = None
        self.drawing_area.queue_draw()
        for key in self.labels:
            if self.labels[key].get_label() != "N/A":
                self.labels[key].set_text("Loading...")
        thread = threading.Thread(target=self._load_stats_data, daemon=True)
        thread.start()

    def _load_stats_data(self):
        try:
            response_totals = requests.get(self.totals_api_url, timeout=5)
            response_totals.raise_for_status()
            totals_data = response_totals.json()
            GLib.idle_add(self._update_ui_totals, totals_data['result']['job_totals'])
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get totals from API: {e}")
            GLib.idle_add(self._update_ui_error, "Error: No Connection")
            return  
        except (KeyError, json.JSONDecodeError) as e:
            logging.error(f"Failed to parse totals API response: {e}")
            GLib.idle_add(self._update_ui_error, "Error: Invalid Data")
            return

        try:
            all_jobs = []
            start_index = 0
            page_limit = 100
            while True:
                paginated_url = f"{self.history_list_api_url}?start={start_index}&limit={page_limit}"
                response_page = requests.get(paginated_url, timeout=10)
                response_page.raise_for_status()
                history_page_data = response_page.json()
                jobs_chunk = history_page_data['result']['jobs']
                
                if not jobs_chunk:
                    break
                
                all_jobs.extend(jobs_chunk)
                start_index += page_limit

                if len(jobs_chunk) < page_limit:
                    break
            
            full_history_result = {"jobs": all_jobs, "count": len(all_jobs)}
            GLib.idle_add(self._update_ui_chart, full_history_result)
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get history from API: {e}")
            GLib.idle_add(self._update_ui_chart_error)
        except (KeyError, json.JSONDecodeError) as e:
            logging.error(f"Failed to parse history API response: {e}")
            GLib.idle_add(self._update_ui_chart_error)

    def _update_ui_totals(self, job_totals):
        total_print_time = job_totals.get('total_print_time', 0)
        total_jobs = job_totals.get('total_jobs', 0)
        average_time = total_print_time / total_jobs if total_jobs > 0 else 0
        
        self.labels['average_print_time'].set_text(self._format_time(average_time))
        self.labels['total_print_time'].set_text(self._format_time(total_print_time))
        self.labels['longest_print'].set_text(self._format_time(job_totals.get('longest_print', 0)))
        self.labels['total_filament_used'].set_text(f"{job_totals.get('total_filament_used', 0) / 1000:.1f} m")
        self.labels['total_jobs'].set_text(str(total_jobs))
        return False

    def _update_ui_chart(self, history_result):
        status_counts = {
            "finish_printing": 0, "unprint": 0, "klippy_closed": 0, "other": 0
        }
        for job in history_result.get('jobs', []):
            status = job.get('status')
            if status == 'completed': 
                status_counts['finish_printing'] += 1
            elif status == 'cancelled': 
                status_counts['unprint'] += 1
            elif status in ['klippy_shutdown', 'klippy_disconnect']: 
                status_counts['klippy_closed'] += 1
            else: 
                status_counts['other'] += 1
        
        self.chart_data = [
            {"label": _("Finished"), "value": status_counts["finish_printing"], "color": (0.2, 0.7, 0.3)},
            {"label": _("Cancelled"), "value": status_counts["unprint"], "color": (0.9, 0.3, 0.2)},
            {"label": _("Klippy Close"), "value": status_counts["klippy_closed"], "color": (0.2, 0.6, 0.9)},
            {"label": _("Other"), "value": status_counts["other"], "color": (0.6, 0.6, 0.6)},
        ]
        self.drawing_area.queue_draw()
        return False

    def _update_ui_error(self, message):
        for key in self.labels: 
            self.labels[key].set_text(message)
        self.chart_data = "error"
        if hasattr(self, 'drawing_area'): 
            self.drawing_area.queue_draw()
        return False

    def _update_ui_chart_error(self):
        self.chart_data = "error"
        if hasattr(self, 'drawing_area'): 
            self.drawing_area.queue_draw()
        return False
    
    def _format_time(self, seconds_float):
        if seconds_float is None: return "N/A"
        total_seconds = int(seconds_float)
        hours, rem = divmod(total_seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{hours}h {minutes}m {seconds}s"

    def create_stat_row(self, grid, name, value, row, data_key):
        name_label=Gtk.Label(label=name); name_label.set_halign(Gtk.Align.START); name_label.get_style_context().add_class("stat-label")
        value_label=Gtk.Label(label=value); value_label.set_halign(Gtk.Align.END); value_label.get_style_context().add_class("stat-value")
        self.labels[data_key] = value_label
        if row == 0:
            name_label.set_margin_top(15)
            value_label.set_margin_top(15)
        grid.attach(name_label, 0, row, 1, 1); grid.attach(value_label, 1, row, 1, 1)

    def on_draw_chart(self, da, ctx):
        width = da.get_allocated_width()
        height = da.get_allocated_height()
        ctx.translate(width / 2-11, height / 2)
        if self.chart_data is None or self.chart_data == "error":
            radius = min(width, height) / 5
            line_width = radius * 0.6
            ctx.set_source_rgba(0.5, 0.5, 0.5, 0.5)
            ctx.set_line_width(line_width)
            ctx.arc(0, 0, radius, 0, 2 * math.pi)
            ctx.stroke()
            if self.chart_data == "error":
                 ctx.select_font_face("sans-serif", 0, 0)
                 ctx.set_font_size(14)
                 (x, y, w, h, dx, dy) = ctx.text_extents("Error")
                 ctx.move_to(-w/2, h/2)
                 ctx.show_text("Error")
            elif self.chart_data is None:
                 ctx.select_font_face("sans-serif", 0, 0)
                 ctx.set_font_size(14)
                 (x, y, w, h, dx, dy) = ctx.text_extents("Loading...")
                 ctx.move_to(-w/2, h/2)
                 ctx.show_text("Loading...")
            return
        total_value = sum(item['value'] for item in self.chart_data)
        if total_value == 0: return
        gap_angle = math.radians(4)
        num_segments = sum(1 for item in self.chart_data if item['value'] > 0)
        total_drawable_angle = 2 * math.pi - (num_segments * gap_angle) if num_segments > 1 else 2 * math.pi
        gap_angle = gap_angle if num_segments > 1 else 0
        radius = min(width, height) / 5
        line_width = radius * 0.6
        start_angle = -math.pi / 2
        ctx.set_line_cap(cairo.LineCap.BUTT)
        label_infos = []
        for item in self.chart_data:
            if item['value'] == 0: continue
            percentage = item['value'] / total_value
            angle_delta = percentage * total_drawable_angle
            end_angle = start_angle + angle_delta
            ctx.new_path()
            ctx.set_line_width(line_width)
            ctx.set_source_rgb(*item['color'])
            ctx.arc(0, 0, radius, start_angle, end_angle)
            ctx.stroke()
            label_angle = start_angle + angle_delta / 2
            layout = PangoCairo.create_layout(ctx)
            font_desc = Pango.font_description_from_string("Sans 12")
            layout.set_font_description(font_desc)
            layout.set_text(item['label'], -1)
            ink_rect, logical_rect = layout.get_pixel_extents()
            text_width, text_height = logical_rect.width, logical_rect.height
            line_start_radius = radius + line_width / 2
            line_end_radius = line_start_radius + 20
            start_x, start_y = math.cos(label_angle) * line_start_radius, math.sin(label_angle) * line_start_radius
            end_x, end_y = math.cos(label_angle) * line_end_radius, math.sin(label_angle) * line_end_radius
            is_right_side = math.cos(label_angle) > 0
            text_x = end_x + 5 if is_right_side else end_x - text_width - 5
            text_y = end_y - text_height / 2
            label_infos.append({"layout": layout, "label": item['label'], "is_right": is_right_side, "start_pos": (start_x, start_y), "end_pos": (end_x, end_y), "text_pos": [text_x, text_y], "box": [text_x, text_y, text_width, text_height], "original_y": end_y})
            start_angle = end_angle + gap_angle
        running, iteration, max_iterations = True, 0, 100
        while running and iteration < max_iterations:
            running, iteration = False, iteration + 1
            label_infos.sort(key=lambda info: info['text_pos'][1])
            for i in range(len(label_infos) - 1):
                box1, box2 = label_infos[i]['box'], label_infos[i+1]['box']
                if box1[1] < box2[1] + box2[3] and box2[1] < box1[1] + box1[3]:
                    if label_infos[i]['is_right'] != label_infos[i+1]['is_right']: continue
                    running = True
                    overlap = (box1[1] + box1[3]) - box2[1]
                    adjust = overlap / 2 + 2
                    label_infos[i]['text_pos'][1] -= adjust
                    label_infos[i]['box'][1] -= adjust
                    label_infos[i+1]['text_pos'][1] += adjust
                    label_infos[i+1]['box'][1] += adjust
        for info in label_infos:
            start_x, start_y = info['start_pos']
            end_x, original_end_y = info['end_pos']
            text_x, text_y = info['text_pos']
            new_end_y = text_y + info['box'][3] / 2
            ctx.new_path()
            ctx.set_source_rgb(0.8, 0.8, 0.8)
            ctx.set_line_width(1.5)
            ctx.move_to(start_x, start_y)
            ctx.line_to(end_x, new_end_y)
            ctx.line_to(end_x + 5 if info['is_right'] else end_x - 5, new_end_y)
            ctx.stroke()
            ctx.move_to(text_x, text_y)
            PangoCairo.show_layout(ctx, info['layout'])
            