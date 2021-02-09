# Fabricaide

Source code for Fabricaide: Fabrication-Aware Design for 2D Cutting Machines.

![Fabricaide](GIFteasernolabels.gif)

### Acknowledgements 

[Fabricaide](https://hcie.csail.mit.edu/) is a system that helps designers of laser-cut objects make material-conscious design decisions and make the most of their scrap material. If you use Fabricaide as part of your research, please cite it as follows

> Fabricaide: Fabrication-Aware Design for 2D Cutting Machines.
> Ticha Sethapakdi, Daniel Anderson, Adrian Reginald Chua Sy, Stefanie Mueller.
> To Appear in The Proceedings of the 2021 ACM CHI Conference on Human Factors in Computing Systems, 2021

## Requirements

* Mac OSX 10.6+ (may work  with older versions)
* [Docker](https://www.docker.com/)
* Adobe Illustrator
* The latest version  of [Processing](https://processing.org/)


## Fabricaide backend setup

* Install the [Packaide](https://github.com/DanielLiamAnderson/Packaide) backend
	* If you have a zip copy of the docker image (`packaide.tar.gz`), run `docker load < packaide.tar.gz` to load the image.
	* Alternatively, follow the instructions [here](https://github.com/HCIELab/FabricaideDocker) to build the image yourself.
	* If you don't have access to Docker, install Packaide following instructions [here](https://github.com/DanielLiamAnderson/Packaide) then comment out line 7 and uncomment line 6 in `Fabricaide.command`.
* Initialize the sample material database by running `python3 initmatdb.py MatDB.svg`    


## Processing setup

You will need the ControlP5 library and processing-java. This step only needs to be done once.
* Open Processing
* Tools > install "processing-java"
* Sketch > Import library > add library
* Search for "ControlP5" and install it


## Adobe Illustrator swatch setup

If you plan on using Fabricaide with Adobe Illustrator and do not already have the custom Illustrator swatch, you will need to do the following:
* Open up Adobe Illustrator
* Open up the Swatches panel (if it is not visible, go to Window->Swatches)
* In the lower-left hand corner of the panel select the Swatch Libraries menu, then select Other Library...
* Inside the src/FabricaideUI folder, select  the `Fabricaide.ai` file

Once you have the Fabricaide swatch imported, you can now select it in the Swatch Libraries menu, under the User Defined submenu

## Using Fabricaide with Adobe Illustrator

* Create a blank Adobe Illustrator document (use a resolution of 72 PPI and color mode of RGB)
* Double-click the `Fabricaide.command` file (it is a Terminal shell script). If it is not double-clickable, try executing it with `./Fabricaide.command`. If you are not using Docker, run `Fabricaide-nodocker.command` instead.
* Please refer to the [Fabricaide Reference Guide](https://docs.google.com/document/d/1dcog25s2pAyX-dLwB0EoQPB70EbVmCBMU2zszpl-_LE/edit?usp=sharing) for more details on how to use Fabricaide in Illustrator