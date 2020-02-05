# DWM1001-DEV


# Installation

## Flasher le DWM1001-DEV

Pour fonctionner, la carte DWM1001-DEV a besoin d'être flashée. 

* Télécharger le dossier dans lequel se trouve l'image à flasher, ainsi que toutes les documentations sur le [site de Decawave](https://www.decawave.com/1001-license/) (fichier de plus de 1.9 Go)

* Installer "J-FlashLite" disponible sur le site de [SEGGER](https://www.segger.com/downloads/jlink#J-LinkSoftwareAndDocumentationPack), section "J-Link Software and Documentation Pack".

* Ouvrir J-FlashLite.

* Sélectionner en device nRF52832_xxAA (Manufacturer : Nordic Semi)

* Interface SWD, fréquence 1000 kHz, "OK"

![JFlashLite](docs/source/img/JFlashLite1.png)

* Selectionner le data file ```DWM1001_DWM1001-DEV_MDEK1001_Sources_and_Docs_v9/DWM1001/Factory_Firmware_Image/DWM1001_PANS_R2.0.hex```

![JFlashLite](docs/source/img/JFlashLite2.png)

* Brancher la DWM1001-DEV.

![JFlashLite](docs/source/img/DWM1001_DEV_plugged.png)

* Cliquer sur "Program Ship"

![JFlashLite](docs/source/img/JFlashLite3.png)

La carte est flashée, les LEDs ont du changer de couleur. Vous pouvez la débrancher.

![JFlashLite](docs/source/img/DWM1001_DEV_flashed.png)


