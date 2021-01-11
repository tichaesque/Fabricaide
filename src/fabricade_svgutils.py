# Utilities for processing SVG files needed by Fabricade
#
# Provides:
#   prepareForCutting: changes the style attribute of all of
#     the shapes in the given SVG file to those required by
#     the laser cutter to be considered as contours to cut.
#  updateMaterialHoles: Adds the holes from the given job
#    file to the sheet with the given material name and sheet
#    id. This essentially merges the two SVG files and applies
#    the appropriate styles for each of the shapes
#  generateThumbnails: Generates all of the thumbnail images
#    for the material database
#  getCurrentPackedParts: Return a list of the SVG elements
#    that are currently packed onto the given sheet
#  removeTransform: Remove the transform attribute from an XML
#    strinng
#  equalsIgnoreTransform: Return True if the two given SVG XML
#   elements are equal ignoring their transform attribute

import json
import os
import xml.dom.minidom as DOM

from cairosvg import svg2png

# SVG elements and style for laser cuts
SVG_SHAPE_ELEMENTS = ['circle', 'rect', 'ellipse', 'polygon', 'polyline', 'path']
CUT_STYLE = 'fill:none;stroke:red;stroke-width:1px'
HOLE_STYLE = 'fill:#646464;stroke:none'

# Material database
MAT_DB = 'mat-data.txt'   # Material availability data
CUT_DIR = 'cuts'          # Currently packed cuts
THUMB_DIR = 'FabricaideUI/data/matdb/'  # Material thumbnails

# Add the holes depicted in matname:sheetid to the
# given SVG file
def addHolesToSVG(svgfile, matname, sheetid):
  with open(MAT_DB, 'r') as infile:
    matdb = json.load(infile)

  shapes = DOM.parse(svgfile)
  svg = shapes.getElementsByTagName('svg')[0]

  # Copy the holes into the new group
  holedom = DOM.parseString(matdb['materialsheets'][matname][sheetid])
  holesvg = holedom.getElementsByTagName('svg')[0]
  for child in holesvg.childNodes:
    svg.appendChild(child.cloneNode(True))

  # Save the file with holes
  with open(svgfile, 'w') as outfile:
    outfile.write(svg.toxml())

# Remove the depictions of the holes from the given
# packed SVG file
def removeHolesFromSVG(svgfile):
  shapes = DOM.parse(svgfile)
  svg = shapes.getElementsByTagName('svg')[0]
  holes = []

  # Find holes, identifying them by their fill style
  def collect_holes(node):
    if node.nodeType != node.TEXT_NODE:
      if node.hasAttribute('style') and node.getAttribute('style').startswith(HOLE_STYLE):
        holes.append(node)
      for child in node.childNodes:
        collect_holes(child)
  collect_holes(svg)

  # Remove all holes
  for hole in holes:
    hole.parentNode.removeChild(hole)

  # Save the file without holes
  with open(svgfile, 'w') as outfile:
    outfile.write(svg.toxml())

# Prepare the given file for cutting. This consists in
# changing the style of the SVG elements to the appropriate
# fill and stroke to be interpreted by the laser cutter.
#
# Returns: The filename of the prepared version of the file
def prepareForCutting(filename):
  doc = DOM.parse(filename)
  svgroot = doc.getElementsByTagName('svg')[0]
  
  def update(node):
    if node.nodeType != node.TEXT_NODE:
      if node.tagName in SVG_SHAPE_ELEMENTS:
        node.setAttribute('style', CUT_STYLE)
      elif node.tagName == 'g' or node.tagName == 'svg':
        for child in node.childNodes:
          update(child)

  update(svgroot)
  newfilename = filename[:-4] + "-prepared.svg"
  with open(newfilename, 'w') as f_out:
    f_out.write(doc.toxml())
  return newfilename

# Generate all of the thumbnails for the material database
def generateThumbnails():
  with open(MAT_DB, 'r') as infile:
    matdb = json.load(infile)
  for material, sheets in matdb['materialsheets'].items():
    for sheetid, sheet in enumerate(sheets):
      if not os.path.exists(os.path.join(THUMB_DIR, material)):
        os.makedirs(os.path.join(THUMB_DIR, material))
      pngout = os.path.join(THUMB_DIR, material, str(sheetid)+'.png')
      svg2png(bytestring=sheet, write_to=pngout)

# Return an XML string corresponding to the given
# XML string with the transform attribute removed,
# and the removed transform attribute
def removeTransform(part):
  node = DOM.parseString(part).childNodes[0]
  transform = node.getAttribute('transform')
  node.removeAttribute('transform')
  return node.toxml(), transform

# Returns true if the two part elements (given as SVG element strings)
# correspond to the same element, ignoring transformations, i.e. they
# are the same type and have the same size and location
def equalIgnoreTransform(part1, part2):
  return removeTransform(part1)[0] == removeTransform(part2)[0]

# Return a list of SVG elements corresponding to the parts
# that are currently packed onto the sheet with the given
# material name and sheet id.
def getCurrentPackedParts(matname, sheetid):
  filename = os.path.join(CUT_DIR, "{}_{}.svg".format(matname, sheetid))
  doc = DOM.parse(filename)
  svg = doc.getElementsByTagName('svg')[0]

  # Collect all of the SVG elements that correspond
  # to shapes (ignoring text nodes and groups).
  parts = []
  def collect_parts(node):
    if node.nodeType != node.TEXT_NODE:
      if node.tagName in SVG_SHAPE_ELEMENTS:
        parts.append(node.toxml())
      for child in node.childNodes:
        collect_parts(child)

  collect_parts(svg)
  return parts


# Add the contours from the given job file to the given
# material sheet as holes.
#
# TODO: For composite paths (paths with holes), we should
# just take the exterior part of the path. Also, we could
# avoid adding nested parts (parts that were packed inside
# another part's hole).
def updateMaterialHoles(jobfile, matname, sheetid):
  with open(MAT_DB, 'r') as infile:
    matdb = json.load(infile)
    
  materialsheet = matdb['materialsheets'][matname][sheetid]
  sheetdoc = DOM.parseString(materialsheet)
  sheetroot = sheetdoc.getElementsByTagName('svg')[0]

  cutdoc = DOM.parse(jobfile)
  cutroot = cutdoc.getElementsByTagName('svg')[0]

  # Add cuts to the material database
  for child in cutroot.childNodes:
    if child.nodeType != child.TEXT_NODE:
      sheetroot.appendChild(child.cloneNode(True))

  updated_sheet = sheetdoc.toxml()
  updated_sheet = updated_sheet.replace(CUT_STYLE, HOLE_STYLE)

  matdb['materialsheets'][matname][sheetid] = updated_sheet

  with open(MAT_DB, 'w') as outfile:
    json.dump(matdb, outfile)
