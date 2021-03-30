import controlP5.*;  //<>// //<>//
import java.util.Map;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import static java.nio.file.StandardCopyOption.REPLACE_EXISTING;

boolean use3D = false;
boolean debug = false; 
boolean processingfile = false;
boolean paused = false;

JobList joblist; // all the sheets that will be cut out

final int HOME = 0; 
final int REORDER = 1; 
final int CUTTING = 2;
final int EDITING = 3;
final int SCROLLING = 4;
final int OPTIONS = 5;

final String url = "";

int copies = 1;

int sheetheight = 80; 

int state = 0; 
int previousstate = 0; 

boolean reorderingSheet = false; // is the user trying to rearrange a sheet?

String selectedMaterialName = "";
String packedshapes_dir = "packed";
String matdb = "matdb";

Sheet selectedSheet = null; 
String selectedSheetName = "";
String editingFileName = "";

ControlP5 cp5;
ControlP5 toggles;
Button lasercutbutton;
Button exportbutton;
Button databasebutton;
Button backbutton;
Button nextbutton;
Toggle globutilToggle;
Toggle localutilToggle;
Toggle thumbToggle;
ControlFont font;
PFont receipt;

JSONObject colorsdict;
JSONObject percentages;

String fabricaidedocpath;
File fabricaidedocfile;
String[] cacheddoc;

String editedpackingdocpath;
File editedpackingdocfile;

Map<String, List<String>> insufficientmaterials;
Set<String> crashedMaterials; 
Map<String, Integer> failedFitsForMaterial; 

float jobListYOffset = 0; 
float scrollingMouseYStart = 0; 

int lastRefresh = 0; 

final float buttonPosition = 15; 

boolean showPacking = true;
boolean showGlobalUtilization = true;
boolean showLocalUtilization = true;
boolean showThumbnails = true;

AdobeIllustratorInteraction illustrator;

float UIpanelY; 

float packingstart = 0f;

String illustratorPath;

// For now, we assume that Illustrator is version 2020 and installed in the
// default location. If not, these paths will have to be modified.
String getIllustratorExecutable() {
  final String OS = platformNames[platform];
  String path = "";
  if ("macosx".equals(OS)) {
    path = "/Applications/Adobe Illustrator 2020/Adobe Illustrator.app";
  }
  else {
    // If not Mac, assume Windows since Illustrator doesn't support Linux
    path = "C:\\Program Files\\Adobe\\Adobe Illustrator 2020\\Support Files\\Contents\\Windows\\Illustrator.exe";
  }
  
  // If the default path is no good, the user should help us find Illustrator
  File f = new File(path);
  if (!f.exists()) {
    println("Could not find Illustrator in the default location. You will have to modify the Illustrator path in FabricaideUI.pde");
    exit();
    return null;
  }
  else {
    return path; 
  }
}

void locateIllustrator(File selection) {
  if  (selection == null) {
    illustratorPath = null; 
  }
  else {
    illustratorPath = selection.getAbsolutePath(); 
  }
}

