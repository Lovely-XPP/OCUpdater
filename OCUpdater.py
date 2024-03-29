import json
import sys, tty, termios 
import requests
import os
import time
import copy
import shutil
import zipfile
from datetime import datetime
from plistlib import *


class OCUpdater:
    def __init__(self):
        # Verify running os
        if not sys.platform.lower() == "darwin":
            print("")
            print(self.Colors("[Error] OpenCore Update can only run on macOS!", fcolor='red'))
            print(self.Colors("[Info] The script is terminated.", fcolor='green'))
            print("")
            exit()
        # PATH and Constant
        ROOT = sys.path[0]
        self.ver = 'V1.35'
        self.path = ROOT + '/data.json'
        self.mode = 0
        self.EFI_disk = ''
        self.url = 'https://raw.githubusercontent.com/dortania/build-repo/builds/config.json'
        self.bootloader = ""
        self.kexts_list = []
        self.password = ""
        self.network = False
        self.type = 'Release'
        self.change = {'Release': 'Debug', 'Debug': 'Release'}
        self.root = ''
        self.choice = ''
        self.local = {}
        self.remote = {}
        self.update_info = {}
        self.install = 0
        self.update = [0, 0]


    # set text format
    def Colors(self, text, fcolor=None, bcolor=None, style=None):
        '''
        User-Defined print text format
        '''
        # Font Color
        fg = {
            'black': '\33[30m',
            'red': '\33[31m',
            'green': '\33[32m',
            'yellow': '\33[33m',
            'blue': '\33[34m',
            'magenta': '\33[35m',
            'cyan': '\33[36m',
            'white': '\33[37m',
            'end': '\33[0m'
        }
        # Background Color
        bg = {
            'black': '\33[40m',
            'red': '\33[41m',
            'green': '\33[42m',
            'yellow': '\33[43m',
            'blue': '\33[44m',
            'magenta': '\33[45m',
            'cyan': '\33[46m',
            'white': '\33[47m',
        }
        # 
        st = {
            'bold': '\33[1m', # Highlight
            'url': '\33[4m',  # Underline
            'blink': '\33[5m',
            'selected': '\33[7m',
        }

        if fcolor in fg:
            text = fg[fcolor]+text+fg['end']
        if bcolor in bg:
            text = bg[bcolor] + text + fg['end']
        if style in st:
            text = st[style] + text + fg['end']
        return text


    # get input
    def getch(self):
        fd = sys.stdin.fileno() 
        old_settings = termios.tcgetattr(fd) 
        try: 
            tty.setraw(sys.stdin.fileno()) 
            ch = sys.stdin.read(1) 
        finally: 
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings) 
        return ch 


    # password hide
    def getpass(self): 
        password = "" 
        nums = 0
        max_nums = 0
        while True: 
            ch = self.getch() 
            if ch == "\r" or ch == "\n": 
                return password 
            elif ch == "\b" or ord(ch) == 127: 
                if nums > 0: 
                    nums -= 1
                    password = password[:-1] 
                    # clean and rewrite * num
                    print("\r" + " "*max_nums + "\n\033[A" + "*"*nums, end="", flush=True)
            else: 
                nums += 1
                if nums > max_nums:
                    max_nums = nums
                password += ch
                print("\r" + "*"*nums, end="", flush=True)


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
        if t2[-1] - t1[-1] > 600:
            res = 1
        return res


    # get local data
    def get_local_data(self):
        local = {}

        # OpenCore info
        if self.mode == 1:
            ver = 'Unknown'
        else:
            oc_ver = os.popen('nvram 4D1FDA02-38C7-4A6A-9CC6-4BCCA8B30102:opencore-version').read()
            oc_ver = oc_ver.split('REL-')[-1]
            oc_ver = oc_ver[0:3]
            ver = oc_ver[0] + '.' + oc_ver[1] + '.' + oc_ver[2]
        oc = os.path.abspath(os.path.join(self.root, 'OpenCore.efi'))
        time = self.get_time(oc)
        local[self.bootloader] = {'time': time, 'version': ver}

        # kexts info
        for kext in os.listdir(os.path.join(self.root, 'Kexts')):
            kext0 = kext.split('.')
            kext0 = kext0[0]
            domain = os.path.abspath(os.path.join(self.root, 'Kexts'))
            kext_full = os.path.join(domain, kext)

            # IntelBluetoothFirmware
            if kext0[0:14].lower() == 'intelbluetooth' or kext0.lower() == 'intelbtpatcher':
                try:
                    local['IntelBluetoothFirmware']['kexts'].append(kext)
                except:
                    plist_name = os.path.join(kext_full, 'Contents/Info.plist')
                    with open(plist_name, 'rb') as pl:
                        plist = load(pl)
                        ver = plist['CFBundleVersion']
                        pl.close()
                    time = self.get_time(plist_name)
                    local['IntelBluetoothFirmware'] = {'time': time, 'version': ver, 'kexts': [kext]}
                continue


            # BrcmPatchRAM
            if kext0[0:4].lower() == 'brcm' or kext0.lower() == 'bluetoolfixup':
                try:
                    local['BrcmPatchRAM']['kexts'].append(kext)
                except:
                    plist_name = os.path.join(kext_full, 'Contents/Info.plist')
                    with open(plist_name, 'rb') as pl:
                        plist = load(pl)
                        ver = plist['CFBundleVersion']
                        pl.close()
                    time = self.get_time(plist_name)
                    local['BrcmPatchRAM'] = {'time': time, 'version': ver, 'kexts': [kext]}
                continue

            # VirtualSMC
            if kext0[0:3].upper() == 'SMC' or kext0.upper() == 'VIRTUALSMC':
                try: 
                    local['VirtualSMC']['kexts'].append(kext)
                    if kext0.upper() == 'VIRTUALSMC':
                        plist_name = os.path.join(kext_full, 'Contents/Info.plist')
                        with open(plist_name, 'rb') as pl:
                            plist = load(pl)
                            ver = plist['CFBundleVersion']
                            pl.close()
                        time = self.get_time(plist_name)
                        local['VirtualSMC']['time'] = time
                        local['VirtualSMC']['version'] = ver
                except:
                    plist_name = os.path.join(kext_full, 'Contents/Info.plist')
                    with open(plist_name, 'rb') as pl:
                        plist = load(pl)
                        ver = plist['CFBundleVersion']
                        pl.close()
                    time = self.get_time(plist_name)
                    local['VirtualSMC'] = {'time': time, 'version': ver, 'kexts': [kext]}
                continue
            
            # VoodooPS2
            if kext0 == "VoodooPS2Controller":
                plist_name = os.path.join(kext_full, 'Contents/Info.plist')
                with open(plist_name, 'rb') as pl:
                    plist = load(pl)
                    ver = plist['CFBundleVersion']
                    pl.close()
                time = self.get_time(plist_name)
                local['VoodooPS2'] = {'time': time, 'version': ver, 'kexts': [kext]}
                continue
            
            # other not in kexts_list: skip
            if kext0 not in self.kexts_list:
                continue
            
            # in kexts_list: save time and kext name
            plist_name = os.path.join(kext_full, 'Contents/Info.plist')
            with open(plist_name, 'rb') as pl:
                plist = load(pl)
                ver = plist['CFBundleVersion']
                pl.close()
            time = self.get_time(plist_name)
            local[kext0] = {'time': time, 'version': ver, 'kexts': [kext]}
        return local


    # download database
    def download_database(self):
        r = requests.get(self.url)
        with open(self.path, 'wb') as f:
            f.write(r.content)
            f.close


    # get kexts list
    def get_kexts_list(self):
        with open(self.path, 'r') as f:
            row_data = json.load(f)
            f.close()
        for key in row_data.keys():
            try:
                if row_data[key]['type'].lower() == "bootloader":
                    self.bootloader = key
                if row_data[key]['type'].lower() == "kext":
                    self.kexts_list.append(key)
            except:
                continue


    # get remote data
    def get_remote_data(self):
        remote = {}
        with open(self.path, 'r') as f:
            row_data = json.load(f)
            f.close()
        list = self.kexts_list.copy()
        list.append(self.bootloader)
        for i in list:
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
        update = [0, 0]
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
            if key != self.bootloader:
                update_info[key]['kexts'] = self.local[key]['kexts']
            if res == 1:
                if key == self.bootloader:
                    update[0] = 1
                else:
                    update[1] = update[1] + 1
                update_info[key]['status'] = "Update Available"
                continue
            update_info[key]['status'] = "Up-to-date"
        self.update = update
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
            if i == self.bootloader:
                print("     [Status]  " + cg['status'] + '\n')
                continue
            print("     [Installed Kexts]   ")
            for kext in cg['kexts']:
                print("\t\t   " + str(kext))
            print("     [Status]  " + cg['status'] + '\n')


    # mount EFI and get EFI partition name
    def mount_EFI(self):
        # get list of EFI disks
        EFI_disks = []
        out = os.popen('diskutil list').read()
        out = out.split('EFI')
        out.pop(0)
        for strings in out:
            string = strings.strip()
            if len(string) < 3:
                continue
            string = strings.split('\n', 1)
            string = string[0]
            string = string.split('disk')
            string = string[1]
            string = 'disk' + string.strip()
            EFI_disks.append(string)
        self.title()
        # get pwd to mount EFI
        print("Please Input your Password to mount EFI: ")
        self.password = self.getpass()
        test = os.popen('echo ' + self.password + ' | sudo -S echo 2').read()
        test = test.strip()
        if test != "2":
            os.system("clear")
            self.title()
            print(self.Colors('[Error] Wrong Password', fcolor='red'))
            print(self.Colors("[Info] The script is terminated.", fcolor='green'))
            print("")
            exit()
        os.system("clear")
        OC_disks = []
        OC_roots = []
        # check OC folder in all EFI partitions
        for EFI_disk in EFI_disks:
            out = os.popen('echo ' + self.password + ' | sudo -S diskutil mount /dev/' + EFI_disk).read()
            out = out.strip()
            out = out.split('on')
            out = out[0]
            out = out.split('Volume')
            out = out[1].strip()
            EFI_root = os.path.join('/Volumes/', out)
            # checkout OC Path
            # get efi name
            efi_name = 'EFI'
            oc_name = 'OC'
            source_path = os.path.abspath(os.path.join(EFI_root, efi_name))
            if not os.path.exists(source_path):
                efi_name = efi_name.lower()
                source_path = os.path.abspath(os.path.join(EFI_root, efi_name))
            source_path = os.path.abspath(os.path.join(source_path, oc_name))
            if not os.path.exists(source_path):
                oc_name = oc_name.lower()
                source_path = os.path.abspath(os.path.join(EFI_root, oc_name))
            # if not exist, unmount EFI and try next one
            if not os.path.exists(source_path):
                os.system('echo ' + self.password + ' | sudo -S diskutil unmount force /dev/' + EFI_disk + ' >> /dev/null')
                continue
            OC_disks.append(EFI_disk)
            OC_roots.append(source_path)
            os.system('echo ' + self.password + ' | sudo -S diskutil unmount force /dev/' + EFI_disk + ' >> /dev/null')
        # if no detect EFI 
        if len(OC_disks) == 0:
            self.title()
            print(self.Colors('[Error] Not OpenCore Detected, please check EFI partition', fcolor='red'))
            print(self.Colors("[Info] The script is terminated.", fcolor='green'))
            print("")
            exit()
        # if detect EFI partition > 1, let user choose the right one
        if len(OC_disks) == 1:
            self.root = OC_roots[0]
            self.EFI_disk = OC_disks[0]
        else:
            choose = -1
            while(True):
                count = 0
                self.title()
                print(self.Colors("[Warn] Detect More than 1 EFI Partition with OC Folder, Please choose one!"))
                for OC_disk in OC_disks:
                    count += 1
                    res = os.popen('diskutil list /dev/' + OC_disk).read()
                    out = res.split('\n', 1)
                    print(str(count) + '. ' + self.Colors(out[0], fcolor='green'))
                    print(out[1])
                print(self.Colors("0. exit\n", fcolor="green"))
                choose = input("Please input 0 ~ " + str(len(OC_disks)) + " :")
                try:
                    choose = int(choose)
                    if (choose < 0 and choose > len(OC_disks)):
                        print(self.Colors('\n[Error] Input Error, Please input 0 ~ ' + str(len(OC_disks)), fcolor='red'))
                        time.sleep(3)
                        continue
                    break
                except:
                    print(self.Colors('\n[Error] Input Error, Please input 0 ~ ' + str(len(OC_disks)), fcolor='red'))
                    time.sleep(3)
                    continue
            if choose == 0:
                os.system("clear")
                self.title()
                print(self.Colors("[Info] The script is terminated.", fcolor='green'))
                print("")
                print("Have a nice day ~")
                exit()
            # get the choose EFI and unmount others
            self.EFI_disk = OC_disks[choose-1]
            self.root = OC_roots[choose-1]
        os.system('echo ' + self.password + ' | sudo -S diskutil mount /dev/' + self.EFI_disk + ' >> /dev/null')



    # check network
    def check_network(self):
        try:
            res = requests.get(self.url, timeout=5)
            self.network = res.ok
        except:
            self.network = False


    # init
    def init(self):
        # input mode
        while True:
            try:
                os.system("clear")
                self.title()
                user_name = os.getlogin()
                print(self.Colors("Welcome User [" + user_name + "] to Use OpenCoreUpdate ~\n", fcolor='green'))
                print("0. " + self.Colors("EFI Mode", fcolor="blue") + " (Automatically mount EFI)")
                print("1. " + self.Colors("Local Mode", fcolor="blue") + " (Manually Specify OpenCore Folder)\n")
                choose = input("Please choose running mode: ")
                choose = int(choose)
                if (choose == 0 or choose == 1):
                    break
                print(self.Colors('\n[Error] Input Error, Please input 0 or 1 ...', fcolor='red'))
                time.sleep(3)
            except:
                print(self.Colors('\n[Error] Input Error, Please input 0 or 1 ...', fcolor='red'))
                time.sleep(3)
                continue
        self.mode = choose
        # get EFI path, 0: EFI, 1: Local
        if choose == 1:
            while True:
                try:
                    os.system('clear')
                    self.title()
                    print(self.Colors("Local Mode", fcolor="blue") +
                          "\n [Input Example]\n     /user/Desktop/EFI/OC]\n     ./EFI/OC\n     ../EFI/OC\n")
                    oc_folder = input("Please Input Local OpenCore EFI Folder: ")
                    if oc_folder[0] == '.':
                        oc_folder = os.path.abspath(os.path.join(sys.path[0], oc_folder))
                    if not os.path.exists(oc_folder):
                        print(self.Colors(
                            '\n[Error] Input Directory Not Exists, Please Retry ...', fcolor='red'))
                        time.sleep(3)
                        continue
                    break
                except:
                    print(self.Colors(
                        '\n[Error] Input Directory Not Exists, Please Retry ...', fcolor='red'))
                    time.sleep(3)
                    continue
            self.root = oc_folder
        else:
            self.mount_EFI()

        # print title
        os.system('clear')
        self.title()
        print(self.Colors('[Info] Preparing for running...', fcolor='green'))

        # check network
        self.check_network()

        # judge if database file exists
        if not os.path.exists(self.path):
            print(self.Colors('[Info] Data File not Found, Downloading...', fcolor='green'))
            if not self.network:
                print(self.Colors('[Error] Network error, please check your connection to ' + self.url , fcolor='red'))
                print(self.Colors("[Info] The script is terminated.", fcolor='green'))
                print("")
                exit()
            self.download_database()
            print(self.Colors('[Info] Downloading Done', fcolor='green'))
        else:
            if self.network:
                print(self.Colors('[Info] Data File is Updating...', fcolor='green'))
                self.download_database()
                print(self.Colors('[Info] Updating Done', fcolor='green'))
        print(self.Colors('[Info] Data File Found...', fcolor='green'))
        print(self.Colors('[Info] Reading Data File...', fcolor='green'))

        # get kexts list
        self.get_kexts_list()

        # get local data
        try:
            self.local = self.get_local_data()
            self.install = len(self.local.keys())
        except:
            print(self.Colors('[Error] OpenCore Folder Structure is not complete, please check EFI partition', fcolor='red'))
            print(self.Colors("[Info] The script is terminated.", fcolor='green'))
            print("")
            exit()
        
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
        if self.update[0] + self.update[1] == 0:
            print(self.Colors("[Info] OpenCore Pkg and All Installed Kexts are up-to-date.", fcolor='green'))
            return
        print(self.Colors("[Info] Time Format: UTC \n", fcolor='green'))
        for i in self.local.keys():
            cg = self.update_info[i]
            if cg['status'] == "Update Available":
                if i == self.bootloader:
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


    # title
    def title(self, size=85):
        title_name = "OpenCore Updater"
        l = len(title_name) + len(self.ver) + 1
        title_name = title_name + ' ' + self.Colors(self.ver, fcolor='green')
        if (size % 2) != (l % 2):
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
            if self.mode == 0:
                print("     EFI: " + self.Colors("mounted [" + self.EFI_disk + "]", fcolor='green'))
            else:
                print("     EFI: " + self.Colors("Local Folder [" + self.root + "]", fcolor='green'))
        else:
            print("     EFI: " + self.Colors("unmounted", fcolor='red'))
        if self.mode == 1:
            print("     OpenCore: " + self.Colors("Detected, ", fcolor='green') +
                  self.Colors("Unknow Version", fcolor='yellow') + self.Colors(" [Local Mode]", fcolor='blue'))
        else:
            if not self.update[0]:
                print("     OpenCore: " + self.Colors("Detected, " + self.local[self.bootloader]['version'] + " [Up-to-date]", fcolor='green'))
            else:
                print("     OpenCore: " + self.Colors("Detected, " + self.local[self.bootloader]['version'], fcolor='green') + self.Colors(" [Update Available]", fcolor='yellow'))
        if not self.update[1]:
            print("     Kexts: " + self.Colors("Up-to-date", fcolor='green'))
        else:
            print("     Kexts: " + self.Colors(str(self.update[1]) + " Update Available", fcolor='yellow'))
        if self.network:
            print("     Network: " + self.Colors("Online", fcolor='green'))
        else:
            print("     Network: " + self.Colors("Offline", fcolor='red'))
        if len(self.remote) > 0:
            print("     Remote Data: " + self.Colors("loaded", fcolor='green'))
        else:
            print("     Remote Data: " + self.Colors("unloaded", fcolor='red'))
        if len(self.local) > 0:
            print("     Local Data: " + self.Colors("loaded", fcolor='green'))
        else:
            print("     Local Data: " + self.Colors("unloaded", fcolor='red'))
        print("     Update Type: " + self.Colors(self.type, fcolor='green'))
        print("")
        print("A. Show All Kexts Information")
        print("B. Backup EFI")
        print("C. Change Update Type to " + self.Colors(self.change[self.type], fcolor='yellow'))
        print("D. Download and Update Remote Database")
        print("L. Reload Data")
        print("R. Refresh Network Status")
        print("S. Show Update Information")
        print("UO. Update OpenCore (Automatically Backup EFI)")
        print("UK. Update Kexts (Automatically Backup EFI)")
        print("")
        print("Q. Quit")
        print("")
        choice = input("Please select your option: ")
        choice = choice.upper()
        self.choice = choice


    # backup EFI
    def backup_EFI(self):
        dist_root = sys.path[0]
        dist_root = os.path.abspath(os.path.join(dist_root, 'backup_EFI/'))
        if not os.path.exists(dist_root):
            os.makedirs(dist_root)
        now = time.time()
        now = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(now))
        dist = os.path.abspath(os.path.join(dist_root, now + '.zip'))
        zip = zipfile.ZipFile(dist,"w",zipfile.ZIP_DEFLATED)
        tmp_path = os.path.abspath(os.path.join(self.root, '..'))
        efi_path = os.path.abspath(os.path.join(self.root, '../..'))
        efi_name = tmp_path[len(efi_path):-1] + tmp_path[-1]
        efi_name = efi_name.replace('/', '')
        str_count = len(efi_name) + 1
        for path,dirnames,filenames in os.walk(efi_path):
            fpath = path.replace(efi_path,'')
            if fpath[0:str_count] != ("/" + efi_name):
                continue
            for filename in filenames:
                source_file = os.path.join(fpath,filename)
                if source_file[0:str_count] != ("/" + efi_name):
                    continue
                zip.write(os.path.join(path, filename), source_file)
        zip.close()
        print(self.Colors("[Info] EFI is successfully backup to: " + dist, fcolor='green'))
    

    # update config
    def update_oc_config(self, update_config, source_config, save_config):
        del_keys = []
        del_platform_info = []
        update_info = []

        # read update plist
        with open(update_config, 'rb') as pl:
            custom_plist = load(pl)
            up_plist = copy.deepcopy(custom_plist)
        # read source plist
        with open(source_config, 'rb') as pl:
            source_plist = load(pl)
            src_plist = copy.deepcopy(source_plist)

        # clean warning section
        for key in up_plist.keys():
            if key[0] == '#':
                del_keys.append(key)
                continue
        for del_key in del_keys:
            up_plist.pop(del_key)

        for key in up_plist.keys():
            # deviceproperties
            if key.lower() == "deviceproperties":
                up_plist[key] = src_plist[key]
                continue
            for key2 in up_plist[key].keys():
                # platforminfo
                if key.lower() == "platforminfo":
                    if key2 in src_plist[key].keys():
                        up_plist[key][key2] = src_plist[key][key2]
                        continue
                    del_platform_info.append(key2)
                    continue
                # nvram
                if key.lower() == "nvram":
                    if key2 in src_plist[key].keys():
                        up_plist[key][key2] = src_plist[key][key2]
                        continue
                # others entry
                # list copy directly
                if isinstance(up_plist[key][key2], list):
                    try:
                        # if list contains dict, check if some keys are missing
                        if isinstance(up_plist[key][key2][0], dict):
                            add = []
                            example = up_plist[key][key2][0]
                            up_plist[key][key2] = src_plist[key][key2]
                            for entry in up_plist[key][key2]:
                                for key3 in example.keys():
                                    if key3.lower() == "loadearly":
                                        entry[key3] = False
                                    if key3 not in entry.keys():
                                        add.append(key3)
                                        entry[key3] = example[key3]
                            add = list(set(add))
                            if len(add) > 0:
                                for key3 in add:
                                    info = "[Config: Add Entry] " + str(key) + "->" + str(key2) + "->" + str(key3) + ":  " 
                                    info = info + str(example[key3])
                                    update_info.append(info)
                            continue
                        up_plist[key][key2] = src_plist[key][key2]
                    except IndexError:
                        up_plist[key][key2] = src_plist[key][key2]
                # dict copy 
                if isinstance(up_plist[key][key2], dict):
                    keys = src_plist[key][key2].keys()
                    keys_up = up_plist[key][key2].keys()
                    # check delete entry
                    for key3 in keys:
                        if key3 not in keys_up:
                            info = "[Config: Delete Entry] " + str(key) + "->" + str(key2) + "->" + str(key3) + ":  " 
                            info = info + str(src_plist[key][key2][key3])
                            update_info.append(info)
                    for key3 in keys_up:
                        # if add entry, keep the default key-value 
                        if key3 not in keys:
                            info = "[Config: Add Entry] " + str(key) + "->" + str(key2) + "->" + str(key3) + ":  " 
                            info = info + str(up_plist[key][key2][key3])
                            update_info.append(info)
                            continue
                        # if change entry type, keep the default key-value
                        if type(up_plist[key][key2][key3]) != type(src_plist[key][key2][key3]):
                            info = "[Config: Change Entry] " + str(key) + "->" + str(key2) + "->" + str(key3) + ":  " 
                            info = info + str(src_plist[key][key2][key3]) + " -> " +str(up_plist[key][key2][key3])
                            info = self.Colors(info, fcolor="yellow")
                            update_info.append(info)
                            continue
                        up_plist[key][key2][key3] = src_plist[key][key2][key3]
                    continue
                # other type
                # if change entry type, keep the default key-value
                if type(up_plist[key][key2]) != type(src_plist[key][key2]):
                    info = "[Config: Change Entry] " + str(key) + "->" + str(key2) + ":  " 
                    info = info + str(src_plist[key][key2]) + " -> " +str(up_plist[key][key2])
                    info = self.Colors(info, fcolor="yellow")
                    update_info.append(info)
                    continue
                up_plist[key][key2] = src_plist[key][key2]
                
        # delete no need platform information
        for platform_info in del_platform_info:
            up_plist["PlatformInfo"].pop(platform_info)

        # save new config
        with open(save_config, 'wb') as new_plist:
            dump(up_plist, new_plist, fmt=FMT_XML,
                 sort_keys=True, skipkeys=False)

        # display config update info
        for info in update_info:
            print(info)


    # update OpenCore interface
    def update_oc_interface(self, kext, progress):
        os.system('clear')
        self.title()
        print(self.Colors("- Update OpenCorePkg Done", fcolor='green'))
        print("> Update Kexts Package")
        print("")
        progress1 = progress[0] + 1
        progress2 = progress[1]
        ratio = float(progress1*4 + progress2 - 4)/self.install/4
        sym_nums = 60
        sym_progress = int(sym_nums*ratio)
        space = sym_nums - sym_progress
        print("[" + str(progress1-1) +"/" + str(self.install) + "]  " + str(round(ratio*100,2)) + " %  [" + "="*sym_progress + " "*space + "]")
        print("")
        print("Updating Kext Package: " + self.Colors(kext, fcolor='yellow') + "\n" + "These kext(s) will be update: ")
        for k in self.update_info[kext]['kexts']:
            print(self.Colors("\t" + k, fcolor='yellow'))
        print("")
        if progress2 >= 0:
            print(self.Colors("[Info] Downloading Kext Package: " + kext, fcolor='green'))
        if progress2 >= 1:
            print(self.Colors("[Info] Download Kext Package: " + kext + " Done", fcolor='green'))
            print(self.Colors("[Info] Extracting Kext Package: " + kext, fcolor='green'))
        if progress2 >= 2:
            print(self.Colors("[Info] Extract Kext Package: " + kext + " Done", fcolor='green'))
            print(self.Colors("[Info] Updating Kext Package: " + kext, fcolor='green'))
        if progress2 >= 3:
            print(self.Colors("[Info] Update Kext Package: " + kext + " Done", fcolor='green'))
            print(self.Colors("[Info] Cleaning Cache: " + kext, fcolor='green'))
        if progress2 >= 4:
            print(self.Colors("[Info] Clean Cache: " + kext + " Done", fcolor='green'))


    # update OpenCore
    def update_OpenCore(self):
        oc = self.update_info[self.bootloader]
        tmp_root = sys.path[0]
        tmp_path = os.path.abspath(os.path.join(tmp_root, 'cache/'))
        if not os.path.exists(tmp_path):
            os.mkdir(tmp_path)
        tmp = os.path.abspath(os.path.join(tmp_path, 'OpenCorePkg.zip'))
        update_type = self.type
        update_type = update_type.lower()

        # download
        print(self.Colors("[Info] Downloading OpenCorePkg...", fcolor='green'))
        headers = {"Auth": "{abcd}", "accept": "*/*", "accept-encoding": "gzip;deflate;br"}
        response = requests.request("GET", oc[update_type]['link'], headers = headers)
        with open(tmp, "wb") as f:
            f.write(response.content)
        print(self.Colors("[Info] Download Done", fcolor='green'))

        # extract zip
        print(self.Colors("[Info] Extract OpenCorePkg...", fcolor='green'))
        tmp_path = os.path.abspath(os.path.join(tmp_path, 'OpenCorePkg/'))
        ys = zipfile.ZipFile(tmp)
        ys.extractall(tmp_path)
        ys.close()
        os.remove(tmp)
        print(self.Colors("[Info] Extract Done", fcolor='green'))

        # OpenCore.efi update
        print(self.Colors("[Info] Updating OpenCorePkg Core...", fcolor='green'))
        oc_efi_source = os.path.abspath(os.path.join(self.root, 'OpenCore.efi'))
        oc_efi_update = os.path.abspath(os.path.join(tmp_path, 'X64/EFI/OC/OpenCore.efi'))
        shutil.copy(oc_efi_update, oc_efi_source)
        print(self.Colors("[Info] Update Core Done", fcolor='green'))

        # Drivers update
        print(self.Colors("[Info] Updating OpenCorePkg Drivers...", fcolor='green'))
        drivers = []
        oc_drivers_source = os.path.abspath(os.path.join(self.root, 'Drivers/'))
        oc_drivers_update = os.path.abspath(os.path.join(tmp_path, 'X64/EFI/OC/Drivers/'))
        for driver in os.listdir(oc_drivers_update):
            drivers.append(driver)
        for driver in os.listdir(oc_drivers_source):
            if driver[0] == '.':
                continue
            if driver not in drivers:
                print(self.Colors("[Warning] Driver " + driver + " is not in Official Drivers folders, update skipped", fcolor='yellow'))
                continue
            source_driver = os.path.abspath(os.path.join(oc_drivers_source, driver))
            update_driver = os.path.abspath(os.path.join(oc_drivers_update, driver))
            shutil.copy(update_driver, source_driver)
        print(self.Colors("[Info] Update Drivers Done", fcolor='green'))

        # Tools update
        print(self.Colors("[Info] Updating OpenCorePkg Tools...", fcolor='green'))
        tools = []
        oc_tools_source = os.path.abspath(os.path.join(self.root, 'Tools/'))
        oc_tools_update = os.path.abspath(os.path.join(tmp_path, 'X64/EFI/OC/Tools/'))
        for tool in os.listdir(oc_tools_update):
            tools.append(tool)
        for tool in os.listdir(oc_tools_source):
            if tool[0] == '.':
                continue
            if tool not in tools:
                print(self.Colors("[Warning] Tool " + tool + " is not in Official Tools folders, update skipped", fcolor='yellow'))
                continue
            source_tool = os.path.abspath(os.path.join(oc_tools_source, tool))
            update_tool = os.path.abspath(os.path.join(oc_tools_update, tool))
            shutil.copy(update_tool, source_tool)
        print(self.Colors("[Info] Update Tools Done", fcolor='green'))

        # check plist
        ocvalidate_path = os.path.abspath(os.path.join(tmp_path, 'Utilities/ocvalidate/ocvalidate'))
        os.system('chmod +x ' + ocvalidate_path)
        plist_path = os.path.abspath(os.path.join(self.root, 'Config.plist'))
        if not os.path.exists(plist_path):
            plist_path = os.path.abspath(os.path.join(self.root, 'config.plist'))
        if not os.path.exists(plist_path):
            print(self.Colors("[Warning] config plist not found, check skipped", fcolor='yellow'))
        else:
            os.system('chmod +x ' + ocvalidate_path)
            ocvalidate_path_sys = ocvalidate_path.replace(' ', '\ ')
            plist_path_sys = plist_path.replace(' ', '\ ')
            v = os.popen(ocvalidate_path_sys + ' ' + plist_path_sys).read()
            if "No issues found" in v:
                print(self.Colors("[Info] **** Config plist check Done, No issues Found! ****", fcolor='green'))
            else:
                update_config = os.path.abspath(os.path.join(sys.path[0], "cache/OpenCorePkg/Docs/SampleCustom.plist"))
                source_config = plist_path
                save_config = os.path.abspath(os.path.join(sys.path[0], "cache/OpenCorePkg/Config.plist"))
                self.update_oc_config(update_config, source_config, save_config)
                shutil.copy(save_config, source_config)
                v2 = os.popen(ocvalidate_path_sys + ' ' + save_config.replace(' ', '\ ')).read()
                if "No issues found" in v2:
                    print(self.Colors("[Info] **** Config update automatically and check Done, No issues Found! ****", fcolor='green'))
                    print(self.Colors("[Warning] **** Automatically plist update is not reliable all the time, please check and save your backup EFI in backup_EFI folder ****", fcolor='yellow'))
                else:
                    v = v2.split(self.remote[self.bootloader]['version'] + '!')
                    v = v[1].strip()
                    v = v.split('Completed validating')
                    v1 = v[0].strip()
                    v1 = v1.replace('\n', '\n\t')
                    v1 = '\t' + v1
                    v2 = v[1].split('. Found ')
                    v2 = 'Found ' + v2[1]
                    v2 = v2.replace('.', ':')
                    print(self.Colors("[Error] Config plist update automatically and check Done, Errors still occur: " + v2 + ' ', fcolor='red'))
                    print(self.Colors(v1, fcolor='yellow'))
                    print(self.Colors("[Warning] Please read instruction from the official website to update your config.plist or recover EFI from backup.", fcolor='yellow'))

        # clean cache
        print(self.Colors("[Info] Cleaning cache...", fcolor='green'))
        shutil.rmtree(tmp_path)
        print(self.Colors("[Info] Clean Done", fcolor='green'))

        input("Press [Enter] to continue...")

        # update kexts
        # mkdir cache folder for downloading kexts
        tmp_path = os.path.abspath(os.path.join(tmp_root, 'cache/'))
        if not os.path.exists(tmp_path):
            os.mkdir(tmp_path)
        tmp_path = os.path.abspath(os.path.join(tmp_path, 'Kexts/'))
        if not os.path.exists(tmp_path):
            os.mkdir(tmp_path)
        # save info for progress and error kexts
        progress = [0, 0]
        '''
        progress[0]:
            the No. of updating kext
        progress[1]:
            0: download
            1: extract
            2: copy
            3: clean
        '''
        err = []
        # check every local kexts
        for kext in self.local.keys():
            # update_info including OpenCorePKG, we need to skip it
            if kext == self.bootloader:
                continue
            progress[0] = progress[0] + 1
            progress[1] = 0
            self.update_oc_interface(kext, progress)

            # download
            try:
                tmp = os.path.abspath(os.path.join(tmp_path, kext + '.zip'))
                update_type = self.type
                update_type = update_type.lower()
                headers = {"Auth": "{abcd}", "accept": "*/*",
                           "accept-encoding": "gzip;deflate;br"}
                response = requests.request(
                    "GET", self.update_info[kext][update_type]['link'], headers=headers)
                with open(tmp, "wb") as f:
                    f.write(response.content)
                progress[1] = progress[1] + 1
            except:
                err.append(kext)
                continue
            self.update_oc_interface(kext, progress)

            # extract
            try:
                tmp_path0 = os.path.abspath(
                    os.path.join(tmp_path,  kext + '/'))
                ys = zipfile.ZipFile(tmp)
                ys.extractall(tmp_path0)
                ys.close()
                os.remove(tmp)
                tmp_path1 = os.path.abspath(os.path.join(tmp_path,  kext))
                tmp_path1 = os.path.abspath(os.path.join(tmp_path1,  'Kexts'))
                if os.path.exists(tmp_path1):
                    os.system('mv ' + tmp_path1 + '/* ' + tmp_path0)
                progress[1] = progress[1] + 1
            except:
                err.append(kext)
                continue
            self.update_oc_interface(kext, progress)

            # copy
            try:
                for k in self.update_info[kext]['kexts']:
                    source = os.path.abspath(
                        os.path.join(self.root, 'Kexts/'))
                    update = os.path.abspath(os.path.join(tmp_path0, k))
                    source = source.replace(' ', '\ ')
                    os.system('cp -rf ' + update + ' ' + source)
                progress[1] = progress[1] + 1
            except:
                err.append(kext)
                continue
            
            # clean
            try:
                shutil.rmtree(tmp_path0)
                progress[1] = progress[1] + 1
            except:
                err.append(kext)
                continue
            self.update_oc_interface(kext, progress)
        
        os.system('clear')
        self.title()
        first_time = 0
        # if not err, print info of success
        for i in self.local.keys():
            cg = self.update_info[i]
            if i == self.bootloader:
                continue
            if i not in err:
                if first_time == 0:
                    if len(err) > 0:
                        print(self.Colors(
                            "These Kext Package(s) Update Successfully:", fcolor='magenta'))
                    else:
                        print(self.Colors(
                            "All Kext Packages Update Successfully:", fcolor='magenta'))
                    first_time = 1
                if len(i) < 11:
                    print(self.Colors("   " + i, fcolor='blue'))
                else:
                    print(self.Colors("   " + i, fcolor='blue'))
        print("")
        # if err, print error info
        if len(err) > 0:
            first_time = 0
            for i in self.local.keys():
                if i == self.bootloader:
                    continue
                cg = self.update_info[i]
                if i in err:
                    if first_time == 0:
                        print(self.Colors(
                            "These Kext Package(s) Update Unsuccessfully:", fcolor='red'))
                        first_time = 1
                    if len(i) < 11:
                        print(self.Colors("   " + i, fcolor='yellow'))
                    else:
                        print(self.Colors("   " + i), fcolor='yellow')
            print("")


    # update kexts interface
    def update_kexts_interface(self, kext, progress):
        os.system('clear')
        self.title()
        print("> Update Kexts Package")
        print("")
        progress1 = progress[0]
        progress2 = progress[1]
        ratio = float(progress1*4 + progress2 - 4)/self.update[1]/4
        sym_nums = 60
        sym_progress = int(sym_nums*ratio)
        space = sym_nums - sym_progress
        print("[" + str(progress1) +"/" + str(self.update[1]) + "]  " + str(round(ratio*100,2)) + " %  [" + "="*sym_progress + " "*space + "]")
        print("")
        print("Updating Kext Package: " + self.Colors(kext, fcolor='yellow') + "\n" + "These kext(s) will be update: ")
        for k in self.update_info[kext]['kexts']:
            print(self.Colors("\t" + k, fcolor='yellow'))
        print("")
        if progress2 >= 0:
            print(self.Colors("[Info] Downloading Kext Package: " + kext, fcolor='green'))
        if progress2 >= 1:
            print(self.Colors("[Info] Download Kext Package: " + kext + " Done", fcolor='green'))
            print(self.Colors("[Info] Extracting Kext Package: " + kext, fcolor='green'))
        if progress2 >= 2:
            print(self.Colors("[Info] Extract Kext Package: " + kext + " Done", fcolor='green'))
            print(self.Colors("[Info] Updating Kext Package: " + kext, fcolor='green'))
        if progress2 >= 3:
            print(self.Colors("[Info] Update Kext Package: " + kext + " Done", fcolor='green'))
            print(self.Colors("[Info] Cleaning Cache: " + kext, fcolor='green'))
        if progress2 >= 4:
            print(self.Colors("[Info] Clean Cache: " + kext + " Done", fcolor='green'))


    # update kexts
    def update_kexts(self):
        # mkdir cache folder for downloading kexts
        tmp_root = sys.path[0]
        tmp_path = os.path.abspath(os.path.join(tmp_root, 'cache/'))
        if not os.path.exists(tmp_path):
            os.mkdir(tmp_path)
        tmp_path = os.path.abspath(os.path.join(tmp_path, 'Kexts/'))
        if not os.path.exists(tmp_path):
            os.mkdir(tmp_path)
        # save info for progress and error kexts
        progress = [0, 0]
        '''
        progress[0]:
            the No. of updating kext
        progress[1]:
            0: download
            1: extract
            2: copy
            3: clean
        '''
        err = []
        # check every local kexts
        for kext in self.local.keys():
            # update_info including OpenCorePKG, we need to skip it
            cg = self.update_info[kext]
            if kext == self.bootloader:
                continue
            if cg['status'] != "Update Available":
                continue
            progress[0] = progress[0] + 1
            progress[1] = 0
            self.update_kexts_interface(kext, progress)
            
            # download
            try:
                tmp = os.path.abspath(os.path.join(tmp_path, kext + '.zip'))
                update_type = self.type
                update_type = update_type.lower()
                headers = {"Auth": "{abcd}", "accept": "*/*", "accept-encoding": "gzip;deflate;br"}
                response = requests.request("GET", self.update_info[kext][update_type]['link'], headers = headers)
                with open(tmp, "wb") as f:
                    f.write(response.content)
                progress[1] = progress[1] + 1
            except:
                err.append(kext)
                continue
            self.update_kexts_interface(kext, progress)

            # extract
            try:
                tmp_path0 = os.path.abspath(os.path.join(tmp_path,  kext + '/'))
                ys = zipfile.ZipFile(tmp)
                ys.extractall(tmp_path0)
                ys.close()
                os.remove(tmp)
                tmp_path1 = os.path.abspath(os.path.join(tmp_path,  kext))
                tmp_path1 = os.path.abspath(os.path.join(tmp_path1,  'Kexts'))
                if os.path.exists(tmp_path1):
                    os.system('mv ' + tmp_path1 + '/* ' + tmp_path0)
                progress[1] = progress[1] + 1
            except:
                err.append(kext)
                continue
            self.update_kexts_interface(kext, progress)

            # copy
            try:
                for k in self.update_info[kext]['kexts']:
                    source = os.path.abspath(os.path.join(self.root, 'Kexts/'))
                    update = os.path.abspath(os.path.join(tmp_path0, k))
                    info_plist = os.path.abspath(os.path.join(update, 'Contents/Info.plist'))
                    with open(info_plist, 'rb') as pl:
                        origin = load(pl)
                        rewrite = copy.deepcopy(origin)
                    with open(info_plist, 'wb') as new_plist:
                        dump(rewrite, new_plist, fmt=FMT_XML,sort_keys=True, skipkeys=False)
                    source = source.replace(' ', '\ ')
                    os.system('cp -rf ' + update + ' ' + source)
                progress[1] = progress[1] + 1
            except:
                err.append(kext)
                continue
            
            # clean
            try:
                shutil.rmtree(tmp_path0)
                progress[1] = progress[1] + 1
            except:
                err.append(kext)
                continue
            self.update_kexts_interface(kext, progress)
        
        os.system('clear')
        self.title()
        # if not err, print info of success
        first_time = 0
        for i in self.local.keys():
            cg = self.update_info[i]
            if i == self.bootloader:
                continue
            if cg['status'] == "Update Available" and (i not in err):
                if first_time == 0:
                    if len(err) > 0:
                        print(self.Colors("These Kext Package(s) Update Successfully:", fcolor='magenta'))
                    else:
                        print(self.Colors("All Kext Packages Update Successfully:", fcolor='magenta'))
                    first_time = 1
                if len(i) < 11:
                    print(self.Colors("   " + i + ":\t\t" + cg['local_version'] + ' (' + cg['local_time'][0] +'-' + cg['local_time'][1] + '-' + cg['local_time'][2] + ' ' + cg['local_time'][3] + ':' + cg['local_time'][4] + ':' + cg['local_time'][5] + ')' + '  ->  ' + cg['remote_version'] + ' (' + cg['remote_time'][0] + '-' + cg['remote_time'][1] + '-' + cg['remote_time'][2] + ' ' + cg['remote_time'][3] + ':' + cg['remote_time'][4] + ':' + cg['remote_time'][5] + ')', fcolor='blue'))
                else: 
                    print(self.Colors("   " + i + ":\t" + cg['local_version'] + ' (' + cg['local_time'][0] +'-' + cg['local_time'][1] + '-' + cg['local_time'][2] + ' ' + cg['local_time'][3] + ':' + cg['local_time'][4] + ':' + cg['local_time'][5] + ')' + '  ->  ' + cg['remote_version'] + ' (' + cg['remote_time'][0] + '-' + cg['remote_time'][1] + '-' + cg['remote_time'][2] + ' ' + cg['remote_time'][3] + ':' + cg['remote_time'][4] + ':' + cg['remote_time'][5] + ')', fcolor='blue'))
        print("")

        # if err occur, print error info
        if len(err) > 0:
            first_time = 0
            for i in self.local.keys():
                if i == self.bootloader:
                    continue
                cg = self.update_info[i]
                if cg['status'] == "Update Available" and (i in err):
                    if first_time == 0:
                        print(self.Colors("These Kext Package(s) Update Unsuccessfully:", fcolor='red'))
                        first_time = 1
                    if len(i) < 11:
                        print(self.Colors("   " + i + ":\t\t" + cg['local_version'] + ' (' + cg['local_time'][0] +'-' + cg['local_time'][1] + '-' + cg['local_time'][2] + ' ' + cg['local_time'][3] + ':' + cg['local_time'][4] + ':' + cg['local_time'][5] + ')' + '  ->  ' + cg['remote_version'] + ' (' + cg['remote_time'][0] + '-' + cg['remote_time'][1] + '-' + cg['remote_time'][2] + ' ' + cg['remote_time'][3] + ':' + cg['remote_time'][4] + ':' + cg['remote_time'][5] + ')', fcolor='yellow'))
                    else: 
                        print(self.Colors("   " + i + ":\t" + cg['local_version'] + ' (' + cg['local_time'][0] + '-' + cg['local_time'][1] + '-' + cg['local_time'][2] + ' ' + cg['local_time'][3] + ':' + cg['local_time'][4] + ':' + cg['local_time'][5] + ')' +
                              '  ->  ' + cg['remote_version'] + ' (' + cg['remote_time'][0] + '-' + cg['remote_time'][1] + '-' + cg['remote_time'][2] + ' ' + cg['remote_time'][3] + ':' + cg['remote_time'][4] + ':' + cg['remote_time'][5] + ')', fcolor='yellow'))
            print("")



    # main
    def main(self):
        # clear
        os.system('clear')

        # init
        self.init()

        # operation
        while self.choice != 'Q':
            os.system("clear")
            self.title()
            if self.choice == 'A':
                self.choice = ''
                print("> All Kexts Information")
                print("")
                self.output_all()
                print("")
                input("Press [Enter] to back...")
                continue

            if self.choice == 'B':
                self.choice = ''
                print("> Back up EFI")
                print("")
                print(self.Colors("[Info] EFI folder is backing up...", fcolor='green'))
                self.backup_EFI()
                print(self.Colors("[Info] EFI back up Done", fcolor='green'))
                print("")
                input("Press [Enter] to back...")
                continue

            if self.choice == 'C':
                self.choice = ''
                self.type = self.change[self.type]
                continue

            if self.choice == 'D':
                self.choice = ''
                print("> Download and Update Remote Database")
                print("")
                print(self.Colors("[Info] Checking Network...", fcolor='green'))
                self.check_network()
                print(self.Colors("[Info] Check Network Done", fcolor='green'))
                if not self.network:
                    print(self.Colors('[Error] Network error, please check your connection to ' + self.url , fcolor='red'))
                    print(self.Colors('[Error] Update cancel because of connection error', fcolor='red'))
                    print("")
                    input("Press [Enter] to back...")
                    continue
                print(self.Colors("[Info] Connection successfully", fcolor='green'))
                print(self.Colors("[Info] Downloading the latest remote database...", fcolor='green'))
                self.download_database()
                print(self.Colors("[Info] Download Done", fcolor='green'))
                print(self.Colors("[Info] Updating remote data", fcolor='green'))
                self.remote = self.get_remote_data()
                self.update_info = self.gen_update_info()
                print(self.Colors("[Info] Update Done", fcolor='green'))
                print("")
                input("Press [Enter] to back...")
                continue
            
            if self.choice == 'L':
                self.choice = ''
                print("> Reload Data")
                print("")
                print(self.Colors("[Info] Reloading local data...", fcolor='green'))
                self.remote = self.get_remote_data()
                self.local = self.get_local_data()
                self.update_info = self.gen_update_info()
                print(self.Colors("[Info] Reload local data Done", fcolor='green'))
                continue

            if self.choice == 'R':
                self.choice = ''
                print("> Refresh Network")
                print("")
                print(self.Colors("[Info] Checking Network...", fcolor='green'))
                self.check_network()
                print(self.Colors("[Info] Checking Network Done", fcolor='green'))
                continue

            if self.choice == 'S':
                self.choice = ''
                print("> Update Information")
                print("")
                self.output_update()
                print("")
                input("Press [Enter] to back...")
                continue

            if self.choice == 'UO':
                self.choice = ''
                print("> Update OpenCore")
                print("")
                if self.update[0] == 0:
                    print(self.Colors("[Info] OpenCore is up-to-date", fcolor='green'))
                    print("")
                    input("Press [Enter] to back...")
                    continue
                # check network
                self.check_network()
                if not self.network:
                    print(self.Colors('[Error] Network error', fcolor='red'))
                    print(self.Colors("[Error] OpenCore Update canceled because of network error.", fcolor='red'))
                    print("")
                    input("Press [Enter] to back...")
                    continue
                print(self.Colors("[Info] EFI folder is backing up...", fcolor='green'))
                self.backup_EFI()
                print(self.Colors("[Info] EFI back up Done", fcolor='green'))
                print(self.Colors("[Info] OpenCore Update Begin", fcolor='green'))
                self.update_OpenCore()
                print(self.Colors("[Info] OpenCore and All Kexts Update Done", fcolor='green'))
                print(self.Colors("[Info] Updating local data...", fcolor='green'))
                self.local = self.get_local_data()
                self.update_info = self.gen_update_info()
                print(self.Colors("[Info] Update local data Done", fcolor='green'))
                print("")
                input("Press [Enter] to back...")
                continue

            if self.choice == 'UK':
                self.choice = ''
                print("> Update Kexts")
                print("")
                if self.update[1] == 0:
                    print(self.Colors("[Info] All Installed Kexts is up-to-date", fcolor='green'))
                    print("")
                    input("Press [Enter] to back...")
                    continue
                # check network
                self.check_network()
                if not self.network:
                    print(self.Colors('[Error] Network error', fcolor='red'))
                    print(self.Colors("[Error] Kexts Update canceled because of network error.", fcolor='red'))
                    print("")
                    input("Press [Enter] to back...")
                    continue
                print(self.Colors("[Info] EFI folder is backing up...", fcolor='green'))
                self.backup_EFI()
                print(self.Colors("[Info] EFI back up Done", fcolor='green'))
                self.update_kexts()
                print(self.Colors("[Info] All Kexts update Done.", fcolor='green'))
                print(self.Colors("[Info] Updating local data...", fcolor='green'))
                self.local = self.get_local_data()
                self.update_info = self.gen_update_info()
                print(self.Colors("[Info] Update local data Done", fcolor='green'))
                print("")
                input("Press [Enter] to back...")
                continue

            self.main_interface()
        
        # quit
        os.system("clear")
        self.title()
        # unmount EFI
        if self.mode == 0:
            res = os.popen('echo ' + self.password + ' | sudo -S diskutil unmount force /dev/' + self.EFI_disk).read().strip()
            print(self.Colors("[Info] (EFI partition) " + res + ".", fcolor='green'))
        print(self.Colors("[Info] The script is terminated.", fcolor='green'))
        print("")
        print("Have a nice day ~")
        exit()


if __name__ == "__main__":
    # create obj
    oc_update = OCUpdater()

    # run script
    oc_update.main()
    