# -*- coding: utf-8 -*-
#
# This tool installs a Fedora Live ISO (F7+) on to a USB stick, from Windows.
# For information regarding the installation of Fedora on USB drives, see
# the wiki: http://fedoraproject.org/wiki/FedoraLiveCD/USBHowTo
#
# Copyright © 2008  Red Hat, Inc. All rights reserved.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program; if
# not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth
# Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Red Hat Author(s): Luke Macken <lmacken@redhat.com>

import win32file
import win32api
import shutil
import os
import re

class LiveUSBCreator:

    iso   = None     # Fedora-8-Live-i686.iso
    drive = None     # F:\
    label = "FEDORA" # if one doesn't already exist

    def detectRemovableDrives(self):
        """
        Detect all removable drives.  If we find more than one, ask the user
        which they would like to use.
        """
        drives = []
        for drive in [l.upper() + ':' for l in 'abcdefghijklmnopqrstuvwxyz']:
            if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
                drives.append(drive)
        if not len(drives):
            raise Exception("Sorry, I couldn't find any devices")
        elif len(drives) > 1:
            drives[0] = raw_input("Which drive do you want to put Fedora on: "
                                  "%s ? " % drives)
            drives[0] = drives[0].upper()
            if not drives[0].endswith(":"):
                drives[0] += ":"
        self.drive = drives[0] + os.sep

    def verifyFilesystem(self):
        """
        Verify our filesystem type, and set the volume label if necessary
        """
        try:
            vol = win32api.GetVolumeInformation(self.drive[:-1])
        except:
            raise Exception("Make sure your USB key is plugged in and formatted"
                            " using the FAT filesystem")
        if vol[-1] not in ('FAT32', 'FAT'):
            raise Exception("Unsupported filesystem: %s\nPlease backup and "
                            "format your USB key with the FAT filesystem." %
                            vol[-1])
        if vol[0] == '':
            win32file.SetVolumeLabel(self.drive[:-1], self.label)
        else:
            self.label = vol[0]

    def findISO(self):
        """
        Look in the current directory for our ISO image.
        """
        isos = [item for item in os.listdir(".") if item.endswith(".iso")]
        if not len(isos):
            raise Exception("Cannot find ISO file.  Please drag it into this "
                            "directory.  If you haven't downloaded Fedora yet, "
                            "please visit: http://fedoraproject.org/get-fedora")
        if len(isos) > 1:
            print "I found the following ISOs:"
            for i, iso in enumerate(isos):
                print " [ %d ] %s" % (i + 1, iso)
            choice = raw_input("Which image do you want use: %s ? " %
                               range(1, i + 2))
            isos[0] = isos[int(choice) - 1]
        self.iso = isos[0]

    def extractISO(self):
        """ Extract our ISO with 7-zip directly to the USB key """
        if os.path.isdir(os.path.join(self.drive, "LiveOS")):
            print "Your device already contains a LiveOS!"
        os.system("7-Zip%s7z.exe x %s -x![BOOT] -o%s" % (os.sep, self.iso,
                                                         self.drive))
        if not os.path.isdir(os.path.join(self.drive, "LiveOS")):
            raise Exception("ISO extraction failed? Cannot find LiveOS")

    def updateConfigs(self):
        """ Generate our syslinux.cfg """
        isolinux = file(os.path.join(self.drive,"isolinux","isolinux.cfg"),'r')
        syslinux = file(os.path.join(self.drive,"isolinux","syslinux.cfg"),'w')
        for line in isolinux.readlines():
            if "CDLABEL" in line:
                line = re.sub("CDLABEL=[^ ]*", "LABEL=" + self.label, line)
                line = re.sub("rootfstype=[^ ]*", "rootfstype=vfat", line)
            syslinux.write(line)
        isolinux.close()
        syslinux.close()

    def installBootloader(self):
        print "Installing bootloader"
        syslinux = os.path.join(self.drive, "syslinux")
        if os.path.isdir(syslinux):
            shutil.rmtree(syslinux)
        shutil.move(os.path.join(self.drive, "isolinux"),
                    os.path.join(self.drive, "syslinux"))
        os.unlink(os.path.join(self.drive, "syslinux", "isolinux.cfg"))
        os.system("syslinux -d %s %s" % (os.path.join(self.drive, "syslinux"),
                                         self.drive[:-1]))

if __name__ == '__main__':
    try:
        live = LiveUSBCreator()
        live.detectRemovableDrives()
        live.verifyFilesystem()
        live.findISO()
        live.extractISO()
        live.updateConfigs()
        live.installBootloader()
    except Exception, e:
        print "Oops!  Something went wrong:"
        print str(e)

    x = raw_input("\nDone!")