void setup() {

  size(250, 500);
  surface.setAlwaysOnTop(true);
  pixelDensity(displayDensity());
  smooth();
  surface.setSize(250, int(0.95*displayHeight));

  UIpanelY = height-50;

  // Find and set up interaction with Adobe Illustrator
  illustrator = new AdobeIllustratorInteraction(getIllustratorExecutable());

  fabricaidedocpath = dataPath("../../fabricaidedoc.svg");
  editedpackingdocpath = dataPath("../../editedpacking.svg");

  insufficientmaterials = new TreeMap<String, List<String>>();
  failedFitsForMaterial = new TreeMap<String, Integer>();
  crashedMaterials = new TreeSet<String>();

  fabricaidedocfile = new File(fabricaidedocpath);
  editedpackingdocfile = new File(editedpackingdocpath);

  colorsdict = loadJSONObject("colordict.json");

  joblist = new JobList();

  surface.setTitle("Fabricaide");
  surface.setLocation(displayWidth-300, 0);

  textAlign(CENTER);

  cp5 = new ControlP5(this);
  toggles = new ControlP5(this);

  receipt = loadFont("FakeReceipt-Regular-48.vlw");
  textFont(receipt, 10);
  font = new ControlFont(receipt, 10);

  makeHomeButtons();

  toggles.addToggle("packingToggle")
    .setPosition(40, 100)
    .setSize(25, 25)
    .setState(true)
    .setColorBackground(color(120, 120, 120))
    .setColorActive(color(252, 186, 3))
    .setLabelVisible(false)
    ;

  globutilToggle = toggles.addToggle("globutilizationToggle")
    .setPosition(40, 140)
    .setSize(25, 25)
    .setState(true)
    .setColorBackground(color(120, 120, 120))
    .setColorActive(color(252, 186, 3))
    .setLabelVisible(false)
    ;

  localutilToggle = toggles.addToggle("localutilizationToggle")
    .setPosition(40, 180)
    .setSize(25, 25)
    .setState(true)
    .setColorBackground(color(120, 120, 120))
    .setColorActive(color(252, 186, 3))
    .setLabelVisible(false)
    ;

  thumbToggle = toggles.addToggle("thumbnailsToggle")
    .setPosition(40, 220)
    .setSize(25, 25)
    .setState(true)
    .setColorBackground(color(120, 120, 120))
    .setColorActive(color(252, 186, 3))
    .setLabelVisible(false)
    ;
    
  Textfield t = toggles.addTextfield("copies")
     .setText(str(copies))
     .setLabel("make copies:")
     .setPosition(117,20)
     .setSize(30,30)
     .setFont(createFont("Monaco",5.5))
     .setAutoClear(false)
     ;
     
  Label label = t.getCaptionLabel(); 
  label.align(ControlP5.LEFT_OUTSIDE, CENTER);
  label.getStyle().setPaddingLeft(-10);
  
  toggles.hide();

  if (!debug) loadStrings("http://127.0.0.1:3000/generate_thumbnails");

  layoutUI();
  state = HOME;
}   

public void makeHomeButtons() {
  databasebutton = cp5.addButton("matdb")
    .setLabel("database")
    .setFont(font)
    .setPosition(buttonPosition, height-40)
    .setSize(75, 30)
    .setColorBackground(color(55, 55, 55))
    .setColorForeground(color(252, 186, 3))
    ;

  exportbutton = cp5.addButton("exportPDF")
    .setLabel("export")
    .setFont(font)
    .setPosition(width*0.5, height-40)
    .setSize(60, 30)
    .setColorBackground(color(55, 55, 55))
    .setColorForeground(color(252, 186, 3))
    ;

  lasercutbutton = cp5.addButton("maxcopies")
    .setLabel("max")
    .setFont(font)
    .setPosition(exportbutton.getPosition()[0] + exportbutton.getWidth() + 10, height-40)
    .setSize(40, 30)
    .setColorBackground(color(55, 55, 55))
    .setColorForeground(color(252, 186, 3))
    ;
}

public void matdb(int theValue) {
  loadStrings("http://127.0.0.1:3000/materials");

  link("http://127.0.0.1:3000/materials");
}

public void exportPDF(int theValue) {
  selectFolder("Select a folder to process:", "folderSelected");
}


