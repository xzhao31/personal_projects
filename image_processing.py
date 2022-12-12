### this file contains functions for loading both grayscale and color images,
### modifying (blur, sharpen, seam carve, color scales) images, and saving them

import math
from PIL import Image


# HELPER FUNCTIONS

def get_index(image,x,y):
    """
    x is the horizontal element (0 to width-1) and y is the vertical element (0 to height-1),
    like in the Cartesian plane.
    """
    return y*image['width']+x


def get_coords(image,index):
    """
    takes index, returns (x,y)
    """
    y=index//image['width']
    x=index-y*image['width']
    return x,y

def get_pixel(image, x, y):
    return image['pixels'][get_index(image,x,y)]


def set_pixel(image, x, y, c):
    image['pixels'][get_index(image,x,y)] = c


def apply_per_pixel(image, func):
    """
    takes image (dictionary) and performs func on each pixel and returns new image (dictionary)
    """
    result = {
        'height': image['height'],
        'width': image['width'],
        'pixels': [0]*image['height']*image['width'],
    }
    for y in range(image['height']):
        for x in range(image['width']):
            color = get_pixel(image, x, y)
            newcolor = func(color)
            set_pixel(result, x, y, newcolor)
    return result


def inverted(image):
    return apply_per_pixel(image, lambda c: 255-c)


def get_any_pixel(image,x,y,method=None):
    """
    does the same thing as get_pixel except it accounts for pixels not in the image through one of
    3 methods: zero, extend, and wrap.
    """
    if x in range(image['width']) and y in range(image['height']):
        return image['pixels'][get_index(image,x,y)]

    elif method=='zero':
        return 0

    elif method=='extend':
        #snap x to the closest value
        if x<0:
            x_i=0
        elif x>image['width']-1:
            x_i=image['width']-1
        else:
            x_i=x
        #snap y to the closest value
        if y<0:
            y_i=0
        elif y>image['height']-1:
            y_i=image['height']-1
        else:
            y_i=y
        #return value
        return image['pixels'][get_index(image,x_i,y_i)]

    elif method=='wrap':
        x_i=x%image['width']
        y_i=y%image['height']
        return image['pixels'][get_index(image,x_i,y_i)]

    else:
        return None


