import cv2 
import numpy as np 

from scipy.interpolate import splprep, splev

from sys import argv

# Ignore curves enclosing an area / of length less than this
small_area_threshold = 25
small_length_threshold = 15

# Smooth contours
# https://agniva.me/scipy/2016/10/25/contour-smoothing.html
def smooth_contours(contours):
  smoothened = []
  for contour in contours: 
      x,y = contour.T
      # Convert from numpy arrays to normal arrays
      x = x.tolist()[0]
      y = y.tolist()[0]
      tck, u = splprep([x,y], u=None, s=1.0, per=1)
      u_new = np.linspace(u.min(), u.max(), len(x)//10)
      x_new, y_new = splev(u_new, tck, der=0)
      # Convert it back to np format for opencv to be able to display it
      res_array = [[[int(i[0]), int(i[1])]] for i in zip(x_new,y_new)]
      smoothened.append(np.asarray(res_array, dtype=np.int32))
  return smoothened

# Create an SVG path element from the given sequence of points
def create_path_element(points):
  output = '<path d="M'
  
  for x,y in points:
    output += '{} {} '.format(x, y)
    
  # Duplicate the first point to close the path
  x, y = points[0]
  output += '{} {} '.format(x, y)
  
  output += '"/>'
  return output

def contours2svg(contours, width, height): 
    output = '<svg width="{}" height="{}" viewBox="0 0 {} {}" xmlns="http://www.w3.org/2000/svg">'.format(width, height, width, height)

    for idx,c in enumerate(contours):
        area = cv2.contourArea(c)
        length = cv2.arcLength(c, True)
    
        # Ignore very small or short contours. They are probably noise
        if (area <= small_area_threshold): continue
        if (length <= small_length_threshold): continue
 
        P = []
        for p in c:
          x, y = p[0]
          P.append((x,y))
 
        output += create_path_element(P)       
    output += '</svg>' 

    return output

def boundingBox(mask):
  height, width = mask.shape

  xmin, xmax, ymin, ymax = width,0,height,0
  for x in range(width):
    for y in range(height):
      if mask[y][x] == 255:
        xmin = min(xmin, x)
        ymin = min(ymin, y)
        xmax = max(xmax, x)
        ymax = max(ymax, y)

  return xmin, ymin, xmax, ymax

def extractContours(filename, x,y): 

  # Preprocess -- grayscale, blur, and threshold
  image = cv2.imread(filename) 
  height, width, channels = image.shape
  seed = (x,y)

  mask = np.zeros((height+2,width+2),np.uint8)

  floodflags = 4
  floodflags |= cv2.FLOODFILL_MASK_ONLY
  floodflags |= (255 << 8)

  num,im,mask,rect = cv2.floodFill(image, mask, seed, (255,0,0), (10,)*3, (10,)*3, floodflags)
  cv2.imwrite('mask1.jpg',mask)

  x1,y1,x2,y2 = boundingBox(mask)

  mask = mask[y1:y2, x1:x2]

  height,width = mask.shape

  mask[0:height-1,0] = 255
  mask[0:height-1,width-1] = 255
  mask[0,0:width-1] = 255
  mask[height-1, 0:width-1] = 255

  cv2.imwrite('mask-cropped.jpg',mask)

  # Find Canny edges 
  edged = cv2.Canny(mask, 127, 127)
  cv2.imwrite('edged.jpg',edged)
    
  # Apply a small amount of dilation to close contours
  dilated = cv2.dilate(edged, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3)))
  cv2.imwrite('dilated.jpg', dilated)

  # Finding Contours 
  contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
  all_contours = []

  # Fix each contour individually
  for i,contour in enumerate(contours):
    img = np.zeros((height,width,3), np.uint8) 
    cv2.drawContours(img, [contour], 0, (0, 255, 0), 1) 
    
    # Additional dilation to close contours that still haven't closed
    dilated = cv2.dilate(img, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5)))
    gray = cv2.cvtColor(dilated, cv2.COLOR_BGR2GRAY)

    # Find new contours
    new_contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    all_contours.extend(smooth_contours(new_contours))

  return contours2svg(all_contours, width, height)