void folderSelected(File selection) {
  if (selection == null) {
    println("Window was closed or the user hit cancel.");
  } else {
    String outputFolder = selection.getAbsolutePath();
    loadStrings("http://127.0.0.1:3000/export_cuttable_file");

    try {
      if (Files.exists(Paths.get(outputFolder+ "/fabricaide_files/"))) {
        File[] old_export = listFiles(outputFolder+ "/fabricaide_files/");
        for (File f : old_export) {
          String fname = f.getName();
          Files.delete(Paths.get(outputFolder+ "/fabricaide_files/"+fname));
        }

        Files.delete(Paths.get(outputFolder+ "/fabricaide_files/"));
      }

      Files.move(Paths.get(dataPath("placeholder/fabricaide_files")), Paths.get(outputFolder+ "/fabricaide_files/"), REPLACE_EXISTING);
    } 
    catch (IOException e) {
      println("Could not export files");
      println(e);
    }

    // assume the user will cut the shapes out and update the material database
    File[] files = listFiles(outputFolder + "/fabricaide_files/");

    for (File f : files) {
      String jobname = f.getName();
      String matname = jobname.split("_")[0];
      String sheetId = jobname.split("_")[1].split("-")[0];
      String jobfile = "cuts/" + matname + "_" + sheetId + ".svg";
      loadStrings("http://127.0.0.1:3000/update_material_database?jobfile=" + jobfile + "&matname=" + matname + "&sheetid=" + sheetId);
    }

    loadStrings("http://127.0.0.1:3000/reset_cache");

    // refresh the sheet thumbnails
    loadStrings("http://127.0.0.1:3000/generate_thumbnails");
    cacheddoc = null;
  }
}

public void lasercut(int theValue) {
  materialqueue = new ArrayList(joblist.getJobs());
  surface.setTitle("Cut sheets");

  queueIdx = 0;
  selectedSheetIdx = 0; 

  state = CUTTING;

  backbutton = cp5.addButton("goback")
    .setLabel("cancel")
    .setFont(font)
    .setPosition(20, height-40)
    .setSize(50, 30)
    .setColorBackground(color(55, 55, 55))
    .setColorForeground(color(252, 186, 3))
    ;

  nextbutton = cp5.addButton("nextsheet")
    .setLabel("next")
    .setFont(font)
    .setPosition(exportbutton.getPosition()[0] + exportbutton.getWidth() + 10, height-40)
    .setSize(40, 30)
    .setColorBackground(color(55, 55, 55))
    .setColorForeground(color(252, 186, 3))
    ;

  lasercutbutton.remove();
  exportbutton.remove();
  databasebutton.remove();

  joblist.layout();
}

public void maxcopies(int theValue) {
  JSONObject response = loadJSONObject("http://127.0.0.1:3000/maxcopies?svgfile=cacheddoc.svg");
  int max_copies = response.getInt("maxcopies");

  print("Max copies is " + max_copies);

  if (max_copies > 0) {
    // Update the copies field to show the maximum number of copies
    copies = max_copies;
    toggles.get(Textfield.class, "copies").setText(str(copies));
    cacheddoc = null;  // Force a repacking
    
    surface.setTitle("Fabricaide ["+max_copies+" COPIES]");
  }
}

public void nextsheet(int theValue) {
  PrintWriter lasercutfile = createWriter(dataPath("../../.laserjob"));
  String cuttingMaterial = materialqueue.get(queueIdx);
  int sheetId = joblist.getContainer(cuttingMaterial).getSheetDataForSheet(selectedSheetIdx).getSheetID();
  String jobfile = "cuts/"+ cuttingMaterial + "_" + sheetId + ".svg";
  String matname = cuttingMaterial;

  loadStrings("http://127.0.0.1:3000/lasercut?jobfile=" + jobfile + "&matname=" + matname);
  String[] check_lasercut = loadStrings("http://127.0.0.1:3000/check_lasercut");

  println("starting cutting");
  while (check_lasercut[0].equals("False")) {
    check_lasercut = loadStrings("http://127.0.0.1:3000/check_lasercut");
    delay(500);
  }
  println("done cutting");
  loadStrings("http://127.0.0.1:3000/update_material_database?jobfile=" + jobfile + "&matname=" + matname + "&sheetid=" + sheetId);

  selectedSheetIdx++; 

  if (selectedSheetIdx >= joblist.getContainer(materialqueue.get(queueIdx)).numChildren()) {
    queueIdx++;
    selectedSheetIdx = 0;
  }

  if (queueIdx >= materialqueue.size()) {
    println("finished job"); 

    queueIdx = -1; 
    nextbutton.remove();
    cacheddoc = null;

    loadStrings("http://127.0.0.1:3000/reset_cache");
    loadStrings("http://127.0.0.1:3000/generate_thumbnails");

    return;
  }
}

