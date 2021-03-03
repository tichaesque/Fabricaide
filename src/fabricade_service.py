# Local server that services the backend of the Fabricade UI
#
# Exposes the following REST API:
#
# Process the given SVG document and create the packed outputs
#   /process?svgfile=<svg file name>
# Check whether a process job has completed and new data is available
#   /check_refresh
# Execute the given laser cutter job:
#   /lasercut?jobfile=<job file>&matname=<material name>
# Check whether the laser cutter job has finished
#   /check_lasercut
# Update the material database with the cutouts from the given job
#   /update_material_database?jobfile=<job file>&matname=<material name>&sheetid=<ID of sheet>
# Generate the thumbnails for the material database
#   /generate_thumbnails
# Open the given file
#   /open_file?svgfile=<svg file name>
# Return a list of similar materials for a given material
#   /get_similar_materials?matname=<material name>
# Turn off the server
#   /shutdown
#
# See individual functions for more information.

from cairosvg import svg2png, svg2pdf
# from RemoteLaserCutter.Client.remote_laser import RemoteLaserCutter

import argparse
import glob
import json
import os
import signal
import shutil
import threading
import time
import intellipack
import xml.dom.minidom as DOM

import fabricade_svgutils
import fabricade_packing
import fabricaide_contours

from flask import Flask, flash, request, redirect, url_for, session, send_file

# Directories
PACKED_PREVIEW_DIR = 'FabricaideUI/data/packed/'
PACKED_OUTPUT_DIR = 'cuts/'
EXPORTED_FILES_DIR = 'fabricaide_files/'
PLACEHOLDER_FILES_DIR = 'FabricaideUI/data/placeholder/'

MAT_DB = 'mat-data.txt'   # Material availability data

# Configure the service as a webserver hosting a REST API
app = Flask(__name__)
args = None

# Persistent data needed across multiple requests
remoteLaser = None                                  # Remove laser cutting interface
currentlyPacking = False                            # True if a job is being packed
packingProcess = fabricade_packing.PackingJob()     # The packing procedure (runs asynchronously)

UPLOAD_FORM = """
  <form class="addmaterial" action="/register" name="registerform-MATNAME" id="registerform-MATNAME" method="post" enctype="multipart/form-data">
    <div id="loader-button" class="upload-btn-wrapper">
      <button class="add-material">
        <span>+</span> 
      </button>
      <input type="file" name="newsheet-MATNAME" id="newsheet-MATNAME" />
      <input type="hidden" name="matname" value="MATNAME" />
    </div>
  </form>
  
  <script type="text/javascript">
    $( document ).ready(function() {
      $("#newsheet-MATNAME").change(function(e) {
        $('#registerform-MATNAME').submit();  
      });
    });
  </script>


"""

PHOTO_PAGE = """
<h2> Adding {0}.</h2>
<p> Click on a point in the material sheet. </p>

  <div class="uploaded-img">
  <a href="/register"> <img src="/sheetphoto?{1}" ismap> </a>
  </div> 


  <a class="cancel-button" id="cancel-button" href="/materials" onclick="return confirm('Are you sure you want to cancel?')" >Cancel</a>
  </form>
  

"""

REGISTER_PAGE = """
  <form action="/registerdone" name="registerdoneform" id="registerdoneform" method="post" enctype="multipart/form-data">
  <input type="hidden" id="newsheet" name="newsheet" value='{0}'>
  
<h2> Adding {1}.</h2>
<p> Press confirm if the sheet looks correct. </p>

  <div class="instruction-img">
  {0}
  </div> 

  <button class="btn">
        <span>Confirm</span> 
  </button>

  <a class="cancel-button" id="cancel-button" href="/materials" onclick="return confirm('Are you sure you want to cancel?')" >Cancel</a>
  </form>
  

"""

# Process the given SVG file and create the packed
# output of all of the shapes that it contains
#
# args:
#  svgfile: The filename of the SVG file
#  copies: The number of copies that should be packed
# Returns: OK
@app.route('/process', methods=['GET'])
def process():
  global packingProcess
  global currentlyPacking
  
  svgfile = request.args.get('svgfile')
  copies = int(request.args.get('copies'))
  print(copies)
  
  # read illustrator svg file and call packing
  with open(svgfile, 'r') as myfile:
    fabricaidedoc = myfile.read().strip()

  # Remove old packed files
  if (os.path.exists(PACKED_PREVIEW_DIR)):
    shutil.rmtree(PACKED_PREVIEW_DIR)
  os.mkdir(PACKED_PREVIEW_DIR)

  # Execute packing
  packingProcess.loadFile(svgfile, copies)
  
  print('packing...')
  packingProcess.packAsync() # start the packing process
  currentlyPacking = True
      
  return 'OK'

