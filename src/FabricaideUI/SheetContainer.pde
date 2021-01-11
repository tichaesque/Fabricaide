public class SheetContainer extends UIElement { //<>// //<>// //<>//
  private String materialname; 
  private ArrayList<Sheet> children; 
  private ArrayList<Integer> childrenIdx; 
  private float childspacing = 30; 
  private float containermargintop = 25;
  private final float topbarmarginleft = 20;
  private final float topbarlength = 35;
  private final float barMargin = 1.5;
  private ArrayList<PImage> thumbnails;
  private ArrayList<Float> percentages;
  private float supplyBarHeight = 4; 
  private boolean insufficient = false;
  private  boolean crashed = false; 
  private int totalsheets = 0; 
  private int extrasheets = 0;
  private boolean hasExtras = false;

  public SheetContainer(String matname) { 
    super(0, 0, width, 0); 
    children = new ArrayList<Sheet>();
    childrenIdx = new ArrayList<Integer>();
    thumbnails = new ArrayList<PImage>();
    materialname = matname;
    percentages = new ArrayList<Float>();
    totalsheets = getTotalSheets();
  }

  public int numChildren() {
    return children.size();
  }

  public void purgeSheets() {
    children.clear();
    clearChildren();
  }

  public void purgeThumbnails() {
    thumbnails.clear();
  }

  public void setPercentages(ArrayList<Float> p) {
    percentages = (ArrayList<Float>) p.clone();
  }

  public String getMaterialName() {
    return materialname;
  }

  public void addSheet(Sheet newchild) {
    children.add(newchild);
    addChild(newchild);
  }

  public SheetData getSheetDataForSheet(int childidx) {
    return children.get(childidx).getSheetData();
  }

  private int getTotalSheets() {
    File[] files = listFiles(dataPath(matdb+ "/"+materialname));
    int count = 0;
    for (File f : files) {
      String matsheet = f.getName();
      if (matsheet.length() < 1 || matsheet.charAt(0) == '.') { 
        continue;
      }

      count++;
    }

    return count;
  }

  public void layout() {
    int heightMultiplier = 0;
    int extrapadding = 0;
    
    if(!showThumbnails && !showLocalUtilization) childspacing = 10; 

    if (crashedMaterials.contains(materialname)) {
      crashed = true;
      extrapadding = 100;
    } else if (insufficientmaterials.containsKey(materialname)) insufficient = true;

    if (!crashed) {
      if (showPacking) {
        // add some padding to make room for the insufficient materials messsage
        if (insufficient) extrapadding = 100;

        heightMultiplier = children.size();
        for (int i = 0; i < children.size(); i++) { 
          Sheet child = children.get(i);
          float childWidth = child.getWidth();
          child.setX((width-childWidth)/2); 
          child.setY(extrapadding + containermargintop + getY() + (child.getHeight() + childspacing)*i); 

          children.set(i, child);

          childrenIdx.add(child.getSheetData().getSheetID());
        }
      }

      if (state == HOME || state == OPTIONS) {
        if (showThumbnails && !insufficient) {
          File[] allSheets = listFiles(dataPath(matdb + "/"+materialname));
          Arrays.sort(allSheets, new Comparator<File>() {
            @Override
              public int compare(File o1, File o2) {
              int n1 = extractNumber(o1.getName());
              int n2 = extractNumber(o2.getName());
              return n1 - n2;
            }

            private int extractNumber(String name) {
              int i = 0;
              try {
                int s = name.indexOf('_')+1;
                int e = name.lastIndexOf('.');
                String number = name.substring(s, e);
                i = Integer.parseInt(number);
              } 
              catch(Exception e) {
                i = 0; // if filename does not match the format
                // then default to 0
              }
              return i;
            }
          }
          );

          for (File sheet : allSheets) {

            String sheetfilename = sheet.getName();
            String sheetfileid = sheetfilename.substring(0, sheetfilename.length() - 4);

            if (!childrenIdx.contains(int(sheetfileid))) {
              hasExtras = true;
              PImage thumbnail = loadImage(matdb + "/"+materialname + "/" + sheetfilename);
              thumbnail.resize(0, sheetheight/3);
              thumbnails.add(thumbnail);

              if (thumbnails.size() >= 2) break;
            }
          }
        }
      }
    }

    setHeight(extrapadding + containermargintop + heightMultiplier*(sheetheight + childspacing) + 
      ((showThumbnails && hasExtras) ? sheetheight/2 : 0));

    if (hasExtras) extrasheets = totalsheets - children.size() - thumbnails.size();
  }

  public void display() {

    if (getVisible()) {

      noStroke(); 
      fill(100);
      if (insufficient || crashed) fill(#c9270e, 170);

      rect(getX(), getY(), getWidth(), getHeight()); 

      color sheetcolor = 0;
      float thumbX = 0;
      float thumbY = 0;

      int percentage_index = 1;

      if (!crashed) {
        if (showPacking) {
          for (int i = 0; i < children.size(); i++) {
            Sheet child = children.get(i);

            if (percentages.size() > 0) {
              child.setPercentage(percentages.get(child.getSheetData().getSheetID() + 1));
              percentage_index += 1;
            }

            child.display();

            thumbX = child.getX(); 
            thumbY = child.getY();

            if (state == CUTTING && queueIdx >= 0 && materialname.equals(materialqueue.get(queueIdx))) {
              if (i != selectedSheetIdx) {
                fill(0, 100);
                rect(child.getX(), child.getY(), child.getWidth(), child.getHeight());
              } else {
                stroke(255, 255, 0); 
                strokeWeight(3);
                noFill();
                rect(child.getX(), child.getY(), child.getWidth(), child.getHeight());
              }
            }
          }
        }


        if (showThumbnails) {
          if (state == HOME || state == SCROLLING || state == EDITING || state == OPTIONS) {
            thumbY += sheetheight + childspacing;

            JSONArray rgb = colorsdict.getJSONArray(materialname); 
            if (rgb != null) sheetcolor = color(rgb.getInt(0), rgb.getInt(1), rgb.getInt(2));

            for (PImage thumbnail : thumbnails) {
              stroke(0);
              strokeWeight(2);
              fill(sheetcolor, 100); 
              rect(thumbX, thumbY, thumbnail.width, thumbnail.height); 
              image(thumbnail, thumbX, thumbY);

              // utilization bars for thumbnails
              if (showLocalUtilization) {
                if (percentages.size() > 0 && percentage_index < percentages.size()) {
                  fill(0);
                  rect(thumbX, thumbY + thumbnail.height + 5, (thumbnail.width), supplyBarHeight);

                  noStroke();
                  fill(255);
                  rect(thumbX + barMargin, thumbY + thumbnail.height + 5 + barMargin, 
                    (thumbnail.width*(1-percentages.get(percentage_index)))-(2*barMargin - 0.5), supplyBarHeight - (2*barMargin - 0.5));

                  percentage_index += 1;
                }
              }

              thumbX += thumbnail.width + 10;
            }

            if (extrasheets > 0) {
              textAlign(LEFT);
              fill(255);
              // add quantity of extra sheets if there are more than 2 extras
              text("+" + extrasheets + " more", thumbX, thumbY + 30);
            }
          }
        }
      }

      if (insufficient) {
        textAlign(CENTER);

        fill(255);

        String insufficientWarning = "[!] " +failedFitsForMaterial.get(materialname) + " shape(s) failed to fit.\n\n Scale down or try substitutes:\n"; 
        List<String> substitutesList = insufficientmaterials.get(materialname); 
        for (String sub : substitutesList) {
          insufficientWarning += "> " + sub + "\n";
        }

        text(insufficientWarning, getX() + getWidth()/2, getY() + containermargintop + 15);
      } else if (crashed) {
        textAlign(CENTER);

        fill(255);

        text("[!] internal error. \n\n please check your design for: \n > self-intersections \n > empty paths.", getX() + getWidth()/2, getY() + containermargintop + 15);
      }


      stroke(0);
      strokeWeight(1);

      fill(50);

      rect(getX(), getY(), getWidth(), containermargintop-5); 



      if (showGlobalUtilization) {
        if (!insufficient) stroke(255);
        else stroke(color(255, 0, 0));

        strokeWeight(1);
        noFill();
        rect(getX() + topbarmarginleft, getY() + 5, topbarlength, 10);

        // global suppy bar for material
        if (!insufficient && percentages.size() > 0) {

          noStroke();
          fill(255);
          rect(getX() + topbarmarginleft+barMargin, getY() + 5 + barMargin, (topbarlength*(1-percentages.get(0)))- (2* barMargin - 0.5), 10 - (2* barMargin - 0.5));
        }

        fill(255);
        textAlign(LEFT);
        text(materialname, getX() + 1.5*topbarmarginleft + topbarlength, getY() + containermargintop-10);
      } else {
        fill(255);
        textAlign(CENTER);
        text(materialname, width/2, getY() + containermargintop-10);
      }


      if (state == CUTTING) {
        if (queueIdx < 0 || !materialname.equals(materialqueue.get(queueIdx))) {
          fill(0, 100);
          rect(getX(), getY(), getWidth(), getHeight());
        }
      }
    }
  }
}