public void goback(int theValue) {
  surface.setTitle("Fabricaide");
  resetVariables();
  backbutton.remove();

  makeHomeButtons();

  joblist.layout();
}

public void finishediting(int theValue) {
  illustrator.swapDocument(fabricaidedocpath);

  loadStrings("http://127.0.0.1:3000/remove_holes_from_cut_file?svgfile="+editingFileName);

  resetVariables();
  backbutton.remove();

  makeHomeButtons();

  showThumbnails = thumbToggle.getState();

  joblist.layout();
}

// this toggle affects the thumbnails + local utilization  because it doesn't make sense to show those without the previews
void packingToggle(boolean theFlag) {
  cursor(ARROW);
  if (theFlag != showPacking) {
    showPacking = theFlag;
    showLocalUtilization = showPacking;
    showThumbnails = showPacking; 

    localutilToggle.setState(theFlag);
    thumbToggle.setState(theFlag);

    if (!showPacking) {
      localutilToggle.lock();
      thumbToggle.lock();
    } else {
      localutilToggle.unlock();
      thumbToggle.unlock();
    }

    joblist.layout();
  }
}

void globutilizationToggle(boolean theFlag) {
  if (theFlag != showGlobalUtilization) {
    showGlobalUtilization = theFlag;
    joblist.layout();
  }
}

void localutilizationToggle(boolean theFlag) {
  if (theFlag != showLocalUtilization) {
    showLocalUtilization = theFlag;
    joblist.layout();
  }
}

void thumbnailsToggle(boolean theFlag) {
  if (theFlag != showThumbnails) {
    println("thumbnails toggle");
    showThumbnails = theFlag;
    joblist.layout();
  }
}

public static class FilenameComparator implements Comparator<File> {
  public int compare(File f1, File f2) {
    String s1 = f1.getName();
    String s2 = f2.getName();
    String matname1 = s1.split("_")[0]; 
    String matname2 = s2.split("_")[0];
    int id1 = int(s1.split("_")[1]);
    int id2 = int(s2.split("_")[1]);

    int comp = matname1.compareTo(matname2);
    if (comp != 0) return comp; 
    else return id1-id2;
  }
}

void layoutUI() {
  File[] files = listFiles(dataPath(packedshapes_dir));

  // ensures that the files are sorted such that
  // all materials are grouped by material name
  // all sheet ids are sorted in ascending order
  Arrays.sort(files, new FilenameComparator());

  for (File f : files) {
    String packedshapes = f.getName();
    if (packedshapes.length() < 1 || packedshapes.charAt(0) == '.') { 
      continue;
    }

    SheetData matsheet = new SheetData(packedshapes); 

    if (matsheet.getSheetColor() != -1) {
      Sheet newSheet = new Sheet(matsheet);
      String matname = matsheet.getMaterialName(); 

      if (joblist.hasMaterial(matname)) {
        SheetContainer cont = joblist.getContainer(matname);
        cont.addSheet(newSheet);
      } else {
        SheetContainer cont = new SheetContainer(matname);
        cont.addSheet(newSheet);
        joblist.addMaterial(cont);
      }
    }
  }

  for (String materialname : insufficientmaterials.keySet()) {
    if (!joblist.hasMaterial(materialname)) {
      SheetContainer cont = new SheetContainer(materialname);
      joblist.addMaterial(cont);
    }
  }

  for (String materialname : crashedMaterials) {
    if (!joblist.hasMaterial(materialname)) {
      SheetContainer cont = new SheetContainer(materialname);
      joblist.addMaterial(cont);
    }
  }

  joblist.layout();
}