# Compute the maximum number of copies of the given design
# that can be packed onto the available material
#
# args:
#  svgfile: The filename of the SVG file
# Returns: A JSON string consisting of an integral field, maxcopies
@app.route('/maxcopies', methods=['GET'])
def maxcopies():
  svgfile = request.args.get('svgfile')
  
  # read illustrator svg file and call packing
  with open(svgfile, 'r') as myfile:
    fabricaidedoc = myfile.read().strip()

  # Remove old packed files
  if (os.path.exists(PACKED_PREVIEW_DIR)):
    shutil.rmtree(PACKED_PREVIEW_DIR)
  os.mkdir(PACKED_PREVIEW_DIR)

  # Execute packing
  print('Starting maxcopies computation. This might take a while...')
  answer = packingProcess.computeMaxCopies(svgfile)
  print('Finished maxcopies computation.')
  return json.dumps({'maxcopies': answer})


# Return a page containing 'content' surrounded by the header and footer
def make_content(content):
  return open('header.inc', 'r').read() +  content + open('footer.inc', 'r').read()

@app.route('/materials', methods=['GET'])
def serve_mat_db():
  with open(MAT_DB, 'r') as file:
    materialsdb = json.load(file)
  materialcolour = {v:k for k,v in materialsdb['fillmappings'].items()}
    
  content = '<h1>Materials Database</h1>'  
    
  for material in materialsdb['materialinfo'].keys():
    content += '<h2>{}</h2>'.format(material)
    content += UPLOAD_FORM.replace('MATNAME', material)

    if material in materialsdb['materialsheets']:
      sheets = materialsdb['materialsheets'][material]
      content += '<div class="sheets">'
      for sheet in sheets:
        content += colorize(sheet, material, materialsdb, materialcolour)
      content += '</div>'
    else:
      content += '<p> No sheets registered for {} </p>'.format(material)

  return make_content(content)

# Colors the sheet with its corresponding color and fills the holes in white
def colorize(sheetString, matname, materialsdb, materialcolour):
  dom = DOM.parseString(sheetString)
  for child in dom.childNodes:
    if child.nodeType != child.TEXT_NODE and child.tagName != 'svg':
      dom.removeChild(child)
  svgroot = dom.getElementsByTagName('svg')[0]
  children = [child for child in svgroot.childNodes]
  for child in children:
    svgroot.removeChild(child)
  rect = dom.createElement('rect')
  rect.setAttribute('x', '0')
  rect.setAttribute('y', '0')
  rect.setAttribute('style', materialcolour[matname])
  _, _, width, height = materialsdb['materialinfo'][matname]['viewBox'].split(' ')
  rect.setAttribute('width', width)
  rect.setAttribute('height', height)
  svgroot.appendChild(rect)
  for child in children:
    if child.nodeType != child.TEXT_NODE:
      child.setAttribute('style', 'fill:#FFF')
    svgroot.appendChild(child)
  return dom.toxml()


# Calculate supply levels for a given material
#
# args:
#  matname: The name of the material to calculate the supply levels from
# returns: A JSON string consisting of
#  usage (float list) : A list of percentage usage for each sheet. The first percentage is the total usage across all sheets
@app.route('/get_supply_levels', methods=['GET'])
def get_supply_levels():
  global packingProcess
  matname = request.args.get('matname')
  packingProcess.calculateSupplyLevels(matname)
  return json.dumps(
      {
        'usage': packingProcess.percentages[matname]
      }
    )

# Generates the png preview for a sheet
#
# args:
#  material: material name
#  sheetid: sheet id
# returns: OK
@app.route('/convert_to_png', methods=['GET'])
def convert_to_png():
  material = request.args.get('material')
  sheetid = request.args.get('sheetid')

  pngout = os.path.join(PACKED_PREVIEW_DIR, material+'_'+str(sheetid)+'.png')
  svg2png(url='cuts/'+material+'_'+sheetid+'.svg', write_to=pngout)
  return 'OK'

# Send the given job to the laser cutter
#
# args:
#  jobfile: The filename of the job to process
#  matname: The name of the material to cut the job from
# Returns: OK
# @app.route('/lasercut', methods=['GET'])
# def lasercut():
#   global remoteLaser
#   jobfile = request.args.get('jobfile')
#   matname = request.args.get('matname')
#   print('Starting a new cutting job: {} ({})'.format(jobfile, matname))
#   preparedFile = fabricade_svgutils.prepareForCutting(jobfile)
#   remoteLaser = RemoteLaserCutter(args.laser_host)
#   assert remoteLaser.ping()
#   remoteLaser.cutJob(preparedFile, matname)
#   return 'OK'


