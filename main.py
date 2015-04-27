#!/usr/bin/env python2
# encoding: utf-8

import sys
import json
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar


class DataState(object):
    def __init__(self):
        self.values = []
        self.x_lim_left = None
        self.x_lim_right = None

    def add_value(self, name, a, b, c, d):
        if b == c:
            type_ = u'Trójkątna'
        else:
            type_ = u'Trapezoidalna'
        a = float(a)
        b = float(b)
        c = float(c)
        d = float(d)
        if a < b <= c < d:
            new_value = {
                'name': name,
                'a': a,
                'b': b,
                'c': c,
                'd': d,
                'type': type_
            }

            for value in self.values:
                if value['a'] < a < value['c'] or value['b'] < d < value['d'] \
                        or a <= value['a'] and value['d'] <= d:
                    raise ValueError()

            old_values = self.values
            self.values.append(new_value)

            for val in (a, b, c, d):
                _, _, frac_sum = self.find_fuzzy_vals(val)
                if frac_sum != 0 and abs(frac_sum - 1) > sys.float_info.epsilon:
                    self.values = old_values
                    raise ValueError()

            self.update_limits()
            
            return new_value
        raise ValueError()

    def update_limits(self):
        smallest, biggest, x_lim_left, x_lim_right = None, None, None, None
        for value in self.values:
            if smallest is None or value['a'] < smallest:
                smallest = value['a']
                x_lim_left = value['b']
            if biggest is None or biggest < value['d']:
                biggest = value['d']
                x_lim_right = value['c']
        self.x_lim_left = x_lim_left
        self.x_lim_right = x_lim_right

    def delete_value(self, index):
        del self.values[index]
        self.update_limits()

    def delete_all_values(self):
        self.values = []

    def save_to_file(self, file_path):
        json.dump(self.values, open(file_path, 'w'))

    def load_from_file(self, file_path):
        values = json.load(open(file_path))
        for value in values:
            value.pop('type', None)
            self.add_value(**value)

    def find_fuzzy_vals(self, val):
        point = None
        fuzzy_values = {}
        frac_sum = 0
        for value in self.values:
            if value['a'] < val < value['b']:
                frac = (val - value['a']) / (value['b'] - value['a'])
            elif value['b'] <= val <= value['c']:
                frac = 1
            elif value['c'] < val < value['d']:
                frac = (value['d'] - val) / (value['d'] - value['c'])
            else:
                continue
            fuzzy_values[value['name']] = frac
            point = [val, frac]
            frac_sum += frac
        return fuzzy_values, point, frac_sum


class AutoWidthListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT)
        ListCtrlAutoWidthMixin.__init__(self)