void mouseMoved() { 
  if (state == HOME) {
    joblist.updateMouseOver();
    joblist.updateSelectedMaterial();
  }

  if (state == HOME && selectedSheet != null) {
    cursor(HAND);
  } else {
    cursor(ARROW);
  }
}

void mousePressed() {
  if (state == HOME && selectedSheet == null && joblist.getHeight() >= height) {
    state = SCROLLING;
    scrollingMouseYStart = mouseY;
  }
}

void mouseDragged() {
  if (state == REORDER && selectedSheet != null) {
    reorderingSheet = true;
  } else if (state == SCROLLING) {
    jobListYOffset = mouseY - scrollingMouseYStart; 
    float joblistnewY = jobListYOffset + joblist.getY();

    joblistnewY = constrain(joblistnewY, height-joblist.getHeight() - 50, 0);

    joblist.setY(joblistnewY);
    joblist.layout();

    scrollingMouseYStart = mouseY;
  }
}

void mouseReleased() {
  if (state ==  HOME && selectedSheet != null) {
    editingFileName = "cuts/"+selectedSheet.getSheetData().getMaterialName() + "_" + selectedSheet.getSheetData().getSheetID() + ".svg";

    if (!debug) {
      loadStrings("http://127.0.0.1:3000/add_holes_to_cut_file?svgfile="+editingFileName + "&matname=" + selectedSheet.getSheetData().getMaterialName() + "&sheetid=" + selectedSheet.getSheetData().getSheetID());
      illustrator.swapDocument(dataPath("../../"+editingFileName));

      delay(2000); // need to give illustrator a few seconds to open the file before saving it again
    }

    illustrator.exportCurrentDocument(editedpackingdocpath);

    String[] editedpackingdoc = loadStrings(editedpackingdocpath);

    PrintWriter materialsheetfile = createWriter(dataPath("../../"+editingFileName));
    for (String line : editedpackingdoc) {
      materialsheetfile.println(line);
    }
    materialsheetfile.flush();
    materialsheetfile.close();

    cacheddoc = editedpackingdoc;

    state = EDITING; 
    showThumbnails = false;

    lasercutbutton.remove();
    exportbutton.remove();
    databasebutton.remove();

    backbutton = cp5.addButton("finishediting")
      .setLabel("done editing")
      .setFont(font)
      .setPosition(20, height-40)
      .setSize(120, 30)
      .setColorBackground(color(55, 55, 55))
      .setColorForeground(color(252, 186, 3))
      ;
  } else if (state == REORDER && selectedSheet != null) {
    println("dropped: "+selectedSheet.getSheetData().getSheetID());
    return;
  } else if (state == SCROLLING) {
    state = HOME;
  }
}

void resetVariables() {

  if (nextbutton != null) nextbutton.remove();

  state = HOME; 
  reorderingSheet = false; 

  selectedMaterialName = "";

  selectedSheetIdx = -1;
  queueIdx = 0; 

  selectedSheet = null; 
  selectedSheetName = "";
}

void drawInterfacePanels() {
  fill(100);
  noStroke();
  rect(0, height-50, width, 50);
  strokeWeight(1);
  stroke(150);
  line(buttonPosition, height-50, width-15, height-50);
}

