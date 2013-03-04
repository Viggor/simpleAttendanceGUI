#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import xmlrpclib
from datetime import *
import pygtk
pygtk.require("2.0")
import gtk
import os


class simpleAttendanceGUI:

    def __init__(self):
        self.mainWindow = gtk.Window()
        self.mainWindow.set_title("Sign In/Out")
        self.mainWindow.connect("destroy", self.on_mainWindow_destroy)
        self.mainWindow.resize(480, 320)
        self.infoLabel = gtk.Label("")
        logLabel = gtk.Label("Login")
        pwdLabel = gtk.Label("Password")
        dbLabel = gtk.Label("Database name")

        self.signButton = gtk.Button("Sign!")
        self.signButton.connect("clicked", self.on_signButton_clicked)

        self.loginEntry = gtk.Entry()
        self.pwdEntry = gtk.Entry()
        self.pwdEntry.set_visibility(False)
        self.dbEntry = gtk.Entry()

        menu = gtk.Menu()
        menu_items = gtk.MenuItem("Server configuration")
        menu.append(menu_items)
        menu_items.connect("activate", self.menuitem_response, "Configuration")
        menu_items.show()

        root_menu = gtk.MenuItem("Configuration")
        root_menu.set_submenu(menu)
        root_menu.show()

        menu_bar = gtk.MenuBar()
        menu_bar.show()
        menu_bar.append(root_menu)


        if os.path.isfile("./credential"):
            with open("./credential", "r") as credential:
                data = credential.read()
                data_ar = data.split('\n')
                self.loginEntry.set_text(data_ar[0])
                self.pwdEntry.set_text(data_ar[1])
                self.dbEntry.set_text(data_ar[2])

        loghbox = gtk.HBox()
        loghbox.pack_start(logLabel)
        loghbox.pack_start(self.loginEntry)

        pwdhbox = gtk.HBox()
        pwdhbox.pack_start(pwdLabel)
        pwdhbox.pack_start(self.pwdEntry)

        dbhbox = gtk.HBox()
        dbhbox.pack_start(dbLabel)
        dbhbox.pack_start(self.dbEntry)

        vBox = gtk.VBox()
        vBox.pack_start(menu_bar)
        vBox.pack_start(self.infoLabel)
        vBox.pack_start(loghbox)
        vBox.pack_start(pwdhbox)
        vBox.pack_start(dbhbox)
        vBox.pack_start(self.signButton)

        self.mainWindow.add(vBox)
        self.mainWindow.show_all()

    def on_mainWindow_destroy(self, widget):
        gtk.main_quit()

    def on_signButton_clicked(self, widget):
        """
        Automatic sign in or sign out according to the last state of employee
        sign
        """

        userlogin = self.loginEntry.get_text()
        pwd = self.pwdEntry.get_text()
        dbname = self.dbEntry.get_text()

        #get employee information from plain text
        #:TODO increase security actually the password is not hashed
        with open("./credential", "w") as credential:
            credential.write(self.loginEntry.get_text() + '\n' + self.pwdEntry.get_text() + '\n' + self.dbEntry.get_text())

        #get server address
        try:
            with open("./server.conf", "r") as conf:
                server_address = conf.read()
        except Exception:
            warningDialog = gtk.MessageDialog(self.mainWindow,
                                              gtk.DIALOG_DESTROY_WITH_PARENT,
                                              gtk.MESSAGE_WARNING,
                                              gtk.BUTTONS_CLOSE,
                                              "Please enter server address in configuration menu")
            warningDialog.run()
            warningDialog.destroy()

        try:
            #init xmlrpc connection with the server
            sock_common = xmlrpclib.ServerProxy('http://' + server_address + '/xmlrpc/common')
            uid = sock_common.login(dbname, userlogin, pwd)
            sock = xmlrpclib.ServerProxy('http://' + server_address + '/xmlrpc/object')

            #get user id
            args = [('login', '=', userlogin)]
            user_ids = sock.execute(dbname, uid, pwd, 'res.users', 'search', args)
            user_id = user_ids[0]
        except Exception as e:
            warningConnectDialog = gtk.MessageDialog(self.mainWindow,
                                              gtk.DIALOG_DESTROY_WITH_PARENT,
                                              gtk.MESSAGE_WARNING,
                                              gtk.BUTTONS_CLOSE,
                                              "Please verify your server "
                                                     "information or your "
                                                     "network connectivity: " + str(e))
            warningConnectDialog.run()
            warningConnectDialog.destroy()
            return 0


        #get emp data
        args= [('user_id', '=', user_id)]
        emp_ids = sock.execute(dbname, uid, pwd, 'hr.employee', 'search', args)
        emp_id = emp_ids[0]
        fields = ['name']
        emp_data = sock.execute(dbname, uid, pwd, 'hr.employee', 'read',
                                       emp_id, fields)
        emp_name = emp_data['name']

        #get signs of employee
        begin_date = datetime.now().strftime('%Y-%m-%d') + ' 23:59:59'
        today = datetime.now()
        td = timedelta(days=5)
        final_dt = today - td
        end_date = final_dt.strftime('%Y-%m-%d %H:%M:%S')
        args = [
            ('name', '<', begin_date), 
            ('name', '>=', end_date), 
            ('employee_id', '=', emp_id)
            ]
        attendance_ids = sock.execute(dbname, uid, pwd, 'hr.attendance', 'search', args)

        #get the last sign of employee
        attendance_sorted_data = []
        if attendance_ids:
            fields = ['name', 'action']
            attendance_data = sock.execute(dbname, uid, pwd, 'hr.attendance', 'read', attendance_ids, fields)
            attendance_sorted_data = sorted(attendance_data, key=lambda k: k['id'])
            if attendance_sorted_data:
                last_action = attendance_sorted_data[len(attendance_sorted_data) - 1]['action']

        #sign in/out
        data = {'emp_id': emp_id, 'name': emp_name, 'id': user_id}
        if attendance_sorted_data and last_action == 'sign_in':
            data['state'] = 'absent'
            si = sock.execute(dbname, uid, pwd, 'hr.sign.in.out', 'sign_out', data)
            self.infoLabel.set_text("Outside")
            self.signButton.set_label("Sign In")
        else:
            data['state'] = 'present'
            si = sock.execute(dbname, uid, pwd, 'hr.sign.in.out', 'sign_in', data)
            self.infoLabel.set_text("At work")
            self.signButton.set_label("Sign Out")


    def menuitem_response(self, widget, string):
        self.confWindow = gtk.Window()
        self.confWindow.set_title("Server conf")
        self.confWindow.resize(240, 120)

        serverLabel = gtk.Label("Server Address:")
        serverLabel.set_size_request(100, 30)
        portLabel = gtk.Label("Server Port:")
        portLabel.set_size_request(100, 30)

        saveButton = gtk.Button("Save")
        saveButton.connect("clicked", self.on_saveButton_clicked)
        saveButton.set_size_request(80, 40)

        #TODO: add a mask for ip and port
        self.serverEntry = gtk.Entry()
        self.serverEntry.set_size_request(130, 30)
        self.portEntry = gtk.Entry()
        self.portEntry.set_size_request(80, 30)

        if os.path.isfile("./server.conf"):
            with open("./server.conf", "r") as conf:
                server_address = conf.read()
                server_tab = server_address.split(":")
                self.serverEntry.set_text(server_tab[0])
                self.portEntry.set_text(server_tab[1])

        fixed = gtk.Fixed()
        fixed.put(serverLabel, 5, 5)
        fixed.put(self.serverEntry, 110, 5)
        fixed.put(portLabel, 5, 40)
        fixed.put(self.portEntry, 110, 40)
        fixed.put(saveButton, 90, 80)

        self.confWindow.add(fixed)
        self.confWindow.show_all()

    def on_saveButton_clicked(self, widget):
        with open("./server.conf", "w") as conf:
            conf.write(
                str(self.serverEntry.get_text()) +
                ':' +
                str(self.portEntry.get_text())
            )
        self.confWindow.destroy()

if __name__ == "__main__":
    simpleAttendanceGUI()
    gtk.main()
