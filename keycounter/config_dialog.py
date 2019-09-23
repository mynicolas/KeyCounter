#-*- coding: utf-8 -*-
from win32ui import IDD_SET_TABSTOPS
from win32ui import IDC_EDIT_TABS
from win32ui import IDC_PROMPT_TABS
from win32con import IDOK
from win32con import IDCANCEL

import win32ui
import win32con

from pywin.mfc import dialog

IDC_EDIT_USERNAME = 2000
IDC_EDIT_PASSWORD = 2001


def ConfigDialogTemplate():
    style = win32con.DS_SETFONT | win32con.DS_MODALFRAME | win32con.DS_FIXEDSYS | win32con.WS_POPUP | win32con.WS_VISIBLE | win32con.WS_CAPTION | win32con.WS_SYSMENU
    cs = win32con.WS_CHILD | win32con.WS_VISIBLE
    listCs = cs | win32con.LBS_NOINTEGRALHEIGHT | win32con.WS_VSCROLL | win32con.WS_TABSTOP

    dlg = [[u'输入用户名密码', (0, 0, 200, 75), style, None, (8, "MS Sans Serif")], ]
    s = cs | win32con.CBS_DROPDOWN | win32con.WS_VSCROLL | win32con.WS_TABSTOP

    dlg.append([130, u"用户名:", -1, (30, 10, 50, 10), cs | win32con.SS_LEFT])
    dlg.append(["EDIT", "", IDC_EDIT_USERNAME, (70, 8, 100, 12), cs])

    dlg.append([130, u"密码:", -1, (30, 30, 50, 30), cs | win32con.SS_LEFT])
    dlg.append(["EDIT", "", IDC_EDIT_PASSWORD, (70, 30, 100, 12), cs])

    s = cs | win32con.WS_TABSTOP
    dlg.append([128, u"确认", win32con.IDOK, (30, 50, 50, 15), s | win32con.BS_DEFPUSHBUTTON])

    s = win32con.BS_PUSHBUTTON | s
    dlg.append([128, u"取消", win32con.IDCANCEL, (120, 50, 50, 15), s])
    return dlg


class ConfigDialog(dialog.Dialog):
    def __init__(self):
        dialog.Dialog.__init__(self, ConfigDialogTemplate())
        self.DoModal()

    def OnInitDialog(self):
        self.username_control = self.GetDlgItem(IDC_EDIT_USERNAME)
        self.password_control = self.GetDlgItem(IDC_EDIT_PASSWORD)

    def OnDestroy(self, msg):
        del self.username_control
        del self.password_control

    def OnOK(self):
        if self.username_control.GetLine() and self.password_control.GetLine():
            self.username = self.username_control.GetLine()
            self.password = self.password_control.GetLine()
            self._obj_.OnOK()
