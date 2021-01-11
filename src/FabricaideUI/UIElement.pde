public class UIElement {
  private float x, y; 
  private float elemwidth; 
  private float elemheight; 
  private boolean isMouseOver; 
  private boolean isVisible;
  private ArrayList<UIElement> children; 

  public UIElement(float x_, float y_, float w, float h) {
    x = x_;
    y = y_; 
    elemwidth = w; 
    elemheight = h; 
    isVisible = true;

    children = new ArrayList<UIElement>();
  }

  public float getX() {
    return x;
  }

  public float getY() {
    return y;
  } 

  public float getWidth() {
    return elemwidth;
  }

  public float getHeight() {
    return elemheight;
  }

  public boolean getMouseOver() {
    return isMouseOver;
  } 
  
  public boolean getVisible() {
    return isVisible;
  }

  public void setX(float x_) {
    x = x_;
  }

  public void setY(float y_) {
    y = y_;
  } 

  public void setWidth(float w) {
    elemwidth = w;
  }

  public void setHeight(float h) {
    elemheight = h;
  }


  public void setMouseOver(boolean mo) {
    isMouseOver = mo;
  }

  public void setVisible(boolean vis) {
    isVisible = vis;
  }


  public boolean contains(int x1, int y1) {
    return (x <= x1) && (x1 <= x + elemwidth) &&
      (y <= y1) && (y1 <= y + elemheight);
  }

  public final void addChild(UIElement newchild) {
    children.add(newchild);
  }

  public final void updateChild(int childidx, UIElement update) {
    children.set(childidx, update);
  }

  public ArrayList<UIElement> getChildren() {
    return children;
  }
  
  void clearChildren() {
    children.clear(); 
  }

  private void unMouseOver() {
    setMouseOver(false); 

    for (UIElement child : children) {
      child.setMouseOver(false);
    }
  }

  public boolean updateMouseOver() {
    
    
    unMouseOver(); 

    if (mouseY < UIpanelY && isVisible && contains(mouseX, mouseY)) {
      setMouseOver(true); 
      mouseOverChildren();

      return true;
    } 

    return false;
  }

  // check which child has the mouse over it and update
  public void mouseOverChildren() {
    for (UIElement child : children) {
      if (child.updateMouseOver()) {
        return; // early exit if we found the child with the mouse
      }
    }
  }
}