void keyReleased() {
  if (key == 'o') {
    if (state != OPTIONS) { // user is opening up the options menu
      previousstate = state;
      state = OPTIONS;

      toggles.show();
    } else { // user is closing the options menu
      copies = int(toggles.get(Textfield.class,"copies").getText());
    
      state = previousstate;
      toggles.hide();
      
    }
    
  } else if (!processingfile && key == 'p') {
    paused = !paused;
    if (paused) surface.setTitle("[PAUSED] Fabricaide");
    else surface.setTitle("Fabricaide");
  } else if (!use3D && !processingfile && key == 'r') {
    fabricaidedocfile.delete();
    illustrator.exportCurrentDocument(fabricaidedocpath);
    while (!fabricaidedocfile.exists()) { 
      delay(500);
    }

    String[] fabricaidedoc = loadStrings(fabricaidedocpath);

    // request to repack unless user is editing a sheet 
    PrintWriter cacheddocfile = createWriter(dataPath("../../cacheddoc.svg"));

    for (String line : fabricaidedoc) {
      cacheddocfile.println(line);
    }
    cacheddocfile.flush();
    cacheddocfile.close();

    cacheddoc = fabricaidedoc;

    surface.setTitle("[PACKING...] Fabricaide");
    loadStrings("http://127.0.0.1:3000/process?svgfile=cacheddoc.svg&copies="+copies);
    processingfile = true;
  }
}


void draw() {
  background(100); 

  joblist.display();

  if (state == OPTIONS) {
    fill(0, 180);
    noStroke();
    rect(0, 0, width, height);

    fill(255);
    textAlign(CENTER);
    text("UI options", width/4, 80);

    textAlign(LEFT);
    text("packing previews", 80, 115);
    text("material utilization", 80, 155);
    text("sheet utilization", 80, 195);
    text("sheet thumbnails", 80, 235);
  } else {
    update();
  }

  drawInterfacePanels();
}

boolean documentChanged(String[] document) {
  if (document.length > 0 && document[document.length-1].trim().equals("</svg>") && 
    !Arrays.equals(document, cacheddoc)) {
    println("Design has changed. Reprocessing");

    PrintWriter cacheddocfile = createWriter(dataPath("../../cacheddoc.svg"));
    for (String line : document) {
      cacheddocfile.println(line);
    }
    cacheddocfile.flush();
    cacheddocfile.close();

    cacheddoc = document;

    return true;
  }

  return false;
}



