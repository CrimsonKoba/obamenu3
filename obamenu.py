#!/usr/bin/env python3
"""Version 1.1.7"""

# ---- config ---
applications_dirs = ("/usr/share/applications", )
# without "pixmaps" -/usr/local/share in FreeBSD, /usr/share on linux
image_dir_base = "/usr/share"
icon_Theme = "Humanity"
image_cat_prefix = "applications-"  # if empty will create no icon text only menu
application_groups = (
    "Office",
    "Development",
    "Graphics",
    "Internet",
    "Games",
    "System",
    "Multimedia",
    "Utilities",
    "Settings")
group_aliases = {
    "Audio": "Multimedia",
    "AudioVideo": "Multimedia",
    "Network": "Internet",
    "Game": "Games",
    "Utility": "Utilities",
    "GTK": "",
    "GNOME": ""}
ignoreList = (
    "evince-previewer",
    "Ted",
    "wingide3.2",
    "python3.4",
    "feh",
    "xfce4-power-manager-settings")
terminal_string = "x-terminal-emulator -e"  # your favourites terminal exec string
simpleOBheader = False  # print full xml style OB header
# --- End of user config ---

import glob


class DtpItem(object):
    def __init__(self, fName):
        self.fileName = fName
        self.Name = ""
        self.Comment = ""
        self.Exec = ""
        self.Terminal = False
        self.Type = ""
        self.Icon = ""
        self.Categories = ()

    def add_name(self, data):
        self.Name = xescape(data)

    def add_comment(self, data):
        self.Comment = data

    def add_exec(self, data):
        if len(data) > 3 and data[-2] == '%':  # get rid of filemanager arguments in dt files
            data = data[:-2].strip()
        self.Exec = data

    def add_icon(self, data):
        self.Icon = ""
        if image_cat_prefix == "":
            return
        image_dir = image_dir_base + "/pixmaps/"
        di = data.strip()
        if len(di) < 3:
            # "Error in %s: Invalid or no icon '%s'" % (self.fileName,  di)
            return
        dix = di.find("/")      # is it a full path?
        # yes, its a path (./path or ../path or /path ...)
        if dix >= 0 and dix <= 2:
            self.Icon = di
            return
        # else a short name like "myapp"
        tmp = image_dir + di + ".*"
        tmp = glob.glob(tmp)
        if len(tmp) > 0:
            self.Icon = tmp[0]
        return

    def add_terminal(self, data):
        data = data.lower()
        if data == "true":
            self.Terminal = True

    def add_type(self, data):
        self.Type = data

    def add_categories(self, data):
        self.Categories = data


def get_cat_icon(cat):
    iconDir = image_dir_base + "/icons/" + icon_Theme + "/categories/24/"
    cat = image_cat_prefix + cat.lower()
    tmp = glob.glob(iconDir + cat + ".*")
    if len(tmp) > 0:
        return tmp[0]
    return ""


def xescape(s):
    Rep = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "'": "&apos;",
        "\"": "&quot;"}
    for p in ("&", "<", ">", "'", "\""):
        sl = len(s)
        last = -1
        while last < sl:
            i = s.find(p, last+1)
            if i < 0:
                break
            last = i
            l = s[:i]
            r = s[i+1:]
            s = l + Rep[p] + r
    return s


def process_category(
        cat,
        curCats,
        appGroups=application_groups,
        aliases=group_aliases):
        # first process aliases
    if cat in aliases:
        if aliases[cat] == "":
            return ""  # ignore this one
        cat = aliases[cat]
    if cat in appGroups and cat not in curCats:  # valid categories only and no doublettes, please
        curCats.append(cat)
        return cat
    return ""


def process_dtfile(dtf,  catDict):  # process this file & extract relevant info
    active = False  # parse only after "[Desktop Entry]" line
    fh = open(dtf,  "r")
    lines = fh.readlines()
    this = DtpItem(dtf)
    for l in lines:
        l = l.strip()
        if l == "[Desktop Entry]":
            active = True
            continue
        if active == False:  # we don't care about licenses or other comments
            continue
        if l is None or len(l) < 1 or l[0] == '#':
            continue
        if l[0] == '[' and l != "[Desktop Entry]":
            active = False
            continue
        # else
        eqi = l.split('=')
        if len(eqi) < 2:
            print("Error: Invalid .desktop line'" + l + "'")
            continue
        # Check what it is ...
        if eqi[0] == "Name":
            this.add_name(eqi[1])
        elif eqi[0] == "Comment":
            this.add_comment(eqi[1])
        elif eqi[0] == "Exec":
            this.add_exec(eqi[1])
        elif eqi[0] == "Icon":
            this.add_icon(eqi[1])
        elif eqi[0] == "Terminal":
            this.add_terminal(eqi[1])
        elif eqi[0] == "Type":
            if eqi[1] != "Application":
                continue
            this.add_type(eqi[1])
        elif eqi[0] == "Categories":
            if eqi[1][-1] == ';':
                eqi[1] = eqi[1][0:-1]
            cats = []
            # DEBUG
            dtCats = eqi[1].split(';')
            for cat in dtCats:
                result = process_category(cat,  cats)
            this.add_categories(cats)
        else:
            continue
    # add to catDict
    # this.dprint()
    if len(this.Categories) > 0:  # don't care about stuff w/o category
        for cat in this.Categories:
            catDict[cat].append(this)



def main():
    category_dict = {}

    # init the application group dict (which will contain list of apps)
    for app_group in application_groups:
        category_dict[app_group] = []

    # now let's look  into the app dirs ...
    for app_dir in applications_dirs:
        app_dir += "/*.desktop"
        dt_files = glob.glob(app_dir)

        # process each .desktop file in dir
        for dtf in dt_files:
            skipFlag = False
            for ifn in ignoreList:
                if dtf.find(ifn) >= 0:
                    skipFlag = True
            if not skipFlag:
                process_dtfile(dtf,  category_dict)

    # now, generate jwm menu include
    if simpleOBheader:
        print('<openbox_pipe_menu>')  # magic header
    else:
        print('<?xml version="1.0" encoding="UTF-8" ?>'
              '<openbox_pipe_menu xmlns="http://openbox.org/"'
              '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
              '  xsi:schemaLocation="http://openbox.org/" >')  # magic header
    appGroupLen = len(application_groups)
    for ag in range(appGroupLen):
        catList = category_dict[application_groups[ag]]
        if len(catList) < 1:
            continue                # don't create empty menus
        catStr = "<menu id=\"openbox-%s\" label=\"%s\" " % (
            application_groups[ag], application_groups[ag])
        tmp = get_cat_icon(application_groups[ag])
        if tmp != "":
            catStr += "icon=\"%s\"" % tmp
        print(catStr,  ">")
        for app in catList:
            progStr = "<item "
            progStr += "label=\"%s\" " % app.Name
            if app.Icon != "":
                progStr += "icon=\"%s\" " % app.Icon
            progStr += "><action name=\"Execute\"><command><![CDATA["
            if app.Terminal:
                progStr += terminal_string + " "
            progStr += "%s]]></command></action></item>" % app.Exec
            print(progStr)
        print("</menu>")
    print("</openbox_pipe_menu>")  # magic footer


if __name__ == '__main__':
    main()
