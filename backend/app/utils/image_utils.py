"""
image_utils.py
--------------
Utility helpers for colour analysis used across the textile pipeline.
"""
import math
import colorsys
from PIL import Image

# ---------------------------------------------------------------------------
# Colour map — standard target colours mapped to their RGB representative
# ---------------------------------------------------------------------------
COLOR_MAP = {
    "White":  (245, 245, 245),
    "Grey":   (128, 128, 128),
    "Black":  ( 25,  25,  25),
    "Red":    (180,  40,  40),
    "Blue":   ( 40,  70, 160),
    "Green":  ( 40, 140,  80),
    "Yellow": (220, 200,  50),
    "Beige":  (225, 210, 185),
    "Brown":  (110,  75,  45),
    "Orange": (220, 110,  40),
    "Purple": (110,  50, 140),
    "Pink":   (230, 130, 170),
}


def rgb_to_hex(rgb: tuple) -> str:
    """Convert an (R, G, B) tuple to a CSS hex string, e.g. '#3a7fd5'."""
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def get_color_name(rgb: tuple) -> str:
    """
    Return the closest named colour in COLOR_MAP for a given RGB tuple 
    using HSV thresholds for human-perceived color matching.
    """
    r, g, b = rgb
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    hue_deg = h * 360.0
    
    # 1. Neutral colors (low saturation)
    if s < 0.18:
        if v > 0.85:
            return "White"
        elif v < 0.18:
            return "Black"
        else:
            return "Grey"
            
    if v < 0.22:
        return "Black"
        
    # 2. Saturated colors
    # Brown and Beige are specific ranges of Orange/Yellow with distinct Saturation/Value
    if 10 <= hue_deg <= 50:
        if v < 0.65:
            return "Brown"
        elif s < 0.35 and v > 0.70:
            return "Beige"
        elif hue_deg > 38:
            return "Yellow"
        else:
            return "Orange"
            
    if hue_deg < 10 or hue_deg > 345:
        # Pink vs Red: Pink is bright and moderately saturated magenta/red
        if hue_deg > 300 and s < 0.6 and v > 0.6:
            return "Pink"
        return "Red"
        
    if 10 <= hue_deg < 40:
        return "Orange"
        
    if 40 <= hue_deg < 75:
        # Yellow vs Beige fallback
        if s < 0.25 and v > 0.75:
            return "Beige"
        return "Yellow"
        
    if 75 <= hue_deg < 165:
        return "Green"
        
    if 165 <= hue_deg < 255:
        return "Blue"
        
    if 255 <= hue_deg < 295:
        return "Purple"
        
    if 295 <= hue_deg <= 345:
        if s < 0.6 and v > 0.5:
            return "Pink"
        return "Purple"
        
    return "Grey"


def get_dominant_color(img: Image.Image) -> tuple:
    """
    Computes a background-aware average/dominant color of an image 
    by cropping to the center region and filtering out neutral background pixels.
    """
    if img.mode != "RGB":
        img = img.convert("RGB")
        
    # Resize to speed up analysis
    img_small = img.resize((100, 100), Image.Resampling.NEAREST)
    width, height = img_small.size
    
    # Crop to the center region (25% to 75%) where the textile is most likely located
    left = int(width * 0.25)
    top = int(height * 0.25)
    right = int(width * 0.75)
    bottom = int(height * 0.75)
    
    center_img = img_small.crop((left, top, right, bottom))
    
    # Retrieve pixel list
    pixels = list(center_img.getdata())
    
    # Filter out neutral background pixels (e.g. white, light gray, black backdrops)
    non_bg_pixels = []
    for r, g, b in pixels:
        is_white_bg = (r > 220 and g > 220 and b > 220)
        is_black_bg = (r < 30 and g < 30 and b < 30)
        # If R, G, and B are very close (max diff < 15), it is a neutral gray backdrop
        is_neutral = max(r, g, b) - min(r, g, b) < 15
        
        if not (is_white_bg or is_black_bg or is_neutral):
            non_bg_pixels.append((r, g, b))
            
    # Fallback if too many pixels were filtered (e.g. if the garment itself is white/gray/black)
    if len(non_bg_pixels) < (len(pixels) * 0.1):
        non_bg_pixels = [p for p in pixels if not (p[0] > 245 and p[1] > 245 and p[2] > 245)]
        if not non_bg_pixels:
            non_bg_pixels = pixels
            
    # Calculate simple average of the non-background garment pixels
    r_avg = sum(p[0] for p in non_bg_pixels) // len(non_bg_pixels)
    g_avg = sum(p[1] for p in non_bg_pixels) // len(non_bg_pixels)
    b_avg = sum(p[2] for p in non_bg_pixels) // len(non_bg_pixels)
    
    return (r_avg, g_avg, b_avg)
