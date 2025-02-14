#ifndef __BASICIMAGEMANIPULATION__H
#define __BASICIMAGEMANIPULATION__H

#include "Image.h"
#include <cmath>
#include <iostream>

using namespace std;

Image create_special();

Image brightness(const Image &im, float factor);
Image contrast(const Image &im, float factor, float midpoint = 0.5);

static const float weight_init[3] = {0.299, 0.587, 0.114};
Image color2gray(const Image &im,
                 const std::vector<float> &weights =
                     std::vector<float>(weight_init, weight_init + 3));

std::vector<Image> lumiChromi(const Image &im);

Image lumiChromi2rgb(const vector<Image> &lc);

Image brightnessContrastLumi(const Image &im, float brightF, float contrastF,
                             float midpoint = 0.3);

Image rgb2yuv(const Image &im);

Image yuv2rgb(const Image &im);

Image saturate(const Image &im, float k);

Image gamma_code(const Image &im, float gamma);

Image quantize(const Image &im, int bits);

std::vector<Image> gamma_test(const Image &im, int bits, float gamma);

std::vector<Image> spanish(const Image &im);

Image grayworld(const Image &in);

Image scaleNN(const Image &im, float factor);
float interpolateLin(const Image &im, float x, float y, int z,
                     bool clamp = false);
Image scaleLin(const Image &im, float factor);
Image scaleBicubic(const Image &im, float factor, float B, float C);
Image scaleLanczos(const Image &im, float factor, float a);

Image rotate(const Image &im, float theta);

#endif