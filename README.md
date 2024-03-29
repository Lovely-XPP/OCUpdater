# OCUpdater
## Introduce

Utility for hackintosh user to update opencore and main kexts. The script will automatically detect the local kexts or OpenCorePkg's version and compare with the remote one, then give the update information of them.

## To Do

- [x] Mount EFI
- [x] Allow to Choose EFI when Encountering More Than 1 EFI
- [x] Allow to Choose Local OpenCore EFI Folder
- [x] Hide Password Input
- [x] Gengerate update information
- [x] Network connection check
- [x] main interface
- [x] EFI backup 
- [x] OpenCorePkg update
- [x] config.plist automatically update with OpenCore update
- [x] Kexts update

## Support kexts

- [x] OpenCorePkg

- [x] AirportBrcmFixup

- [x] AppleALC

- [x] BT4LEContinuityFixup

- [x] BrcmPatchRAM

- [x] BrightnessKeys

- [x] CPUFriend

- [x] CpuTopologySync

- [x] CpuTscSync

- [x] DebugEnhancer

- [x] ECEnabler

- [x] FeatureUnlock

- [x] HibernationFixup

- [x] IntelMausi

- [x] IntelBluetoothFirmware

- [x] Lilu

- [x] MacHyperVSupport

- [x] NVMeFix

- [x] NoTouchID

- [x] RTCMemoryFixup

- [x] RealtekRTL8111

- [x] RestrictEvents

- [x] UEFIGraphicsFB

- [x] VirtualSMC

- [x] VoodooInput

- [x] VoodooPS2

- [x] VoodooPS2-Alps

- [x] VoodooRMI

- [x] WhateverGreen

## Usage

- Clone the repo 
- Install Dependent modules of python

````bash
pip3 install -r requirements.txt
````

- Run `OCUpdater.command`.

Tip: When you run the script, the script will prompt you for password to mount EFI partition. If the process runs wrong, please create issue.

## Credits

- [Dortania](https://github.com/dortania) for provide binary and database of OpenCorePkg with main kexts in [build-repo](https://github.com/dortania/build-repo/tree/builds).

- [Acidanthera](https://github.com/Acidanthera) for OpenCorePkg and main kexts.

- [perez987](https://github.com/perez987) for testing and providing feedback.