# Export the given SVG file as PDF files that can be laser cut
#
# args: 
#   folder: folder that the exported files will be saved in
# Returns: OK
@app.route('/export_cuttable_file', methods=['GET'])
def export_cuttable_file():
  path_to_folder = PLACEHOLDER_FILES_DIR
  if (os.path.exists(os.path.join(path_to_folder, EXPORTED_FILES_DIR))):
    shutil.rmtree(os.path.join(path_to_folder, EXPORTED_FILES_DIR))
  os.mkdir(os.path.join(path_to_folder, EXPORTED_FILES_DIR))

  for packedpngfile in os.listdir(PACKED_PREVIEW_DIR):
    packedfile = PACKED_OUTPUT_DIR +packedpngfile[:-4] + '.svg'
    preparedFile = fabricade_svgutils.prepareForCutting(packedfile)

    svgout = os.path.join(path_to_folder, EXPORTED_FILES_DIR, preparedFile[5:])
    shutil.copy(preparedFile, svgout)

  return 'OK'

# Check whether the previous laser cutting job has finished
#
# args: None
# returns: True if the job is done, False otherwise
@app.route('/check_lasercut', methods=['GET'])
def check_lasercut():
  global remoteLaser
  if not remoteLaser.jobRunning():
    print('The current cutting job has ended')
    return 'True'
  else:
    return 'False'

# Check whether the UI should be refreshed because
# packing has completed and new material data has
# become available
#
# args: None
# returns: A JSON string consisting of
#  refresh (bool): True if a refresh is required
#  usage (string -> float list) : A map from materials to percentage usage for each sheet. The first percentage is the total usage across all sheets
#  insufficient (string list): A list of materials for which not all shapes could be packed
#
# The second two will be absent if refresh is False
@app.route('/check_refresh', methods=['GET'])
def check_refresh():
  global packingProcess
  global currentlyPacking
  if currentlyPacking and packingProcess.packingIsDone():
    currentlyPacking = False
    return json.dumps(
      {
        'refresh': True,
        'usage': packingProcess.percentages,
        'insufficient': packingProcess.insufficientmaterials,
        'crashed': packingProcess.crashedmaterials,
        'failed_fits': packingProcess.failed_fits
      }
    )
  else:
    return json.dumps({'refresh': False})

# Update the material database with the given job file
#
# args:
#  jobfile: The filename of the job to process
#  matname: The name of the material to cut the job from
#  sheetid: The ID of the sheet that was cut from
# returns: OK
@app.route('/update_material_database', methods=['GET'])
def update_material_database():
  jobfile = request.args.get('jobfile')
  matname = request.args.get('matname')
  sheetid = int(request.args.get('sheetid'))

  # Update the material database with new holes
  print('Updating the material database with new holes')
  preparedFile = fabricade_svgutils.prepareForCutting(jobfile)
  fabricade_svgutils.updateMaterialHoles(preparedFile, matname, sheetid)
  
  return 'OK'

# Reset the cuts dictionary to force repacking
@app.route('/reset_cache', methods=['GET'])
def reset_cache():
  packingProcess.reset_cache()
  return 'OK'

# Generate all of the thumbnail images for the material
# database.
#
# Arguments: None
# Returns: OK
@app.route('/generate_thumbnails', methods=['GET'])
def generate_thumbnails():
  fabricade_svgutils.generateThumbnails()
  return 'OK'

# Add an SVG group that displays the holes in a sheet
# to the given packed SVG file.
#
# args:
#   svgfile: The packed SVG file to add the holes to
#   matname: The name of the material sheet
#   sheetid: The id of the sheet whose holes we should display
#
# returns: OK
@app.route('/add_holes_to_cut_file', methods=['GET'])
def add_holes_to_cut_file():
  svgfile = request.args.get('svgfile')
  matname = request.args.get('matname')
  sheetid = int(request.args.get('sheetid'))
  fabricade_svgutils.addHolesToSVG(svgfile, matname, sheetid)
  return 'OK'

# Removes the SVG group that displays the holes in a sheet
# in the given packed SVG file.
#
# args:
#   svgfile: The packed SVG file to remove the holes from
#
# returns: OK
@app.route('/remove_holes_from_cut_file', methods=['GET'])
def remove_holes_from_cut_file():
  svgfile = request.args.get('svgfile')
  fabricade_svgutils.removeHolesFromSVG(svgfile)
  return 'OK'

# Open the given SVG file in Adobe Illustrator
#
# args:
#  svgfile: The name of the SVG file to open
@app.route('/open_file', methods=['GET'])
def open_file():
  svgfile = request.args.get('svgfile')
  os.system('open {}'.format(svgfile))
  return 'OK'

