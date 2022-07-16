import json
import sys
import requests
import os
import time
import copy
from plistlib import *

# the identification of EFI_disk
EFI_disk = 'disk0s4'

# PATH and Constant
ROOT = sys.path[0]
path = ROOT + '/data.json'
kexts_list = [
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


# get file modified time
def get_time(file):
    time0 = []
    k_time = os.stat(file).st_mtime
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
def compare_time(t1, t2):
    res = 0
    if t2[-1] > t1[-1]:
        res = 1
    return res


# get local data
def get_local_data(kexts_list, root):
    local = {}
    first_time1 = 0
    first_time2 = 0

    # OpenCore
    oc = os.path.abspath(os.path.join(root, 'EFI/OC/OpenCore.efi'))
    oc_ver = os.popen('nvram 4D1FDA02-38C7-4A6A-9CC6-4BCCA8B30102:opencore-version').read()
    oc_ver = oc_ver.split('REL-')[-1]
    oc_ver = oc_ver[0:3]
    ver = oc_ver[0] + '.' + oc_ver[1] + '.' + oc_ver[2]
    time = get_time(oc)
    local['OpenCorePkg'] = {'time': time, 'version': ver}

    # kexts
    for kext in os.listdir(os.path.join(root, 'EFI/OC/Kexts')):
        kext0 = kext.split('.')
        kext0 = kext0[0]
        domain = os.path.abspath(os.path.join(root, 'EFI/OC/Kexts'))
        kext_full = os.path.join(domain, kext)

        # BrcmPatchRAM
        if kext0[0:4] == 'Brcm' or kext0 == 'BlueToolFixup':
            if first_time1 == 0:
                plist = os.path.join(kext_full, 'Contents/Info.plist')
                with open(plist, 'rb') as pl:
                    plist = load(pl)
                    ver = plist['CFBundleVersion']
                    pl.close()
                time = get_time(kext_full)
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
                time = get_time(kext_full)
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
            time = get_time(kext_full)
            local['VoodooPS2'] = {'time': time, 'version': ver, 'kexts': [kext]}
            continue
        
        # other not in kexts_list: skip
        if kext0 not in kexts_list:
            continue
        
        # in kexts_list: save time and kext name
        plist = os.path.join(kext_full, 'Contents/Info.plist')
        with open(plist, 'rb') as pl:
            plist = load(pl)
            ver = plist['CFBundleVersion']
            pl.close()
        time = get_time(kext_full)
        local[kext0] = {'time': time, 'version': ver, 'kexts': [kext]}
    return local


# download database
def download_database(path):
    url = 'https://raw.githubusercontent.com/dortania/build-repo/builds/config.json'
    r = requests.get(url)
    with open(path, 'wb') as f:
        f.write(r.content)
        f.close


# get remote data
def get_remote_data(kexts_list, path):
    remote = {}
    with open(path, 'r') as f:
        row_data = json.load(f)
        f.close()
    for i in kexts_list:
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
def gen_update_info(local, remote):
    update_info = copy.deepcopy(remote)
    for key in update_info.keys():
        update_info[key].pop('time')
        update_info[key].pop('version')
        update_info[key]['local_time'] = None
        update_info[key]['remote_time'] = remote[key]['time']
        update_info[key]['local_version'] = None
        update_info[key]['remote_version'] = remote[key]['version']
        update_info[key]['kexts'] = [None]
    for key in local.keys():
        time1 = local[key]['time']
        time2 = remote[key]['time']
        res = compare_time(time1, time2)
        update_info[key]['local_time'] = time1
        update_info[key]['local_version'] = local[key]['version']
        if key != "OpenCorePkg":
            update_info[key]['kexts'] = local[key]['kexts']
        if res == 1:
            update_info[key]['status'] = "Update Available"
            continue
        update_info[key]['status'] = "Up-to-date"
    return update_info


# output information
def output_info(dict):
    for i in dict.keys():
        print(i)
        cg = dict[i]
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
def mount_EFI(EFI_disk):
    out = os.popen('sudo -s diskutil mount /dev/' + EFI_disk).read()
    out = out.strip()
    out = out.split('on')
    out = out[0]
    out = out.split('Volume')
    out = out[1].strip()
    EFI_root = os.path.join('/Volumes/', out)
    return EFI_root

# init
def init(EFI_disk, path, kexts_list):
    print('[Info] 请输入密码以挂载 EFI 分区（输入密码时不可见）：')

    # mount EFI and get EFI partition name
    EFI_root = mount_EFI(EFI_disk)

    print('[Info] 正在初始化程序...')

    # judge if database file exists
    if ~os.path.exists(path):
        print('[Info] 未发现数据文件，正在下载...')
        download_database(path)
        print('[Info] 数据文件下载完成')
    print('[Info] 发现数据文件')
    print('[Info] 正在处理数据文件')

    # get local data
    local = get_local_data(kexts_list, EFI_root)

    # get remote data
    remote = get_remote_data(kexts_list, path)

    # generate update information
    update_info = gen_update_info(local, remote)

    print('[Info] 数据文件处理完成')
    print('[Info] 初始化完成')
    return update_info


if __name__ == "__main__":
    # init
    info = init(EFI_disk, path, kexts_list)

    # update info output
    output_info(info)

    # unmount EFI
    os.system('sudo -s diskutil mount /dev/' + EFI_disk)