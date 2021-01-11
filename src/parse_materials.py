import json
import os
import re
import sys

import xml.dom.minidom as DOM


# Add explicit values for some default attributes
# that Illustrator might not have written
def fix(shape):
  if shape.tagName == 'rect':
    if not shape.hasAttribute('x'):
      shape.setAttribute('x', '0')
    if not shape.hasAttribute('y'):
      shape.setAttribute('y', '0')

def parse(filename):
  svgs = {} # key = material name, value = list of svg sheets
  fillmappings = {} # key = fill color, value = material name
  materialinfo = {} # key = material name, value = dimensions
  
  dom = DOM.parse(filename)
  assert(len(dom.getElementsByTagName('svg')) == 1)
  svg = dom.getElementsByTagName('svg')[0]
  
  # Preprocess to fix missing attributes
  for rect in svg.getElementsByTagName('rect'):
    fix(rect)
  
  top_groups = [g for g in svg.getElementsByTagName('g') if g.parentNode == svg]
  materials = [g.getAttribute('data-name') for g in top_groups]
  
  for top_group in top_groups:
    matname = top_group.getAttribute('data-name')
    
    svg_sheets = []
    
    sheets = [rect for rect in top_group.getElementsByTagName('rect') if rect.parentNode == top_group]
    hole_groups = [g for g in top_group.getElementsByTagName('g') if g.parentNode == top_group]

    assert(len(sheets) >= 1)
    if (len(hole_groups) == 0):
      print(matname)
    # assert(len(hole_groups) >= 1)
    # assert(len(sheets) == len(hole_groups))
    
    colour = re.search('fill:#(?:[0-9a-fA-F]{3}){1,2}', sheets[0].getAttribute('style'))
    assert(colour is not None)
    colour = colour.group(0).lower()
    fillmappings[colour] = matname
    
    width = sheets[0].getAttribute('width')
    height = sheets[0].getAttribute('height')
    materialinfo[matname] = {'width': width, 'height':height, 'viewBox':'0 0 {} {}'.format(width, height)}
    
    sheets.sort(key = lambda x : x.getAttribute('id'))
    hole_groups.sort(key = lambda x : x.getAttribute('id'))
    
    # NOTE: for each material name, it is assumed that either all sheets have holes in them or no sheets have holes in them

    # handle the case for sheets with holes
    if len(hole_groups) >= 1:
      assert(len(sheets) == len(hole_groups))
      for sheet, hole_group in zip(sheets, hole_groups):
        x_offset = float(sheet.getAttribute('x'))
        y_offset = float(sheet.getAttribute('y'))
        
        new_sheet = svg.cloneNode(False)
        new_sheet.setAttribute('width', width)
        new_sheet.setAttribute('height', height)
        new_sheet.setAttribute('viewBox', '0 0 {} {}'.format(width, height))
        
        for hole in hole_group.childNodes:
          if hole.nodeType != hole.TEXT_NODE:
            new_hole = hole.cloneNode(False)
            new_transform = 'translate({} {}) '.format(-x_offset, -y_offset) + new_hole.getAttribute('transform')
            new_hole.setAttribute('transform', new_transform)
            new_sheet.appendChild(new_hole)
            
        svg_sheets.append(new_sheet)

    # handle the case for sheets with no holes in them
    else:
      for sheet in sheets:
        new_sheet = svg.cloneNode(False)
        new_sheet.setAttribute('width', width)
        new_sheet.setAttribute('height', height)
        new_sheet.setAttribute('viewBox', '0 0 {} {}'.format(width, height))
        svg_sheets.append(new_sheet)
    
    svgs[matname] = svg_sheets
  return fillmappings, materialinfo, svgs

# Output all of the SVG files to the directory 'matdb'
def output(svgs):  
  for matname, sheets in svgs.items():
    for i, sheet in enumerate(sheets):
      with open('matdb/{}-{}.svg'.format(matname,i), 'w') as f_out:
        f_out.write(sheet.toxml())

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print('Required argument: filename')
  filename = sys.argv[1]
  fillmappings, materialinfo, svgs = parse(filename)
  