def nxn_matrix_as_list(image,x,y,n,method):
    """
    generate list, len n**2, of pixels in original photo, centered at (x,y)
    """
            
    pixels=[0]*(n**2)
    i=0
    for y_i in range(y-n//2,y+n//2+1):
        for x_i in range(x-n//2,x+n//2+1):
            pixels[i]=get_any_pixel(image,x_i,y_i,method)
            i+=1
    return pixels


def correlate(image, kernel, boundary_behavior):
    """
    Compute the result of correlating the given image with the given kernel.
    `boundary_behavior` will one of the strings 'zero', 'extend', or 'wrap',
    and this function will treat out-of-bounds pixels as having the value zero,
    the value of the nearest edge, or the value wrapped around the other edge
    of the image, respectively.

    if boundary_behavior is not one of 'zero', 'extend', or 'wrap', return
    None.

    Otherwise, the output of this function should have the same form as a 6.101
    image (a dictionary with 'height', 'width', and 'pixels' keys), but its
    pixel values do not necessarily need to be in the range [0,255], nor do
    they need to be integers (they should not be clipped or rounded at all).

    This process should not mutate the input image; rather, it should create a
    separate structure to represent the output.

    Kernel is a list of floats, converting the square matrix using row-major order.
    """
    new_image = {
        'height': image['height'],
        'width': image['width'],
        'pixels': [0]*image['height']*image['width'],
        }
            
    n=int(math.sqrt(len(kernel)))
    for y in range(image['height']):
        for x in range(image['width']):
            #perform kernel operation
            new_value=sum(scale*pixel for scale, pixel in list(zip(kernel,nxn_matrix_as_list(image,x,y,n,boundary_behavior))))    
            #plug it in
            set_pixel(new_image,x,y,new_value)

    return new_image
                                                

def round_and_clip_image(image):
    """
    Given a dictionary, ensure that the values in the 'pixels' list are all
    integers in the range [0, 255].

    All values should be converted to integers using Python's `round` function.

    Any locations with values higher than 255 in the input should have value
    255 in the output; and any locations with values lower than 0 in the input
    should have value 0 in the output.
    """
    for i in range(len(image['pixels'])):
        if image['pixels'][i]<0:
            image['pixels'][i]=0
        elif image['pixels'][i]>255:
            image['pixels'][i]=255
        else:
            image['pixels'][i]=round(image['pixels'][i])


def blurred(image, n):
    """
    Return a new image representing the result of applying a box blur (with
    kernel size n) to the given input image.

    This process should not mutate the input image; rather, it should create a
    separate structure to represent the output.
    """
    #create a representation for the appropriate n-by-n kernel
    blur_kernel=[1/(n**2)]*(n**2)
    #compute the correlation of the input image with that kernel
    output=correlate(image, blur_kernel, 'extend')
    #make sure that the output is a valid image before returning it.
    round_and_clip_image(output)
    return output


def sharpened(image, n):
    """
    return a new image sharpened, with each pixel in the sharpened image
    S=2I-B, where I is the original image and B is the blurred image using
    kernel of size nxn
    """
    sharpen_kernel=[-1/(n**2)]*(n**2)
    sharpen_kernel[(n**2)//2]+=2
    output=correlate(image,sharpen_kernel,'extend')
    round_and_clip_image(output)
    return output


def edges(image):
    """
    return new image with edges emphasized
    """
    K_x=[-1,0,1,-2,0,2,-1,0,1]
    O_x=correlate(image,K_x,'extend')
    K_y=[-1,-2,-1,0,0,0,1,2,1]
    O_y=correlate(image,K_y,'extend')
    output_pixels=[math.sqrt(ox**2+oy**2) for ox,oy in zip(O_x['pixels'],O_y['pixels'])]
    output={'height':image['height'],'width':image['width'],'pixels':output_pixels}
    round_and_clip_image(output)
    return output


# VARIOUS FILTERS

def unpack_colors(image, color):
    """
    takes rgb color image and returns only the r, g, or b component of the
    pixels as a grayscale image
    """
    assert color in ['r','g','b'], f'{color} is not a valid color; must be \"r\", \"g\", or \"b\"'
    if color=='r':
        pixels=[pixel[0] for pixel in image['pixels']]
    if color=='g':
        pixels=[pixel[1] for pixel in image['pixels']]
    if color=='b':
        pixels=[pixel[2] for pixel in image['pixels']]
    return {
        'height':image['height'],
        'width':image['width'],
        'pixels':pixels}


def combine_colors(red,green,blue):
    """
    take 3 separate images in grayscale for r,g,b and combines them into one color image
    """
    assert red['height']==green['height']==blue['height'], 'images must be same dimensions'
    assert red['width']==green['width']==blue['width'], 'images must be same dimensions'
    assert len(red['pixels'])==len(green['pixels'])==len(blue['pixels']), 'images must be same dimensions'
    pixels=list(zip(red['pixels'],green['pixels'],blue['pixels']))
    return {
        'height':red['height'],
        'width':red['width'],
        'pixels':pixels}


def color_filter_from_greyscale_filter(filt):
    """
    Given a filter that takes a greyscale image as input and produces a
    greyscale image as output, returns a function that takes a color image as
    input and produces the filtered color image.
    """
    def color_filter(image):
        #unpack and apply greyscale filter
        red=filt(unpack_colors(image,'r'))
        green=filt(unpack_colors(image,'g'))
        blue=filt(unpack_colors(image,'b'))
        #put together
        return combine_colors(red,green,blue)
    return color_filter


def make_blur_filter(n):
    """
    returns a filter that box blurs of size n
    """
    blur_kernel=[1/(n**2)]*(n**2)
    def blur_filter(image):
        output=correlate(image, blur_kernel, 'extend')
        round_and_clip_image(output)
        return output
    return blur_filter


def make_sharpen_filter(n):
    """
    returns a filter that sharpens
    """
    sharpen_kernel=[-1/(n**2)]*(n**2)
    sharpen_kernel[(n**2)//2]+=2
    def sharpen_filter(image):
        output=correlate(image,sharpen_kernel,'extend')
        round_and_clip_image(output)
        return output
    return sharpen_filter


def filter_cascade(filters):
    """
    Given a list of filters (implemented as functions on images), returns a new
    single filter such that applying that filter to an image produces the same
    output as applying each of the individual ones in turn.
    """
    def cumulative_filter(image):
        output=image
        for f in filters:
            output=f(output)
        return output
    return cumulative_filter
        


# SEAM CARVING

def seam_carving(image, ncols):
    """
    Starting from the given image, use the seam carving technique to remove
    ncols (an integer) columns from the image. Returns a new image.
    """
    output={
        'height':image['height'],
        'width':image['width'],
        'pixels':image['pixels'].copy()}
    i=0
    for iteration in range(ncols):
        grey_image=greyscale_image_from_color_image(output)
        energy=compute_energy(grey_image)
        cum_energy=cumulative_energy_map(energy)
        seam=minimum_energy_seam(cum_energy)
        output=image_without_seam(output,seam)
        print(i)
        i+=1
    return output


def greyscale_image_from_color_image(image):
    """
    Given a color image, computes and returns a corresponding greyscale image.

    Returns a greyscale image (represented as a dictionary).
    """
    pixels=[0]*len(image['pixels'])
    red=unpack_colors(image,'r')['pixels']
    green=unpack_colors(image,'g')['pixels']
    blue=unpack_colors(image,'b')['pixels']
    for i in range(len(pixels)):
        pixels[i]=round(.299*red[i]+.587*green[i]+.114*blue[i])
    return {
        'height':image['height'],
        'width':image['width'],
        'pixels':pixels}


def compute_energy(grey):
    """
    Given a greyscale image, computes a measure of "energy", in our case using
    the edges function from last week.

    Returns a greyscale image (represented as a dictionary).
    """
    return edges(grey)


def find_min_path(energy_map,x,y):
    """
    finds the index of the smallest cumulative energy pixel in the row above
    the inputted (x,y)
    """
    if x==0:
        smallest_value=min(
            energy_map['pixels'][get_index(energy_map,x,y-1)],
            energy_map['pixels'][get_index(energy_map,x+1,y-1)])
        smallest_index=energy_map['pixels'].index(smallest_value,get_index(energy_map,x,y-1))
    elif x==energy_map['width']-1:
        smallest_value=min(
            energy_map['pixels'][get_index(energy_map,x-1,y-1)],
            energy_map['pixels'][get_index(energy_map,x,y-1)])
        smallest_index=energy_map['pixels'].index(smallest_value,get_index(energy_map,x-1,y-1))
    else:
        smallest_value=min(
            energy_map['pixels'][get_index(energy_map,x-1,y-1)],
            energy_map['pixels'][get_index(energy_map,x,y-1)],
            energy_map['pixels'][get_index(energy_map,x+1,y-1)])
        smallest_index=energy_map['pixels'].index(smallest_value,get_index(energy_map,x-1,y-1))
    return smallest_index


def cumulative_energy_map(energy):
    """
    Given a measure of energy (e.g., the output of the compute_energy
    function), computes a "cumulative energy map" as described in the lab 2
    writeup.

    Returns a dictionary with 'height', 'width', and 'pixels' keys (but where
    the values in the 'pixels' array may not necessarily be in the range [0,
    255].
    """
    #create cumulative energy map image to return later on
    energy_map={
        'height':energy['height'],
        'width':energy['width'],
        'pixels':energy['pixels']}

    #first row
    for x in range(energy['width']):
        energy_map['pixels'][x]=energy['pixels'][x]
    #every other row
    for y in range(1,energy['height']):
        for x in range(energy['width']):
            index=find_min_path(energy_map,x,y)
            energy_map['pixels'][get_index(energy_map,x,y)]+=energy_map['pixels'][index]

    #return mutated correct energy map
    return energy_map


def minimum_energy_seam(cem):
    """
    Given a cumulative energy map, returns a list of the indices into the
    'pixels' list that correspond to pixels contained in the minimum-energy
    seam (computed as described in the lab 2 writeup).
    """
    #list of indices in the smallest path
    remove=[]
    #find smallest cumulative energy in bottom row
    bottom=cem['pixels'][get_index(cem,0,cem['height']-1) : get_index(cem,cem['width']-1,cem['height']-1)+1]
    least=min(bottom)
    bottom_index=bottom.index(least)
    index=bottom_index+(cem['width'])*(cem['height']-1)
    remove.append(index)
    #trace upward
    x,y=get_coords(cem,index)
    while index>cem['width']-1:
        index=find_min_path(cem,x,y)
        remove.append(index)
        x,y=get_coords(cem,index)
    #return
    return remove


def image_without_seam(image, seam):
    """
    Given a (color) image and a list of indices to be removed from the image,
    return a new image (without modifying the original) that contains all the
    pixels from the original image except those corresponding to the locations
    in the given list.
    """
    output={
        'height':image['height'],
        'width':image['width']-1,
        'pixels':image['pixels']}
    for index in seam:
        output['pixels'].pop(index)
    return output


# CUSTOM FEATURE: playing with color

og_color_scale=[0,51,102,153,204,255] #5 distinct regions of color that can be altered

def make_color_filter(ry=og_color_scale,gy=og_color_scale,by=og_color_scale):
    """
    creates a custom color filter that modifies r,g,b values like a color curve,
    modifiable in 5 sections each. input is three optional lists for r,g, and b,
    respectively, each length 6 starting at 0 ending at 255. outputs the filter.
    """
    import numpy as np
    assert len(og_color_scale)==len(ry)==len(gy)==len(by), 'Color scale must be broken into sections of 5!'
    def color_filter(image):
        #unpack colors
        r=unpack_colors(image,'r')['pixels']
        g=unpack_colors(image,'g')['pixels']
        b=unpack_colors(image,'b')['pixels']
        #perform interpolation
        new_r_pixels=np.interp(r,og_color_scale,ry)
        new_g_pixels=np.interp(g,og_color_scale,gy)
        new_b_pixels=np.interp(b,og_color_scale,by)
        #make sure pixels are integers
        new_r_pixels = new_r_pixels.astype(np.int)
        new_g_pixels = new_g_pixels.astype(np.int)
        new_b_pixels = new_b_pixels.astype(np.int)
        #combine colors and return
        new_r={
            'height':image['height'],
            'width':image['width'],
            'pixels':new_r_pixels}
        new_g={
            'height':image['height'],
            'width':image['width'],
            'pixels':new_g_pixels}
        new_b={
            'height':image['height'],
            'width':image['width'],
            'pixels':new_b_pixels}
        return combine_colors(new_r,new_g,new_b)
    return color_filter
    

def custom_feature():
    """
    call the color filter! I chose to make the bluers more blue, but there are infinite possibilities!
    """
    color_filter=make_color_filter(by=[10,60,150,175,230,255])
    og_kermie_cuterpie=load_color_image('kermie_cuterpie.jpg')
    blueified_kermie_cuterpie=color_filter(og_kermie_cuterpie)
    print(blueified_kermie_cuterpie['pixels'][0:10])
    save_color_image(blueified_kermie_cuterpie,'blueified_kermie_cuterpie.png')



# HELPER FUNCTIONS FOR LOADING AND SAVING COLOR IMAGES


def load_color_image(filename):
    """
    Loads a color image from the given file and returns a dictionary
    representing that image.

    Invoked as, for example:
       i = load_color_image('test_images/cat.png')
    """
    with open(filename, "rb") as img_handle:
        img = Image.open(img_handle)
        img = img.convert("RGB")  # in case we were given a greyscale image
        img_data = img.getdata()
        pixels = list(img_data)
        w, h = img.size
        return {"height": h, "width": w, "pixels": pixels}


def save_color_image(image, filename, mode="PNG"):
    """
    Saves the given color image to disk or to a file-like object.  If filename
    is given as a string, the file type will be inferred from the given name.
    If filename is given as a file-like object, the file type will be
    determined by the 'mode' parameter.
    """
    out = Image.new(mode="RGB", size=(image["width"], image["height"]))
    out.putdata(image["pixels"])
    if isinstance(filename, str):
        out.save(filename)
    else:
        out.save(filename, mode)
    out.close()


def load_greyscale_image(filename):
    """
    Loads an image from the given file and returns an instance of this class
    representing that image.  This also performs conversion to greyscale.

    Invoked as, for example:
       i = load_greyscale_image('test_images/cat.png')
    """
    with open(filename, "rb") as img_handle:
        img = Image.open(img_handle)
        img_data = img.getdata()
        if img.mode.startswith("RGB"):
            pixels = [
                round(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]) for p in img_data
            ]
        elif img.mode == "LA":
            pixels = [p[0] for p in img_data]
        elif img.mode == "L":
            pixels = list(img_data)
        else:
            raise ValueError("Unsupported image mode: %r" % img.mode)
        w, h = img.size
        return {"height": h, "width": w, "pixels": pixels}


def save_greyscale_image(image, filename, mode="PNG"):
    """
    Saves the given image to disk or to a file-like object.  If filename is
    given as a string, the file type will be inferred from the given name.  If
    filename is given as a file-like object, the file type will be determined
    by the 'mode' parameter.
    """
    out = Image.new(mode="L", size=(image["width"], image["height"]))
    out.putdata(image["pixels"])
    if isinstance(filename, str):
        out.save(filename)
    else:
        out.save(filename, mode)
    out.close()


if __name__ == "__main__":
    pass
