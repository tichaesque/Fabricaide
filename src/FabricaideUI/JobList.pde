import java.util.*;  //<>// //<>// //<>// //<>// //<>//

String cuttingMaterial = "";
int selectedSheetIdx = -1;
int queueIdx = 0; 

List<String> materialqueue;  

public class JobList extends UIElement {
  private TreeMap<String, SheetContainer> children; 

  public JobList() {
    super(0, 0, width, height); 
    children = new TreeMap<String, SheetContainer>();
  }
  
  public Set getJobs() {
    return children.keySet();
  }

  public void clearJobs() {
    children.clear();
    clearChildren();
  }

  public boolean hasMaterial(String mat) {
    return children.containsKey(mat);
  }

  public SheetContainer getContainer(String mat) {
    return children.get(mat);
  }

  public void addMaterial(SheetContainer sheetcon) {
    children.put(sheetcon.getMaterialName(), sheetcon);
    addChild(sheetcon);
  }

  public void layout() {
    float listHeight = 0; 
    float containerY = getY();

    for (Map.Entry<String, SheetContainer> entry : children.entrySet()) {
      SheetContainer container = entry.getValue();
      if (state != SCROLLING) container.purgeThumbnails();

      container.setVisible(true);
      container.setX(getX()); 
      container.setY(containerY);
      container.layout();

      containerY += container.getHeight();
      listHeight += container.getHeight();
    }
    
    setHeight(listHeight);
  }

  public void display() {
    for (SheetContainer container : children.values()) { 
      container.display();
    }
  }
  
  public void updateSelectedMaterial() {
    if (state != CUTTING) {
      selectedMaterialName = "";
      selectedSheet = null;
    }
    
    for (SheetContainer container : children.values()) { 
      if (state == HOME && container.getMouseOver()) {
        selectedMaterialName = container.getMaterialName(); 
        for (UIElement sheetUIElem : container.getChildren()) {
          Sheet sheet = (Sheet) sheetUIElem;
          if (sheet.getMouseOver()) {
            selectedSheet = sheet;
            return;
          }
        }
        
        return;
      }
    }
  }
}
