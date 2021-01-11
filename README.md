# Fabricaide

Source code for Fabricaide: Fabrication-Aware Design for 2D Cutting Machines.

## Requirements

* Mac OSX 10.6+ (may work  with older versions)
* [Docker](https://www.docker.com/)
* Adobe Illustrator
* The latest version  of [Processing](https://processing.org/)

## Adobe Illustrator swatch setup

If you plan on using Fabricaide with Adobe Illustrator and do not already have the custom Illustrator swatch, you will need to do the following:
* Open up Adobe Illustrator
* Open up the Swatches panel (if it is not visible, go to Window->Swatches)
* In the lower-left hand corner of the panel select the Swatch Libraries menu, then select Other Library...
* Inside the FabricaideUI folder, select  the `Fabricaide.ai` file

Once you have the Fabricaide swatch imported, you can now select it in the Swatch Libraries menu, under the User Defined submenu

## Running Fabricaide in Illustrator
* Download the entire FabricaideUI folder
* Install the Packaide backend
	* If you have a zip copy of the docker image (`packaide.tar.gz`), run `docker load < packaide.tar.gz` to load the image.
	* Alternatively, follow the instructions [here](https://github.com/HCIELab/FabricaideDocker) to build the image yourself.
	* If you don't have access to Docker, install Packaide following instructions [here](https://github.com/DanielLiamAnderson/Packaide) then comment out line 7 and uncomment line 6 in `Fabricaide.command`.
* Create a blank Adobe Illustrator document (use a resolution of 72 PPI and color mode of RGB)
* Double-click the `Fabricaide.command` file (it is a Terminal shell script). If it is not double-clickable, try executing it with `./Fabricaide.command`