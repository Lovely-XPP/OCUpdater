import json
import sys
import requests
import os
import time
import copy
from datetime import datetime
from plistlib import *


class OCupdate:
    def __init__(self):
        # Verify running os
        if not sys.platform.lower() == "darwin":
            print("")
            print("OpenCore Update can only be run on macOS!")
            print("The script has been terminated.")
            print("")
            exit()
        # PATH and Constant
        ROOT = sys.path[0]
        self.ver = '0.0.5'
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
        self.mode = "main"
        self.efi_status = 0
        self.database = 0
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
    def get_time(self, file):
        time0 = []
        k_time = os.stat(file).st_mtime
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

        print('[Info] 正在初始化程序...')

        # mount EFI and get EFI partition name
        self.mount_EFI()

        # judge if database file exists
        if not os.path.exists(self.path):
            print('[Info] 未发现数据文件，正在下载...')
            self.download_database()
            print('[Info] 数据文件下载完成')
        print('[Info] 发现数据文件')
        print('[Info] 正在处理数据文件')

        # get local data
        self.local = self.get_local_data()

        # get remote data
        self.remote = self.get_remote_data()

        # generate update information
        self.update_info = self.gen_update_info()

        print('[Info] 数据文件处理完成')
        print('[Info] 初始化完成')
        os.system("clear")

    def output_update(self):
        first_time = 0
        for i in self.local.keys():
            cg = self.update_info[i]
            if i == "OpenCorePkg":
                print(i + ":")
                print("   OpenCore:      \t" + cg['local_version'] + ' (' + cg['local_time'][0] +'-' + cg['local_time'][1] + '-' + cg['local_time'][2] + ' ' + cg['local_time'][3] + ':' + cg['local_time'][4] + ':' + cg['local_time'][5] + ')' + '  ->  ' + cg['remote_version'] + ' (' + cg['remote_time'][0] + '-' + cg['remote_time'][1] + '-' + cg['remote_time'][2] + ' ' + cg['remote_time'][3] + ':' + cg['remote_time'][4] + ':' + cg['remote_time'][5] + ')')
                continue
            if first_time == 0:
                print("Kexts:")
                first_time = 1
            if len(i) < 11:
                print("   " + i + ":\t\t" + cg['local_version'] + ' (' + cg['local_time'][0] +'-' + cg['local_time'][1] + '-' + cg['local_time'][2] + ' ' + cg['local_time'][3] + ':' + cg['local_time'][4] + ':' + cg['local_time'][5] + ')' + '  ->  ' + cg['remote_version'] + ' (' + cg['remote_time'][0] + '-' + cg['remote_time'][1] + '-' + cg['remote_time'][2] + ' ' + cg['remote_time'][3] + ':' + cg['remote_time'][4] + ':' + cg['remote_time'][5] + ')')
            else: 
                print("   " + i + ":\t" + cg['local_version'] + ' (' + cg['local_time'][0] +'-' + cg['local_time'][1] + '-' + cg['local_time'][2] + ' ' + cg['local_time'][3] + ':' + cg['local_time'][4] + ':' + cg['local_time'][5] + ')' + '  ->  ' + cg['remote_version'] + ' (' + cg['remote_time'][0] + '-' + cg['remote_time'][1] + '-' + cg['remote_time'][2] + ' ' + cg['remote_time'][3] + ':' + cg['remote_time'][4] + ':' + cg['remote_time'][5] + ')')


    # title
    def title(self):
        print("#"*61)
        print("#" + " "*22 + "OpenCore Update" + " "*22 + "#")
        print("#"*61)
        print("")

    # main interface
    def main_interface(self):
        print("Current Status:")
        print("     Script version: " + self.ver)
        print("     Show Time format: UTC")
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

    # main
    def main(self):
        # init
        self.init()

        # operation
        while self.choice != 'Q' or self.mode != "main":
            os.system("clear")
            self.title()
            if self.choice == 'A':
                self.mode = 'all'
                self.output_all()
                input("Press [Enter] to back...")
                self.choice = ''
                self.mode = 'main'
                continue
            self.main_interface()


if __name__ == "__main__":
    # 实例化类
    ocup = OCupdate()

    
    # show main menu
    ocup.main()

    # unmount EFI
    # os.system('diskutil unmount /dev/' + EFI_disk)
