Welcome, this is the Klipper and Screen Software of Eryone Thinker X400 3D printer

### the main changlog:

 2025.12.2:

-   increase the bed heat waiting temperature range to reduce the waiting time.
  
2025.11.28:

-   fix a bug need to home first in some pause/resume case
-   optimize the menu on the left 
-   support upload file bigger than 500MB
-   fix a bug that cann't parse the thumbnail image with complicate 3d mode
  
2025.11.17:

  - support high temperature toolhead board that can compatible with 350C hothend
-   optimize the chamber heater heating process.

2025.11.12:

-   auto hiden the passward of wifi

2025.11.6: 

-   support the new toolhead board with new ADC chip for strain gauge sensor
-   fix a bug for homing printer
-   support changing the bed mesh points on the screen

2025.10.9:

-   fix a resume print bug after power off.
-   set the printer disconnect to the cloud by default

2025.8:

-   support change the load/unload temperature on the screen 
-   add timezone auto update

2025.7:

-   support resume printing at any layer on the screen
-   optimize the memory process while printing to prevent timeout problem by klipper.









### How to Upgrade?
There are 3 ways to update and don't forget to reboot the printer after that:
1. Upgrade the software from the SSH (username:`mks` password:`makerbase`)

```
cd ~
mv KlipperScreen KlipperScreen_bk
git clone https://gitcode.com/xpp012/KlipperScreen.git
~/KlipperScreen/all/git_pull.sh

```

2. Upgrade the software from the screen

`More-->System-->Update`

3. Upgrade the software from the farm3d webpage

go to https://eryone.club , then send `Update Software` command in the console page.


### How to Flash linux into the SDcard?
1. Download and unzip the img file from the google drive : https://drive.google.com/drive/folders/1htD4KUY9WmH9W7UyBleRF0uzNoNothT1?usp=sharing
2. Plugin the sdcard into the PC, and flashed it with the balenaEtcher.exe
3. Plugin the sdcard into the X400 printer,and power on the printer.
4. Get the CAN UUID numbers from the printer screen: Memu-->Console-->Send `W`  (note:not `w` but `W`)
5. Back to the Menu and click: Firmware Restart, if it failed please restart the printer and run  Memu-->Console-->Send `W`  again.

### orca slicer
It is recommended that you use this OrcaSlicer, which has been configured for the X400.
https://ln5.sync.com/4.0/dl/2515edb40#fykktwzu-v5tzvm7v-a7s3fay8-5wssn4u6
https://drive.google.com/drive/folders/1htD4KUY9WmH9W7UyBleRF0uzNoNothT1?usp=drive_link

### Software of Farm3D 
More information: [https://github.com/Eryone/farm3d](https://github.com/Eryone/farm3d)

