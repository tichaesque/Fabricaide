public class Sheet extends UIElement {
  private SheetData sheet;
  private float percentage;
  private final float barPadding = 1.5;
  private float supplyBarHeight = 10; 

  public Sheet(SheetData sheet_) {
    super(0, 0, sheet_.getSheetWidth(), sheet_.getSheetHeight()); 
    sheet = sheet_;
  }

  public SheetData getSheetData() {
    return sheet;
  }

  public void setPercentage(float p) {
    percentage = p;
  }

  public void display() {

    sheet.displaySheet(getX(), getY(), getWidth(), getHeight());

    // utilization bar for sheet

    if (showLocalUtilization) {
      fill(0);
      rect(getX(), getY() + getHeight() + 5, getWidth(), supplyBarHeight); 

      noStroke();
      fill(255);
      rect(getX()+barPadding, getY() + getHeight()+5 +barPadding, (getWidth()*(1-percentage)) -(2*barPadding - 0.5), supplyBarHeight -(2*barPadding - 0.5));
    }

    if (getMouseOver()) {
      if (state == HOME) {
        textAlign(CENTER);
        fill(0, 100);
        rect(getX(), getY(), getWidth(), getHeight());
        fill(255);
        text("EDIT", width/2, getY() +getHeight()/2);
      }

      stroke(255, 255, 0); 
      strokeWeight(3);
      noFill();
      rect(getX(), getY(), getWidth(), getHeight());
    }
  }
}
