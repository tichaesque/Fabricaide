// takes an SVG file containing the packed shapes for a given material sheet
// creates an SVG of the shapes packed onto the material sheet
public class SheetData {  
  private PImage packingoutput;
  private PImage materialsheet; 
  private PImage packedsheet; 
  private int id; 
  private String materialname;
  private color sheetcolor; 

  public SheetData(String packingoutputfile) {
    if (packingoutputfile.split("_").length < 2) {
      println("invalid file:"); 
      println(packingoutputfile);
      return;
    }

    materialname = packingoutputfile.split("_")[0];
    id = int(packingoutputfile.split("_")[1]);

    // an id < 0 indicates that we are out of this material
    if (id >= 0) {
      packedsheet = loadImage(packedshapes_dir+"/" +materialname+"_"+ id+".png"); 
      packedsheet.resize(0, sheetheight); // use fixed height
      //packedsheet.resize(sheetheight, 0); // use fixed width
    }

    JSONArray rgb = colorsdict.getJSONArray(materialname); 
    if (rgb != null) sheetcolor = color(rgb.getInt(0), rgb.getInt(1), rgb.getInt(2));
    else sheetcolor = -1;
  }

  public color getSheetColor() {
    return sheetcolor;
  }

  public String getMaterialName() {
    return materialname;
  }

  // pastes img2 into img1
  // requires that dimensions(img2) == dimensions(img1)
  public PImage combineImages(PImage img1, PImage img2) {
    img1.loadPixels();

    // shouldn't run into this issue if the images are saved correctly....
    if (img1.width != img2.width || img1.height != img2.height) {
      if (img2.height*img2.width >= img1.height*img1.width) { // scale the larger one down
        img2.resize(img1.width, img1.height);
      } else {
        img1.resize(img2.width, img2.height);
      }
    }

    for (int i = 0; i < img1.width*packedsheet.height; i++) {
      img1.pixels[i] += img2.pixels[i];
    }

    img1.updatePixels();

    return img1;
  }

  public float getSheetWidth() {
    if (id < 0) return 100;
    return packedsheet.width;
  }

  public float getSheetHeight() {
    if (id < 0) return sheetheight;
    return packedsheet.height;
  }

  public int getSheetID() {
    return id;
  }

  public void reloadSheetPreview(String materialname, String id) {
    packedsheet = loadImage(packedshapes_dir+"/" +materialname+"_"+ id+".png"); 
    packedsheet.resize(0, sheetheight);
  }

  public PImage getPackedSheet() {
    return packedsheet;
  }

  public void displaySheet(float x, float y, float w, float h) {
    stroke(0);
    strokeWeight(2);
    //fill(sheetcolor, 100);
    fill(sheetcolor);
    rect(x, y, w, h);
    fill(0,100);
    rect(x, y, w, h); 

    if (id >= 0) {
      image(packedsheet, x, y, w, h);
    }
  }
}
