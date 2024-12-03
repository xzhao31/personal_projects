/* --------------------------------------------------------------------------
 testing
 * ------------------------------------------------------------------------*/

#include "Image.h"
#include "basicImageManipulation.h"
#include "npr.h"
#include <iomanip>
#include <iostream>
#include <sstream>
#include <vector>

using namespace std;

int main()
{
  // Image im_castle("input/castle.png");
  // vector<float> color = {1, 1, 1};
  // Image texture("input/brush.png");
  // brush(im_castle, 50, 50, color, texture);
  // im_castle.write("Output/brush_castle.png");

  // Image im_china("input/china.png");
  // Image out_china(im_china.width(), im_china.height(), 3);
  // Image texture("Input/longBrush.png");

  // normal brush
  // singleScalePaint(im_china, out_china, texture, 10, 100000);
  // out_china.write("Output/china_brush.png");

  // importance brush
  // Image importance(im_china.width(), im_china.height(), 3);
  // importance.create_rectangle(100, 300, 200, 500, 1, 1, 1);
  // singleScalePaintImportance(im_china, importance, out_china, texture);
  // out_china.write("Output/china_brush_importance.png");

  // two scale painterly
  // painterly(im_china, out_china, texture);
  // out_china.write("Output/china_brush_twoscale.png");

  // Image im_round("Input/round.png");
  // Image angle = testAngle(im_round);
  // angle.write("Output/angle_round.png");

  // testing single scale oriented
  // Image importance(im_round.width(), im_round.height(), 3);
  // importance.create_rectangle(10, 20, 300, 300, 1, 1, 1);
  // importance.write("Output/importance.png");
  // Image out(im_round.width(), im_round.height(), 3);
  // Image tensor = computeTensor(im_round);
  // Image texture("Input/longBrush.png");
  // singleScaleOrientedPaint(im_round, importance, out, tensor, texture, 30, 1000, 0.05);
  // out.write("Output/oriented_single.png");

  // testing two scale oriented
  // Image im_round("Input/round.png");
  // Image out(im_round.width(), im_round.height(), 3);
  // Image texture("Input/longBrush.png");
  // orientedPaint(im_round, out, texture, 1000);
  // out.write("Output/two_scale_oriented.png");

  Image im_china("Input/china.png");
  // Image out(im_china.width(), im_china.height(), 3);
  Image out("Input/china.png");
  Image texture("Input/longBrush.png");
  orientedPaint(im_china, out, texture, 1000);
  out.write("Output/china_two_scale_oriented_2.png");
}
