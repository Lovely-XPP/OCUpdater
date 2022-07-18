from genericpath import exists
import json
from operator import mod
import sys
import requests
import os
import time
import copy
import shutil
from datetime import datetime
from plistlib import *


class OCUpdater:
    def __init__(self):
        # Verify running os
        if not sys.platform.lower() == "darwin":
            print("")
            print(self.Colors("[Error] OpenCore Update can only be run on macOS!", fcolor='red'))
            print(self.Colors("[Info] The script is terminated.", fcolor='green'))
            print("")
            exit()
        # PATH and Constant
        ROOT = sys.path[0]
        self.ver = 'V0.0.8'
        self.path = ROOT + '/data.json'
        self.EFI_disk = ''
        self.kexts_list = [
            'OpenCorePkg',
            'AirportBrcmFixup',
            'AppleALC',
            'BT4LEContinuityFixup',
            'BrcmPatchRAM',
            'BrightnessKeys',
            'CPUFriend',
            'CpuTopologySync',
            'CpuTscSync',
            'DebugEnhancer',
            'ECEnabler',
            'FeatureUnlock',
            'HibernationFixup',
            'IntelMausi',
            'Lilu',
            'MacHyperVSupport',
            'NVMeFix',
            'NoTouchID',
            'RTCMemoryFixup',
            'RealtekRTL8111',
            'RestrictEvents',
            'UEFIGraphicsFB',
            'VirtualSMC',
            'VoodooInput',
            'VoodooPS2',
            'VoodooPS2-Alps',
            'VoodooRMI',
            'WhateverGreen'
        ]
        self.root = ''
        self.choice = ''
        self.local = {}
        self.remote = {}
        self.update_info = {}

    # set text format
    def Colors(self, text, fcolor=None, bcolor=None, style=None):
        '''
        自定义字体样式及颜色
        '''
        # 字体颜色
        fg = {
            'black': '\33[30m',  # 字体黑
            'red': '\33[31m',  # 字体红
            'green': '\33[32m',  # 字体绿
            'yellow': '\33[33m',  # 字体黄
            'blue': '\33[34m',  # 字体蓝
            'magenta': '\33[35m',  # 字体紫
            'cyan': '\33[36m',  # 字体青
            'white': '\33[37m',  # 字体白
            'end': '\33[0m'  # 默认色
        }
        # 背景颜色
        bg = {
            'black': '\33[40m',  # 背景黑
            'red': '\33[41m',  # 背景红
            'green': '\33[42m',  # 背景绿
            'yellow': '\33[43m',  # 背景黄
            'blue': '\33[44m',  # 背景蓝
            'magenta': '\33[45m',  # 背景紫
            'cyan': '\33[46m',  # 背景青
            'white': '\33[47m',  # 背景白
        }
        # 内容样式
        st = {
            'bold': '\33[1m',  # 高亮
            'url': '\33[4m',  # 下划线
            'blink': '\33[5m',  # 闪烁
            'seleted': '\33[7m',  # 反显
        }

        if fcolor in fg:
            text = fg[fcolor]+text+fg['end']
        if bcolor in bg:
            text = bg[bcolor] + text + fg['end']
        if style in st:
            text = st[style] + text + fg['end']
        return text
    

    # get file modified time
    def get_time(self, filename):
        time0 = []
        k_time = os.stat(filename).st_mtime
        k_time = datetime.utcfromtimestamp(k_time)
        k_time = k_time.timestamp()
        k_time1 = time.strftime('%Y-%m-%d', time.localtime(k_time))
        k_time2 = time.strftime('%H:%M:%S', time.localtime(k_time))
        k_time1_sp = k_time1.split('-')
        k_time2_sp = k_time2.split(':')
        for ymd in k_time1_sp:
            time0.append(ymd)
        for hms in k_time2_sp:
            time0.append(hms)
        time0.append(float(k_time))
        return time0


    # compare time
    def compare_time(self, t1, t2):
        res = 0
        if t2[-1] > t1[-1]:
            res = 1
        return res


    # get local data
    def get_local_data(self):
        local = {}
        first_time1 = 0
        first_time2 = 0

        # OpenCore
        oc = os.path.abspath(os.path.join(self.root, 'EFI/OC/OpenCore.efi'))
        oc_ver = os.popen('nvram 4D1FDA02-38C7-4A6A-9CC6-4BCCA8B30102:opencore-version').read()
        oc_ver = oc_ver.split('REL-')[-1]
        oc_ver = oc_ver[0:3]
        ver = oc_ver[0] + '.' + oc_ver[1] + '.' + oc_ver[2]
        time = self.get_time(oc)
        local['OpenCorePkg'] = {'time': time, 'version': ver}

        # kexts
        for kext in os.listdir(os.path.join(self.root, 'EFI/OC/Kexts')):
            kext0 = kext.split('.')
            kext0 = kext0[0]
            domain = os.path.abspath(os.path.join(self.root, 'EFI/OC/Kexts'))
            kext_full = os.path.join(domain, kext)

            # BrcmPatchRAM
            if kext0[0:4] == 'Brcm' or kext0 == 'BlueToolFixup':
                if first_time1 == 0:
                    plist = os.path.join(kext_full, 'Contents/Info.plist')
                    with open(plist, 'rb') as pl:
                        plist = load(pl)
                        ver = plist['CFBundleVersion']
                        pl.close()
                    time = self.get_time(kext_full)
                    local['BrcmPatchRAM'] = {'time': time, 'version': ver, 'kexts': [kext]}
                    first_time1 = 1
                    continue
                local['BrcmPatchRAM']['kexts'].append(kext)
                continue

            # VirtualSMC
            if kext0[0:3] == 'SMC' or kext0[-3:-1] == 'SMC':
                if first_time2 == 0:
                    plist = os.path.join(kext_full, 'Contents/Info.plist')
                    with open(plist, 'rb') as pl:
                        plist = load(pl)
                        ver = plist['CFBundleVersion']
                        pl.close()
                    time = self.get_time(kext_full)
                    local['VirtualSMC'] = {'time': time, 'version': ver, 'kexts': [kext]}
                    first_time2 = 1
                    continue
                local['VirtualSMC']['kexts'].append(kext)
                continue
            
            # VoodooPS2
            if kext0 == "VoodooPS2Controller":
                plist = os.path.join(kext_full, 'Contents/Info.plist')
                with open(plist, 'rb') as pl:
                    plist = load(pl)
                    ver = plist['CFBundleVersion']
                    pl.close()
                time = self.get_time(kext_full)
                local['VoodooPS2'] = {'time': time, 'version': ver, 'kexts': [kext]}
                continue
            
            # other not in kexts_list: skip
            if kext0 not in self.kexts_list:
                continue
            
            # in kexts_list: save time and kext name
            plist = os.path.join(kext_full, 'Contents/Info.plist')
            with open(plist, 'rb') as pl:
                plist = load(pl)
                ver = plist['CFBundleVersion']
                pl.close()
            time = self.get_time(kext_full)
            local[kext0] = {'time': time, 'version': ver, 'kexts': [kext]}
        return local


    # download database
    def download_database(self):
        url = 'https://raw.githubusercontent.com/dortania/build-repo/builds/config.json'
        r = requests.get(url)
        with open(self.path, 'wb') as f:
            f.write(r.content)
            f.close


    # get remote data
    def get_remote_data(self):
        remote = {}
        with open(self.path, 'r') as f:
            row_data = json.load(f)
            f.close()
        for i in self.kexts_list:
            release = {}
            debug = {}

            # get latest version
            info = row_data[i]
            info = info['versions']
            info = info[0]

            # built time
            built_time = []
            time0 = info['date_built']
            time_sp = time0.split('T')
            time1 = time_sp[0]
            time2 = time_sp[1]
            time1_sp = time1.split('-')
            time2_sp = time2.split(':') 
            for ymd in time1_sp:
                built_time.append(ymd)
            built_time.append(time2_sp[0])
            built_time.append(time2_sp[1])
            second = time2_sp[2].split('.')
            second = second[0]
            built_time.append(second)
            mtime = time1 + ' ' + time2.split('.')[0]
            mtime = time.strptime(mtime, '%Y-%m-%d %H:%M:%S')
            mtime = time.mktime(mtime)
            mtime = float(mtime)
            built_time.append(mtime)

            # version
            ver = info['version']

            # download link
            link = info['links']
            release['link'] = link['release']
            debug['link'] = link['debug']

            # sha256
            sha256 = info['hashes']
            release['sha256'] = sha256['release']['sha256']
            debug['sha256'] = sha256['debug']['sha256']
            
            remote[i] = {'time': built_time, 'version': ver, 'release': release, 'debug': debug, 'status': "Not Installed"}
        return remote


    # generate update information
    def gen_update_info(self):
        update_info = copy.deepcopy(self.remote)
        for key in update_info.keys():
            update_info[key].pop('time')
            update_info[key].pop('version')
            update_info[key]['local_time'] = None
            update_info[key]['remote_time'] = self.remote[key]['time']
            update_info[key]['local_version'] = None
            update_info[key]['remote_version'] = self.remote[key]['version']
            update_info[key]['kexts'] = [None]
        for key in self.local.keys():
            time1 = self.local[key]['time']
            time2 = self.remote[key]['time']
            res = self.compare_time(time1, time2)
            update_info[key]['local_time'] = time1
            update_info[key]['local_version'] = self.local[key]['version']
            if key != "OpenCorePkg":
                update_info[key]['kexts'] = self.local[key]['kexts']
            if res == 1:
                update_info[key]['status'] = "Update Available"
                continue
            update_info[key]['status'] = "Up-to-date"
        return update_info


    # output information
    def output_all(self):
        print(self.Colors("[Info] Time Format: UTC \n", fcolor='green'))
        for i in self.update_info.keys():
            print(i)
            cg = self.update_info[i]
            print("     [Remote Version]  " + cg['remote_version'] + ' (' + cg['remote_time'][0] +'-' + cg['remote_time'][1] + '-' + cg['remote_time'][2] + ' ' + cg['remote_time'][3] + ':' + cg['remote_time'][4] + ':' + cg['remote_time'][5] + ')')
            if cg['local_version'] != None:
                print("     [Local Version]   " + cg['local_version'] + ' (' + cg['local_time'][0] + '-' + cg['local_time'][1] + '-' + cg['local_time'][2] + ' ' + cg['local_time'][3] + ':' + cg['local_time'][4] + ':' + cg['local_time'][5] + ')')
            else:
                print("     [Local Version]   " + "None")
            if i == "OpenCorePkg":
                print("     [Status]  " + cg['status'] + '\n')
                continue
            print("     [Installed Kexts]   ")
            for kext in cg['kexts']:
                print("\t\t   " + str(kext))
            print("     [Status]  " + cg['status'] + '\n')


    # mount EFI and get EFI partition name
    def mount_EFI(self):
        out = os.popen('diskutil list').read()
        out = out.split('EFI')[1]
        out = out.split('\n')[0]
        out = out.split('disk')[1]
        self.EFI_disk = 'disk' + out.strip()
        out = os.popen('diskutil mount /dev/' + self.EFI_disk).read()
        out = out.strip()
        out = out.split('on')
        out = out[0]
        out = out.split('Volume')
        out = out[1].strip()
        EFI_root = os.path.join('/Volumes/', out)
        self.root = EFI_root

    # init
    def init(self):

        print(self.Colors('[Info] Prepareing for running...', fcolor='green'))

        # mount EFI and get EFI partition name
        self.mount_EFI()

        # judge if database file exists
        if not os.path.exists(self.path):
            print(self.Colors('[Info] Data File not Found, Downloading...', fcolor='green'))
            self.download_database()
            print(self.Colors('[Info] Downloading Done', fcolor='green'))
        print(self.Colors('[Info] Data File Found...', fcolor='green'))
        print(self.Colors('[Info] Reading Data File...', fcolor='green'))

        # get local data
        self.local = self.get_local_data()

        # get remote data
        self.remote = self.get_remote_data()

        # generate update information
        self.update_info = self.gen_update_info()

        print(self.Colors('[Info] Data File Reading Done', fcolor='green'))
        print(self.Colors('[Info] Init Done', fcolor='green'))
        os.system("clear")


    # update info output
    def output_update(self):
        first_time = 0
        print(self.Colors("[Info] Time Format: UTC \n", fcolor='green'))
        for i in self.local.keys():
            cg = self.update_info[i]
            if i == "OpenCorePkg":
                print(i + ":")
                print("   OpenCore:      \t" + cg['local_version'] + ' (' + cg['local_time'][0] +'-' + cg['local_time'][1] + '-' + cg['local_time'][2] + ' ' + cg['local_time'][3] + ':' + cg['local_time'][4] + ':' + cg['local_time'][5] + ')' + '  ->  ' + cg['remote_version'] + ' (' + cg['remote_time'][0] + '-' + cg['remote_time'][1] + '-' + cg['remote_time'][2] + ' ' + cg['remote_time'][3] + ':' + cg['remote_time'][4] + ':' + cg['remote_time'][5] + ')')
                print("")
                continue
            if first_time == 0:
                print("Kexts:")
                first_time = 1
            if len(i) < 11:
                print("   " + i + ":\t\t" + cg['local_version'] + ' (' + cg['local_time'][0] +'-' + cg['local_time'][1] + '-' + cg['local_time'][2] + ' ' + cg['local_time'][3] + ':' + cg['local_time'][4] + ':' + cg['local_time'][5] + ')' + '  ->  ' + cg['remote_version'] + ' (' + cg['remote_time'][0] + '-' + cg['remote_time'][1] + '-' + cg['remote_time'][2] + ' ' + cg['remote_time'][3] + ':' + cg['remote_time'][4] + ':' + cg['remote_time'][5] + ')')
            else: 
                print("   " + i + ":\t" + cg['local_version'] + ' (' + cg['local_time'][0] +'-' + cg['local_time'][1] + '-' + cg['local_time'][2] + ' ' + cg['local_time'][3] + ':' + cg['local_time'][4] + ':' + cg['local_time'][5] + ')' + '  ->  ' + cg['remote_version'] + ' (' + cg['remote_time'][0] + '-' + cg['remote_time'][1] + '-' + cg['remote_time'][2] + ' ' + cg['remote_time'][3] + ':' + cg['remote_time'][4] + ':' + cg['remote_time'][5] + ')')
        print("")


    # title
    def title(self, size=85):
        title_name = "OpenCore Updater"
        l = len(title_name) + len(self.ver) + 1
        title_name = title_name + ' ' + self.Colors(self.ver, fcolor='green')
        if mod(size,2) != mod(l,2):
            size = size + 1
        print("#"*size)
        space = int(size/2) - int(l/2) - 1
        print("#" + " "*space + title_name + " "*space + "#")
        print("#"*size)
        print("")


    # main interface
    def main_interface(self):
        print("Current Status:")
        if len(self.root) > 0:
            print("     EFI: " + self.Colors("mounted", fcolor='green'))
        else:
            print("     EFI: " + self.Colors("unmounted", fcolor='red'))
        if len(self.remote) > 0:
            print("     Remote Data: " + self.Colors("loaded", fcolor='green'))
        else:
            print("     Remote Data: " + self.Colors("unloaded", fcolor='red'))
        if len(self.local) > 0:
            print("     Local Data: " + self.Colors("loaded", fcolor='green'))
        else:
            print("     Local Data: " + self.Colors("unloaded", fcolor='red'))
        print("")
        print("A. Show All Kexts Information")
        print("B. Backup EFI")
        print("D. Download and Update Remote Database")
        print("S. Show Update Information")
        print("U. Update OpenCore and Kexts (Automatically Backup EFI)")
        print("")
        print("Q. Quit")
        print("")
        choice = input("Please select your option: ")
        choice = choice.upper()
        self.choice = choice


    # backup efi
    def backup_EFI(self):
        dist_root = sys.path[0]
        dist_root = os.path.abspath(os.path.join(dist_root, 'backup_EFI/'))
        if not exists(dist_root):
            os.makedirs(dist_root)
        now = time.time()
        now = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(now))
        dist = os.path.abspath(os.path.join(dist_root, now + '/EFI'))
        source_path = os.path.abspath(os.path.join(self.root, 'EFI'))
        shutil.copytree(source_path, dist)
        print(self.Colors("[Info] EFI is successfully backup to: " + dist, fcolor='green'))
        print("")
        

    # main
    def main(self):
        # init
        self.init()

        # operation
        while self.choice != 'Q':
            os.system("clear")
            self.title()
            if self.choice == 'A':
                self.output_all()
                input("Press [Enter] to back...")
                self.choice = ''
                continue

            if self.choice == 'B':
                print(self.Colors("[Info] EFI folder is backing up...", fcolor='green'))
                self.backup_EFI()
                input("Press [Enter] to back...")
                self.choice = ''
                continue

            if self.choice == 'D':
                print(self.Colors("[Info] Downloading the latest remote database...", fcolor='green'))
                self.download_database()
                print(self.Colors("[Info] Download Done", fcolor='green'))
                print(self.Colors("[Info] Updating remote data", fcolor='green'))
                self.remote = self.get_remote_data()
                print(self.Colors("[Info] Updating Done", fcolor='green'))
                input("Press [Enter] to back...")
                self.choice = ''
                continue

            if self.choice == 'S':
                self.output_update()
                input("Press [Enter] to back...")
                self.choice = ''
                continue

            if self.choice == 'U':
                print(self.Colors("[Info] EFI folder is backing up...", fcolor='green'))
                self.backup_EFI()
                print(self.Colors("[Info] EFI backing up Done", fcolor='green'))
                input("Press [Enter] to back...")
                self.choice = ''
                continue

            self.main_interface()
        
        # quit
        os.system("clear")
        self.title()
        # unmount EFI
        res = os.popen('diskutil unmount /dev/' + self.EFI_disk).read().strip()
        print(self.Colors("[Info] (EFI partition) " + res + ".", fcolor='green'))
        print(self.Colors("[Info] The script is terminated.", fcolor='green'))
        exit()


if __name__ == "__main__":
    # 实例化类
    ocup = OCUpdater()

    # run script
    ocup.main()
