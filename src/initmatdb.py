from cairosvg import svg2png
import json
import os
from parse_materials import parse
import shutil
import sys

# ASSUMES USER IS WORKING AT 72 PPI, DOC MODE RGB
# requires that the parsed document has at least 2 materials

MATDB_PROCESSING = 'FabricaideUI/data/matdb'

if os.path.exists(MATDB_PROCESSING):
    shutil.rmtree(MATDB_PROCESSING)

os.mkdir(MATDB_PROCESSING)

PPI = 72

# materialsubstitutes = {}

def gen_db_from_file():
    colordictionary = {}
    colordictionary2 = {}

    if len(sys.argv) < 2:
        print('Required argument: filename')

    filename = sys.argv[1]

    fillmappings, materialinfo, materialsheets = parse(filename)

    for matname, svglist in materialsheets.items():
        materialsheets[matname] = [svg.toprettyxml() for svg in svglist]

        if not os.path.exists(MATDB_PROCESSING+'/'+matname):
            os.mkdir(MATDB_PROCESSING+'/'+matname)

        for i,svg in enumerate(svglist):
            svgstring = svg.toprettyxml()
            svg2png(bytestring=svgstring, write_to=MATDB_PROCESSING+'/'+matname+'/'+str(i)+'.png')

    for fill in fillmappings:
        h = fill.split(':')[1][1:]
        color = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        colordictionary[fillmappings[fill]] = color
        colordictionary2[fillmappings[fill]] = fill

    with open('FabricaideUI/data/colordict.json', 'w') as outfile:
        json.dump(colordictionary, outfile)

    with open('colordict2.json', 'w') as outfile:
        json.dump(colordictionary2, outfile)

    data = {'fillmappings':fillmappings, 'materialinfo':materialinfo, 'materialsheets':materialsheets}

    with open('mat-data.txt', 'w') as outfile:
        json.dump(data, outfile)


def updateViewbox():
    global materialinfo
    
    for matname in materialinfo:
        width = float(materialinfo[matname]['width'][:-2])
        height = float(materialinfo[matname]['height'][:-2])
        materialinfo[matname]['viewBox'] = '0 0 {} {}'.format(int(width*PPI), int(height*PPI))

def make_material_copies(matname, fill, width, height, copies):
    global materialsheets
    if matname not in materialsheets:
            materialsheets[matname] = []

    for i in range(copies):
        width = materialinfo[matname]['width']
        height = materialinfo[matname]['height']
        viewBox = materialinfo[matname]['viewBox']


        svgstring = '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="{}"></svg>'.format(width, height, viewBox)

        materialsheets[matname].append(svgstring)
        
        if not os.path.exists(MATDB_PROCESSING+'/'+matname):
            os.mkdir(MATDB_PROCESSING+'/'+matname)
        svg2png(bytestring=svgstring, write_to=MATDB_PROCESSING+'/'+matname+'/'+str(i)+'.png')

if __name__ == "__main__":
    gen_db_from_file()