# Return a list of similar materials
#
# args:
#  matname: The baseline material
#
# Returns: A JSON string consisting of
#   substitutes (string list): A list of of substitute material names
@app.route('/get_similar_materials', methods=['GET'])
def get_similar_materials():
  with open(MAT_DB, 'r') as infile:
    matdb = json.load(infile)
  matname = request.args.get('matname')
  mat_thickness = matname.split('-')[0]
  mat_color = matname.split('-')[1]

  colorsubs = []
  thicknesssubs = []
  for material in matdb['materialinfo'].keys():
    if material != matname:
      if len(thicknesssubs) < 2 and material.split('-')[0] == mat_thickness:
        thicknesssubs.append(material)
      elif len(colorsubs) < 2 and material.split('-')[1] == mat_color:
        colorsubs.append(material)

  subs = colorsubs+thicknesssubs
  return json.dumps({"substitutes": subs})

@app.route('/sheetphoto', methods=['GET'])
def sheetphoto():
  
  return send_file('sheetphoto.jpg', mimetype='image/jpeg')

# Upload a new material
@app.route('/register', methods=['GET','POST'])
def register_material():
  global registration_material

  if request.method == 'POST':

    registration_material = request.form.get('matname')
    filefield = 'newsheet-{}'.format(registration_material)

    if filefield not in request.files: 
      return 'Error: No file provided'

    file = request.files[filefield] 

    if not (file.filename.lower().endswith('.jpg') or file.filename.lower().endswith('.jpeg')):
      return 'Invalid file type: Must be jpg.'

    else: 
      file.save('sheetphoto.jpg')
      return make_content(PHOTO_PAGE.format(registration_material, time.time())) 

  else:
    x,y = map(int, list(request.args.keys())[0].split(','))
    newsheet = fabricaide_contours.extractContours('sheetphoto.jpg', x,y)

    return make_content(REGISTER_PAGE.format(newsheet,registration_material)) 

# Confirm registering a new material
@app.route('/registerdone', methods=['POST'])
def register_done():
  global registration_material

  with open(MAT_DB, 'r') as file:
    materialsdb = json.load(file) 

  newmatname = registration_material
  newsheet = request.form.get('newsheet')
  
  # Scale the material sheet to the correct dimensions
  def scale_elements(element):
    if element.nodeType == element.TEXT_NODE:
      return

    if element.tagName == 'svg' or element.tagName == 'g':
      for child in element.childNodes:
        scale_elements(child)
    elif element.tagName in ['circle', 'ellipse', 'line', 'polyline', 'polygon', 'rect', 'path']:
      element.setAttribute('transform', ' scale({} {}) '.format(scale_width, scale_height) + element.getAttribute('transform'))
  
  dom = DOM.parseString(newsheet)
  svgroot = dom.getElementsByTagName('svg')[0]
  
  svgwidth = int(svgroot.getAttribute('width'))
  svgheight = int(svgroot.getAttribute('height'))
  
  viewbox = materialsdb['materialinfo'][newmatname]['viewBox']
  _, _, correct_width, correct_height = map(int, viewbox.split(' '))
  
  scale_width = correct_width / svgwidth
  scale_height = correct_height / svgheight
  
  scale_elements(svgroot)
  
  for attr in ['width', 'height', 'viewBox']:
    svgroot.setAttribute(attr, materialsdb['materialinfo'][newmatname][attr])
  
  materialsdb['materialsheets'][newmatname].insert(0, dom.toxml()) 

  with open(MAT_DB, 'w') as outfile:
    json.dump(materialsdb, outfile)

  return redirect(url_for('serve_mat_db'))


# Turn off the server
#
# args: None
@app.route('/shutdown', methods=['GET'])
def shutdown():
  threading.Thread(target=kill, args=(os.getpid(),)).start()
  return 'OK'

# Kill the host process in one second
def kill(pid):
  time.sleep(1)
  os.kill(pid, signal.SIGKILL)

if __name__ == "__main__":
  argparser = argparse.ArgumentParser()
  argparser.add_argument('--laser-host', dest='laser_host', default='http://127.0.0.1:8000', help='Remote hostname of laser cutter')
  argparser.add_argument('--port', dest='port', default=3000, type=int, help='Port to serve the local service on')
  args = argparser.parse_args()

  # Test if the laser cutter server is running
  # remoteLaser = RemoteLaserCutter(args.laser_host)
  # if remoteLaser.ping() is not True:
  #   print('\033[31m  ** Warning: Laser cutter server is not reachable ** \033[0m')
  
  # Run the flask application locally. This server should never serve to the outside world
  app.run(host='127.0.0.1', port=args.port)

