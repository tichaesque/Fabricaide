# Processes packing jobs.
#
# Optimizes packing jobs by reusing the most recent packing for a particular
# material if no modifications have been made to that material.

import itertools
import glob
import packaide
import json
import os
import re
import shapely.geometry
import shutil
import threading
import time
import traceback
import xml.dom.minidom as DOM

from cairosvg import svg2png

USE_3D = False

__MAT_DB_UI__ = 'FabricaideUI/data/matdb'
__MAT_DB__ = 'mat-data.txt'
__COLOR_DB__ = 'colordict2.json'
__NO_FILL__ = 'fill:none'
__CUT_STYLE__ = 'fill:none;stroke:red;stroke-miterlimit:10;stroke-width:0.0001px'
__COLOR_STYLE__ = '{};stroke:none'

PACKED_PREVIEW_DIR = 'FabricaideUI/data/packed'
PACKED_OUTPUT_DIR = 'cuts'

class PackingJob:
  def __init__(self):
    # Objects with colours not corresponding to any material in
    # the database will default to this material instead
    self.defaultmat = '0.1mm-white-letterpaper'

    # dictionary that associates a shape with its slots (3D only)
    self.slots = {}
  
    # Material availability and colour mappings  
    with open(__MAT_DB__, 'r') as file:
      self.materialsdb = json.load(file)
    with open(__COLOR_DB__, 'r') as file:
      self.colorsdb = json.load(file)

    # Mapping from colours to material names
    self.materialcolour = {v:k for k,v in self.materialsdb['fillmappings'].items()}
  
    # Parts in the design file are split by material assignment
    self.materials = []
    self.materialcuts = {}
    self.reuse_materials = []
    self.packingresults = {}
  
    # Auxiliary data produced by packing
    self.insufficientmaterials = []
    self.crashedmaterials = []
    self.failed_fits = {} # number of failed fits per insufficient material
    self.percentages = {}
  
  # Load an SVG file to prepare for a packing job
  def loadFile(self, filename, copies):
    self.filename = filename
  
    # Reload the material database incase something
    # has changed (new holes added etc.)  
    with open(__MAT_DB__, 'r') as file:
      self.materialsdb = json.load(file)

    # Design and material information
    if USE_3D: 
      self.svginput = self.flattenSVGLayers3D(copies)
    else:
      self.svginput = self.flattenSVGLayers(copies)

    new_materialcuts = self.splitMaterials()
    new_materials = list(new_materialcuts.keys())
    
    # Re-use old packing if the parts for a material have not changed
    self.reuse_materials = []
    for material in self.materials:
      if material in new_materials:
        if self.materialcuts[material].toxml() == new_materialcuts[material].toxml():
          self.reuse_materials.append(material)
    
    self.materials = new_materials
    self.materialcuts = new_materialcuts
  
  # Returns true if n copies of the given SVG file can fit onto the
  # currently available materials
  def canFitNCopies(self, filename, copies):
    self.loadFile(filename, copies)
    self.doPacking()
    return len(self.insufficientmaterials) == 0
  
  # Compute the maximum number of copies of the contents of the given
  # SVG files that can fit onto the currently available materials
  def computeMaxCopies(self, filename):
    lo = 0
    hi = 1
    while (self.canFitNCopies(filename, hi)):
      hi *= 2
    while lo < hi - 1:
      mid = lo + (hi - lo) // 2
      if (self.canFitNCopies(filename, mid)):
        lo = mid
      else:
        hi = mid
    return lo
  
  # Run the packing asynchronously
  def packAsync(self):
    # Initiate packing in a new thread
    self.packingJob = threading.Thread(target=lambda : self.doPacking())
    self.packingJob.start()
  
  # Return True if the most recent asynchronous packing job has finished
  def packingIsDone(self):
    return not self.packingJob.is_alive()

  # Return the available area for a given material as a percentage
  def calculateSupplyLevels(self, material):
    svgsheetlist = self.materialsdb['materialsheets'][material]
    packedfiles = []
    for idx,packedfile in enumerate(sorted(glob.glob(PACKED_OUTPUT_DIR+"/*.svg"))):
      packedfile = os.path.basename(packedfile)
      matname, matid = packedfile[:-4].split('_')
      if matname == material:
        with open(os.path.join(PACKED_OUTPUT_DIR,packedfile) , 'r') as packedshapes:
          packedfiles.append((0, packedshapes.read()))

    merged_sheets = self.merge_sheets(svgsheetlist, packedfiles)
    self.percentages[material] = self.sheet_percentage(merged_sheets)
    return self.percentages[material]
  
  def reset_cache(self):
    self.materialcuts = {}
    self.materials = []

  # Take the output of the packing, and the input sheets, and produce a sequence of
  # documents that contains the original sheets with holes with the newly packed
  # shapes placed onto them
  def merge_sheets(self, svg_files, packing_output):
    sheets = []
    for i in range(len(svg_files)):
      doc = DOM.parseString(svg_files[i])
      if i < len(packing_output):
        packed_shapes = DOM.parseString(packing_output[i][1])
        svgElement = doc.getElementsByTagName('svg')[0]
        for element in packed_shapes.getElementsByTagName('svg')[0].childNodes:
          if element.nodeType != element.TEXT_NODE and (element.tagName == 'g' or element.tagName == 'path'):
            svgElement.appendChild(element.cloneNode(deep=True))
      sheets.append(doc)
    return sheets

  #SVG files should ideally be file names
  def sheet_percentage(self, svg_files, offset = 20):
    consumed_area = 0
    total_area = 0
    sheet_consumption= []
    for svg_file in svg_files:
      svg_string = svg_file.toxml()
      height, width = packaide.get_sheet_dimensions(svg_string)
      boundary = shapely.geometry.Polygon([(0,0),(width,0),(height,width),(0, height)])
      total_area += boundary.area
      elements, shapely_polygons = packaide.extract_shapely_polygons(svg_string, offset)
      if len(shapely_polygons) > 0:
        polygons, holes_list = zip(*shapely_polygons)
        union = shapely.ops.unary_union(polygons)
        holes = list(itertools.chain(*holes_list))
        hole_union = shapely.ops.unary_union(holes)
        unbounded_consume = union.difference(hole_union)
        consumed = boundary.intersection(unbounded_consume)
        consumed_area += consumed.area
        sheet_consumption.append(consumed.area/ boundary.area)
      else:
        consumed_area += 0
        sheet_consumption.append(0)
    return [consumed_area/total_area] + sheet_consumption

  # Run the packing procedure for all materials. This should usually
  # be called from a new thread to avoid blocking the caller, since
  # packing could take a while... See packAsync().
  def doPacking(self):
    self.packingSuccess = True
    self.missingMaterials = []
    self.packedFiles = []
    old_insufficients = self.insufficientmaterials
    self.insufficientmaterials = []
    old_crashes = self.crashedmaterials
    self.crashedmaterials = []

    for material in self.materials:
      shapestopack = self.materialcuts[material]
      svgsheetlist = self.materialsdb['materialsheets'][material]
      
      if material in self.reuse_materials:
        # Reuse the previous packing -- NOTE: We reload the packed SVG file from disk rather
        # than reusing the stored file since the user may have manually editting the packing,
        # and we would like to keep it if this is the case
        print('[Packing] Reusing previous packing for {} since it has not changed'.format(material))
        
        if material in old_crashes:
          self.crashedmaterials.append(material)
          continue

        # This happens when the packing failed last time and the design has not changed
        if material in old_insufficients:
          self.insufficientmaterials.append(material)

          for sheetid, shapes in self.packingresults[material]:
            # Output packed SVG files
            svg_output = os.path.join(PACKED_OUTPUT_DIR, '{}_{}.svg'.format(material, sheetid))

            with open(svg_output, 'w') as cutfile:
              cutfile.write(shapes.toxml())

            # Generate PNG preview
            self.generatePNGPreview(svg_output, material, sheetid)
            
          continue

        for sheetid, _ in self.packingresults[material]:
          svg_output = os.path.join(PACKED_OUTPUT_DIR, '{}_{}.svg'.format(material, sheetid))
          self.generatePNGPreview(svg_output, material, sheetid)
          
      else: 
        try: 
          # Execute the packing algorithm
          print('[Packing] Running the packing algorithm on {}'.format(material))
          
          start = time.time()
          self.packingresults[material], success_fits, num_failed_fits = packaide.pack(svgsheetlist, shapestopack.toxml(), tolerance=5, offset=10, partial_solution=True, rotations=2)

          if num_failed_fits > 0:
            self.failed_fits[material] = num_failed_fits
            self.insufficientmaterials.append(material)

          start = time.time()
          merged_sheets = self.merge_sheets(svgsheetlist, self.packingresults[material])
          self.percentages[material] = self.sheet_percentage(merged_sheets)
          
          # remove old packed files for this material
          old_packed_files = glob.glob(PACKED_OUTPUT_DIR + '/' + material+"*.svg")
          for old_file in old_packed_files:
            os.remove(old_file)

          # (3D only) add the slots back into the packing 
          if USE_3D:
            self.placeSlots(material)

          # Output each packed sheet
          for sheetid, shapes in self.packingresults[material]:
            # Output packed SVG files
            svg_output = os.path.join(PACKED_OUTPUT_DIR, '{}_{}.svg'.format(material, sheetid))

            with open(svg_output, 'w') as cutfile:
              cutfile.write(shapes)

            # Generate PNG preview
            start = time.time()
            self.generatePNGPreview(svg_output, material, sheetid)
            print('gen PNG: ' + str(time.time()-start))
            
        # Failure indicates that something bad happened
        except Exception as e:
          self.packingSuccess = False
          self.crashedmaterials.append(material)
          if material in self.packingresults:
            del self.packingresults[material]
            
          traceback.print_exc()
          print('Packing routine failed')
  
  def placeSlots(self, material):
    sheetlist = self.packingresults[material]
    newpackingresults = []

    for sheetid,sheetdoc in sheetlist:
      root = sheetdoc.getElementsByTagName('svg')[0]
      newroot = sheetdoc.getElementsByTagName('svg')[0]

      children = [child for child in root.childNodes]
      for child in children:
        shapeid = child.getAttribute('id')
        slotlist = self.slots[shapeid]
        for slot in slotlist:
          slot.setAttribute('transform', child.getAttribute('transform')) 

          newroot.appendChild(slot)

      newpackingresults.append((sheetid, newroot.cloneNode(True)))

    self.packingresults[material] = newpackingresults

  # Generate the PNG preview of the packed shapes in the given SVG file. The preview
  # contains the packed shapes as well as the existing holes on the given material sheet
  def generatePNGPreview(self, svgfile, material, sheetid):
    # PNG previews should show the holes and the newly packed shapes
    shapes = DOM.parse(svgfile)
    root = shapes.getElementsByTagName('svg')[0]
    children = [child for child in root.childNodes]
    outdom = DOM.parseString(self.materialsdb['materialsheets'][material][sheetid])
    outsvg = outdom.getElementsByTagName('svg')[0]
    for child in children:
      outsvg.appendChild(child)

    # Create packed PNG preview files
    if len(children) > 0:
      pngout = os.path.join(PACKED_PREVIEW_DIR, '{}_{}.png'.format(material, sheetid))
      svg2png(bytestring=outsvg.toxml(), write_to=pngout)
  
  # flattens layers in SVG file and removes title tag
  def flattenSVGLayers(self, copies):
    doc = DOM.parse(self.filename)
    svgroot = doc.getElementsByTagName('svg')[0]

    titles = svgroot.getElementsByTagName('title')
    for title in titles:
      svgroot.removeChild(title)

    layers = doc.getElementsByTagName('g')

    for layer in layers:
      children = [child for child in layer.childNodes]

      for child in children:
        child = layer.removeChild(child)
        svgroot.appendChild(child)

      svgroot.removeChild(layer)


    children = [child for child in svgroot.childNodes]

    for child in children:
      if child.nodeType == child.TEXT_NODE:
        svgroot.removeChild(child)

      else:
        for copy in range(copies-1):
          svgroot.appendChild(child.cloneNode(True))
    
    return svgroot
    
  # flattens layers in SVG file exported from flatfab/kyub
  def flattenSVGLayers3D(self, copies):
    doc = DOM.parse(self.filename)
    svgroot = doc.getElementsByTagName('svg')[0]

    titles = svgroot.getElementsByTagName('title')
    for title in titles:
      svgroot.removeChild(title)

    layers = doc.getElementsByTagName('g')

    for layer in layers:
      children = [child for child in layer.childNodes]

      slotparentID = ""
      for child in children:
        child = layer.removeChild(child)

        if child.nodeType != child.TEXT_NODE:
          childID = child.getAttribute('id')

          if not 'slot' in childID:
            svgroot.appendChild(child)
            # assumption: the non-slot part of the shape should come 
            # before the slots in the SVG file...
            slotparentID = childID
            self.slots[slotparentID] = []
          else:
            # should be list in case shape has multiple slots
            self.slots[slotparentID].append(child) 

      svgroot.removeChild(layer)

    children = [child for child in svgroot.childNodes]

    # make copies
    for child in children:
      if child.nodeType == child.TEXT_NODE:
        svgroot.removeChild(child)

      else:
        for copy in range(copies-1):
          svgroot.appendChild(child.cloneNode(True))
    
    return svgroot

  # Given an SVG element, determine the material name
  # by inspecting the colour of its fill and looking
  # up the corresponding material in the database
  def getMaterialName(self, shape):
    # since FlatFab exports unfilled shapes
    if USE_3D:
      return self.defaultmat

    style = shape.getAttribute('style')
    r = re.search('fill:#(?:[0-9a-fA-F]{3}){1,2}', style)
    matname = None

    if r is not None:
      matname = self.defaultmat
      fill = r.group(0).lower()

      if fill in self.materialsdb['fillmappings']:
        matname = self.materialsdb['fillmappings'][fill]
    
    return matname

  # makes shallow clone of the root svg element
  def makeMaterialSheet(self):
    return self.svginput.cloneNode(False)

  # Add explicit values for some default attributes
  # that Illustrator might not have written
  def addMissingAttr(self,shape):
    if shape.tagName == 'rect':
      if not shape.hasAttribute('x'):
        shape.setAttribute('x', '0')
      if not shape.hasAttribute('y'):
        shape.setAttribute('y', '0')
    elif shape.tagName == 'circle' or shape.tagName == 'ellipse':
      if not shape.hasAttribute('cx'):
        shape.setAttribute('cx', '0')
      if not shape.hasAttribute('cy'):
        shape.setAttribute('cy', '0')

    return shape
  
  # Split the loaded SVG file up so that the different parts are
  # associated with their corresponding material
  def splitMaterials(self):
    materialcuts = {}

    for shape in self.svginput.childNodes:
      if shape.nodeType != shape.TEXT_NODE:
        matname = self.getMaterialName(shape)
        if matname == None:
          continue

        if matname not in materialcuts:
          materialcuts[matname] = self.makeMaterialSheet()

        shape = self.addMissingAttr(shape)
        color = self.colorsdb[matname]
        shape.setAttribute('style', __COLOR_STYLE__.format(color))

        materialcuts[matname].appendChild(shape.cloneNode(False))

    return materialcuts
    