class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, u'Fuzzer')

        self.data_state = DataState()
        
        self.plot_colors = 'cornflowerblue darkslategray coral hotpink mediumorchid darkviolet lightseagreen yellowgreen turquoise palevioletred sage orangered teal crimson seagreen darksage mediumspringgreen magenta cadetblue darkturquoise dimgrey purple indigo darkslategrey mediumturquoise slategray deepskyblue lightslategray royalblue mediumvioletred mediumaquamarine salmon darkslateblue skyblue steelblue indianred darkcyan lightslategrey lightcoral slategrey dimgray lightskyblue dodgerblue forestgreen chocolate orchid darkorange mediumpurple tomato firebrick darkolivegreen rosybrown blueviolet darksalmon mediumseagreen sienna'.split(' ')

        self.panel = wx.Panel(self)
        self.figure = Figure((8.0, 4.0))
        self.figure.patch.set_facecolor('white')

        self.canvas = FigCanvas(self.panel, -1, self.figure)
        self.axes = self.figure.add_subplot(111)

        form_vbox, self.inputs = self.create_form()
        list_vbox, self.list = self.create_list()

        top_hbox = wx.BoxSizer(wx.HORIZONTAL)
        top_hbox.AddSpacer(5)
        top_hbox.Add(form_vbox)
        top_hbox.AddSpacer(5)
        top_hbox.Add(list_vbox, 1, wx.EXPAND)
        
        main_vbox = wx.BoxSizer(wx.VERTICAL)
        main_vbox.Add(top_hbox, 1, wx.EXPAND)
        main_vbox.AddSpacer(5)
        main_vbox.Add(self.canvas, 2, wx.EXPAND)
        
        self.panel.SetSizer(main_vbox)
        main_vbox.Fit(self)

        menubar = self.create_menu()
        self.SetMenuBar(menubar)

        self.refresh_plot()

    def create_form(self):
        inputs = {}
        val_input_size = (50, -1)

        form_vbox = wx.BoxSizer(wx.VERTICAL)
        form_vbox.AddSpacer(5)

        name_hbox = wx.BoxSizer(wx.HORIZONTAL)
        inputs['name'] = wx.TextCtrl(self.panel, -1)
        name_hbox.Add(wx.StaticText(self.panel, wx.ID_ANY, u'Nazwa:'), 0, wx.CENTER)
        name_hbox.Add(inputs['name'], 1, wx.EXPAND)
        form_vbox.Add(name_hbox, 1, wx.EXPAND)

        form_vbox.AddSpacer(5)

        vals_hbox = wx.BoxSizer(wx.HORIZONTAL)
        vals_hbox.AddSpacer(3)
        inputs['a'] = wx.TextCtrl(self.panel, -1, size=val_input_size)
        vals_hbox.Add(wx.StaticText(self.panel, wx.ID_ANY, u'a:'), 0, wx.CENTER)
        vals_hbox.Add(inputs['a'])
        vals_hbox.AddSpacer(10)
        inputs['b'] = wx.TextCtrl(self.panel, -1, size=val_input_size)
        vals_hbox.Add(wx.StaticText(self.panel, wx.ID_ANY, u'b:'), 0, wx.CENTER)
        vals_hbox.Add(inputs['b'])
        vals_hbox.AddSpacer(10)
        inputs['c'] = wx.TextCtrl(self.panel, -1, size=val_input_size)
        vals_hbox.Add(wx.StaticText(self.panel, wx.ID_ANY, u'c:'), 0, wx.CENTER)
        vals_hbox.Add(inputs['c'])
        vals_hbox.AddSpacer(10)
        inputs['d'] = wx.TextCtrl(self.panel, -1, size=val_input_size)
        vals_hbox.Add(wx.StaticText(self.panel, wx.ID_ANY, u'd:'), 0, wx.CENTER)
        vals_hbox.Add(inputs['d'])
        form_vbox.Add(vals_hbox)
        form_vbox.AddSpacer(3)
        add_value_button = wx.Button(self.panel, -1, u'Dodaj wartość')
        self.Bind(wx.EVT_BUTTON, self.on_add_value, add_value_button)
        form_vbox.Add(add_value_button, 0, wx.EXPAND)

        form_vbox.AddSpacer(20)

        find_fuzzy_vals_hbox = wx.BoxSizer(wx.HORIZONTAL)
        inputs['find_fuzzy_vals'] = wx.TextCtrl(self.panel, -1, size=val_input_size)
        find_fuzzy_vals_hbox.Add(wx.StaticText(self.panel, wx.ID_ANY, u'Rozmyte wartości dla:'), 0, wx.CENTER)
        find_fuzzy_vals_hbox.Add(inputs['find_fuzzy_vals'], 0, wx.EXPAND)
        form_vbox.Add(find_fuzzy_vals_hbox)
        form_vbox.AddSpacer(3)
        find_fuzzy_vals_button = wx.Button(self.panel, -1, u'Szukaj')
        self.Bind(wx.EVT_BUTTON, self.on_find_fuzzy_vals, find_fuzzy_vals_button)
        form_vbox.Add(find_fuzzy_vals_button, 0, wx.EXPAND)
        
        return form_vbox, inputs

    def create_list(self):
        list_vbox = wx.BoxSizer(wx.VERTICAL)
        list_ = AutoWidthListCtrl(self.panel)
        list_.InsertColumn(0, u'Nazwa', width=200)
        list_.InsertColumn(1, u'a', wx.LIST_FORMAT_RIGHT, width=90)
        list_.InsertColumn(2, u'b', wx.LIST_FORMAT_RIGHT, width=90)
        list_.InsertColumn(3, u'c', wx.LIST_FORMAT_RIGHT, width=90)
        list_.InsertColumn(4, u'd', wx.LIST_FORMAT_RIGHT, width=90)
        list_.InsertColumn(5, u'Typ', wx.LIST_FORMAT_RIGHT, width=140)
        list_vbox.Add(list_, 1, wx.EXPAND)
        list_delete_hbox = wx.BoxSizer(wx.HORIZONTAL)

        list_delete_selected_button = wx.Button(self.panel, -1, u'Usuń zaznaczone')
        self.Bind(wx.EVT_BUTTON, self.on_delete_selected, list_delete_selected_button)
        list_delete_hbox.Add(list_delete_selected_button, 1, wx.EXPAND)

        list_delete_all_button = wx.Button(self.panel, -1, u'Usuń wszystkie')
        self.Bind(wx.EVT_BUTTON, self.on_delete_all, list_delete_all_button)
        list_delete_hbox.Add(list_delete_all_button, 1, wx.EXPAND)

        list_vbox.Add(list_delete_hbox, 0, wx.EXPAND)
        return list_vbox, list_

    def create_menu(self):
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        self.Bind(
            wx.EVT_MENU,
            self.on_load_data,
            file_menu.Append(-1, u'&Wczytaj dane\tCtrl-O')
        )
        self.Bind(
            wx.EVT_MENU,
            self.on_save_data,
            file_menu.Append(-1, u'&Zapisz dane\tCtrl-S')
        )
        file_menu.AppendSeparator()
        self.Bind(
            wx.EVT_MENU,
            self.on_exit,
            file_menu.Append(-1, u'Za&kończ\tAlt+F4')
        )
        menubar.Append(file_menu, u'&Plik')
        return menubar

    def refresh_plot(self, draw_point=None):
        self.axes.clear()
        self.axes.set_ylim([0, 1.05])
        if self.data_state.x_lim_left is not None and self.data_state.x_lim_right is not None:
            self.axes.set_xlim([self.data_state.x_lim_left, self.data_state.x_lim_right])
        colors_count = len(self.plot_colors)
        for index, value in enumerate(self.data_state.values):
            self.axes.plot(
                [ value['a'], value['b'], value['c'], value['d'] ],
                [0, 1, 1, 0],
                self.plot_colors[index % colors_count]
            )
        if draw_point is not None:
            self.axes.plot(draw_point[0], draw_point[1], '.m', markersize=20, alpha=0.5)
        self.figure.canvas.draw()

    def open_file_dialog(self):
        openFileDialog = wx.FileDialog(
            self,
            u'Otwórz',
            '',
            '',
            u'Fuzzer JSON files (*.fuzz)|*.fuzz',
            wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )
        path = None
        if openFileDialog.ShowModal() == wx.ID_OK:
            path = openFileDialog.GetPath()
        openFileDialog.Destroy()
        return path

    def save_file_dialog(self):
        saveFileDialog = wx.FileDialog(
            self,
            u'Zapisz',
            '',
            '',
            u'Fuzzer JSON files (*.fuzz)|*.fuzz',
            wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        path = None
        if saveFileDialog.ShowModal() == wx.ID_OK:
            path = saveFileDialog.GetPath()
        saveFileDialog.Destroy()
        return path

    def on_load_data(self, event):
        file_name = self.open_file_dialog()
        if file_name:
            try:
                self.data_state.load_from_file(file_name)
            except ValueError:
                dlg = wx.MessageDialog(
                    self, 
                    u'W pliku znajdowały się błędne dane badź jedna z funkcji nakładałaby się niepoprawnie na już istniejące. Rozważ wyczyszczenie aktualnych wartości przed załadowaniem nowych z pliku.', 
                    u'Niedobrze!',
                    wx.OK | wx.ICON_EXCLAMATION
                )
                dlg.ShowModal()
                dlg.Destroy()
                return
            self.list.DeleteAllItems()
            for value in self.data_state.values:
                self.list.Append([
                    value['name'],
                    value['a'],
                    value['b'],
                    value['c'],
                    value['d'],
                    value['type']
                ])
        self.refresh_plot()

    def on_save_data(self, event):
        file_name = self.save_file_dialog()
        if file_name:
            self.data_state.save_to_file(file_name)

    def on_exit(self, event):
        self.Destroy()

    def on_add_value(self, event):
        name = self.inputs['name'].GetValue()
        a = self.inputs['a'].GetValue()
        b = self.inputs['b'].GetValue()
        c = self.inputs['c'].GetValue()
        d = self.inputs['d'].GetValue()
        try:
            new_value = self.data_state.add_value(name, a, b, c, d)
        except ValueError:
            dlg = wx.MessageDialog(
                self,
                u'Podano błędne dane lub dodawana funkcja niepoprawnie nakładałaby się na już instniejące.',
                u'Niedobrze!',
                wx.OK | wx.ICON_EXCLAMATION
            )
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.list.Append([
            new_value['name'],
            new_value['a'],
            new_value['b'],
            new_value['c'],
            new_value['d'],
            new_value['type']
        ])
        for index, input_ in self.inputs.iteritems():
            input_.Clear()
        self.refresh_plot()

    def on_delete_selected(self, event):
        while True:
            first_selected_id = self.list.GetFirstSelected()
            if first_selected_id == -1:
                break
            self.data_state.delete_value(first_selected_id)
            self.list.DeleteItem(first_selected_id)
        self.refresh_plot()

    def on_delete_all(self, event):
        self.data_state.delete_all_values()
        self.list.DeleteAllItems()
        self.refresh_plot()

    def on_find_fuzzy_vals(self, event):
        try:
            val = float(self.inputs['find_fuzzy_vals'].GetValue())
        except ValueError:
            dlg = wx.MessageDialog(
                self,
                u'Próbowano przemycić błędne dane.',
                u'Nieładnie!',
                wx.OK | wx.ICON_EXCLAMATION
            )
            dlg.ShowModal()
            dlg.Destroy()
            return
        fuzzy_values, point, _ = self.data_state.find_fuzzy_vals(val)
        text = ''
        for name, frac in fuzzy_values.iteritems():
            text += "%s: %d%%\n" % (name, frac * 100)
        if point:
            self.refresh_plot(draw_point=point)
        if len(text) == 0:
            text = u'Nie znaleziono.'
        dlg = wx.MessageDialog(
            self,
            text,
            u'Wartości rozmyte dla %s' % val,
            wx.OK | wx.ICON_INFORMATION
        )
        dlg.ShowModal()
        dlg.Destroy()


if __name__ == '__main__':
    app = wx.App(False)
    app.frame = MainFrame()
    app.frame.Show()
    app.MainLoop()