void update() {

  if (state == HOME) {
    
    
    if (millis() > lastRefresh + 500) {
      lastRefresh = millis();
      if (debug) return; 

      if (!paused && !processingfile) {
        if (!use3D) illustrator.exportCurrentDocument(fabricaidedocpath);

        // Check whether the design has been updated, and if so,
        // request a repacking of the shapes
        if (fabricaidedocfile.exists()) {
          try {
            String[] fabricaidedoc = loadStrings(fabricaidedocpath);

            // request to repack unless user is editing a sheet 
            if (!debug && documentChanged(fabricaidedoc)) {
              surface.setTitle("[PACKING...] Fabricaide");
              
              loadStrings("http://127.0.0.1:3000/process?svgfile=cacheddoc.svg&copies="+copies);
              processingfile = true;
            }
          }

          catch(Exception e) {
            println("error on loading file: " + e);
          }
        }
      } else if (processingfile) {

        JSONObject refresh = loadJSONObject("http://127.0.0.1:3000/check_refresh");

        if (refresh.getBoolean("refresh")) {
          processingfile = false;
          
          println("New data is available. Refreshing percentages and insufficient materials");
          
          // Process insufficient material warnings
          JSONArray insufficient = refresh.getJSONArray("insufficient");
          JSONArray crashed = refresh.getJSONArray("crashed");

          // No insufficient materials :)
          if (insufficient.size() == 0) {
            insufficientmaterials.clear();
          }
          // Some insufficient materials
          else {
            insufficientmaterials.clear();
            JSONObject failed_fits = refresh.getJSONObject("failed_fits"); 

            for (int i = 0; i < insufficient.size(); i++) {
              String insufficientmat = insufficient.getString(i);
              JSONObject substitutes = loadJSONObject("http://127.0.0.1:3000/get_similar_materials?matname="+insufficientmat);
              JSONArray substitutesArray =  substitutes.getJSONArray("substitutes");
              List<String> substitutesList = new ArrayList<String>();

              for (int j = 0; j < substitutesArray.size(); j++) {
                String sub = substitutesArray.getString(j); 
                substitutesList.add(sub);
              }

              insufficientmaterials.put(insufficientmat, substitutesList);
              failedFitsForMaterial.put(insufficientmat, failed_fits.getInt(insufficientmat));
            }
          }

          // No crashed materials
          if (crashed.size() == 0) {
            crashedMaterials.clear();
          }
          // Some crashed materials
          else {
            crashedMaterials.clear();
            for (int i = 0; i < crashed.size(); i++) {
              crashedMaterials.add(crashed.getString(i));
            }
          }

          resetVariables(); 
          joblist.clearJobs(); 
          joblist.setY(0);
          layoutUI(); 
          
          if (!paused) surface.setTitle("Fabricaide");
          else surface.setTitle("[PAUSED] Fabricaide");

          // Update material percentages
          JSONObject percentages = refresh.getJSONObject("usage"); 
          Set material_keys = percentages.keys(); 
          for (Object matname : material_keys) {
            if (percentages.get(matname.toString()) instanceof JSONArray && joblist.hasMaterial(matname.toString())) {
              ArrayList<Float> p = new ArrayList<Float>(); 
              JSONArray percentagesArray = percentages.getJSONArray(matname.toString()); 
              if (percentagesArray != null) {
                for (int i=0; i<percentagesArray.size(); i++) {
                  p.add(percentagesArray.getFloat(i));
                }
                SheetContainer container = joblist.getContainer(matname.toString()); 
                container.setPercentages(p);
              }
            }
          }
          
        }
      }
    }
  } else if (state == EDITING) {
    if (millis() > lastRefresh + 1000) {
      lastRefresh = millis();
      illustrator.exportCurrentDocument(editedpackingdocpath);

      if (editedpackingdocfile.exists()) {
        try {
          String[] editedpackingdoc = loadStrings(editedpackingdocpath);
          if (!debug && documentChanged(editedpackingdoc)) {

            PrintWriter materialsheetfile = createWriter(dataPath("../../cuts/"+selectedMaterialName+"_"+
              selectedSheet.getSheetData().getSheetID()+".svg"));
            for (String line : editedpackingdoc) {
              materialsheetfile.println(line);
            }
            materialsheetfile.flush();
            materialsheetfile.close();

            JSONObject supplylevels = loadJSONObject("http://127.0.0.1:3000/get_supply_levels?matname="+selectedMaterialName);
            JSONArray percentagesArray = supplylevels.getJSONArray("usage"); 
            if (percentagesArray != null) {
              ArrayList<Float> p = new ArrayList<Float>(); 
              for (int i=0; i<percentagesArray.size(); i++) {
                p.add(percentagesArray.getFloat(i));
              }
              SheetContainer container = joblist.getContainer(selectedMaterialName.toString()); 
              container.setPercentages(p);
            }

            // update sheet preview
            loadStrings("http://127.0.0.1:3000/convert_to_png?material="+selectedMaterialName+"&sheetid="+selectedSheet.getSheetData().getSheetID());
            selectedSheet.getSheetData().reloadSheetPreview(selectedMaterialName, str(selectedSheet.getSheetData().getSheetID()));
          }
        }

        catch(Exception e) {
          println("error on loading file: " + e);
        }
      }
    }
  }
}


void exit() {
  println("exited"); 
  loadStrings("http://127.0.0.1:3000/shutdown"); 

  super.exit();
} 

// This function returns all the files in a directory as an array of File objects
// This is useful if you want more info about the file
File[] listFiles(String dir) {
  File file = new File(dir); 
  if (file.isDirectory()) {
    File[] files = file.listFiles(); 
    return files;
  } else {
    // If it's not a directory
    return null;
  }
}
