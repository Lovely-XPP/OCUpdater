# OCUpdater
## Introduce

A utility for hackintosh user to update opencore and some kexts. The script will automatically detect the local kexts or OpenCorePkg's version and compare with the remote one, then give the update information of them.

## To Do

- [x] Mount EFI
- [x] Gengerate update information
- [x] main interface
- [ ] EFI backup & update

## Support kexts

- [x] OpenCorePkg

- [x] AirportBrcmFixup,

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

Clone the repo and run `OCupdate.command`.

Tip: When you run the script, the script will automatically mount EFI partition without any passwords. If the process runs wrong, please create issue.

## Credits

- [Dortania](https://github.com/dortania) for provide binary and database of OpenCorePkg with some kexts in [build-repo](https://github.com/dortania/build-repo/tree/builds).
