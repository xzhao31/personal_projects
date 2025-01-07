#include "npr.h"
#include "filtering.h"
#include "matrix.h"
#include <algorithm>
#include <math.h>

using namespace std;

void brush(Image &im, int x, int y, vector<float> color, const Image &texture)
{
	// Draws a brushstroke defined by texture and color at (x,y) in im

	// cout << texture.width() << "height" << texture.height() << endl;
	// cout << color.size() << endl;
	int dx_offset = texture.width() / 2;
	int dy_offset = texture.height() / 2;
	for (int dx = -dx_offset; dx < texture.width() - dx_offset; dx++)
	{
		for (int dy = -dy_offset; dy < texture.height() - dy_offset; dy++)
		{
			if (x + dx >= 0 && x + dx < im.width() && y + dy >= 0 && y + dy < im.height())
			{
				for (int z = 0; z < im.channels(); z++)
				{
					im(x + dx, y + dy, z) = texture(dx + dx_offset, dy + dy_offset, z) * color[z] + (1 - texture(dx + dx_offset, dy + dy_offset, z)) * im(x + dx, y + dy, z);
				}
			}
		}
	}
	return;
}

void singleScalePaint(const Image &im, Image &out, const Image &texture, int size, int N, float noise)
{
	// Create painted rendering by splatting brushstrokes at N random locations
	// in your ouptut image
	float factor = min(float(size) / texture.width(), float(size) / texture.height());
	Image scaled_texture = scaleLin(texture, factor);
	for (int i = 0; i < N; i++)
	{
		int x = rand() % out.width();
		int y = rand() % out.height();
		vector<float> color = {im.smartAccessor(x, y, 0, true) * (1 - noise / 2 + noise * rand() / RAND_MAX), im.smartAccessor(x, y, 1, true) * (1 - noise / 2 + noise * rand() / RAND_MAX), im.smartAccessor(x, y, 2, true) * (1 - noise / 2 + noise * rand() / RAND_MAX)};
		brush(out, x, y, color, scaled_texture);
	}
	return;
}

void singleScalePaintImportance(const Image &im, const Image &importance, Image &out, const Image &texture, int size, int N, float noise)
{
	// Create painted rendering but vary the density of the strokes according to
	// an importance map
	float factor = min(float(size) / texture.width(), float(size) / texture.height());
	Image scaled_texture = scaleLin(texture, factor);
	// find number of iterations
	float p_total = 0;
	for (int x = 0; x < importance.width(); x++)
	{
		for (int y = 0; y < importance.height(); y++)
		{
			if (importance(x, y, 0) > 0 && importance(x, y, 0) < 1)
			{
				p_total += importance(x, y, 0);
			}
			else if (importance(x, y, 0) >= 1)
			{
				p_total += 1;
			}
		}
	}
	float p_accept = p_total / (importance.width() * importance.height());
	// main loop
	for (int i = 0; i < N / p_accept; i++)
	{
		int x = rand() % out.width();
		int y = rand() % out.height();
		if (rand() / RAND_MAX < importance(x, y, 0))
		{
			vector<float> color = {im.smartAccessor(x, y, 0, true) * (1 - noise / 2 + noise * rand() / RAND_MAX), im.smartAccessor(x, y, 1, true) * (1 - noise / 2 + noise * rand() / RAND_MAX), im.smartAccessor(x, y, 2, true) * (1 - noise / 2 + noise * rand() / RAND_MAX)};
			brush(out, x, y, color, scaled_texture);
		}
	}
	return;
}

Image sharpnessMap(const Image &im, float sigma)
{
	// Calculate sharpness mask
	Image lum = lumiChromi(im)[0];
	Image lum_low = gaussianBlur_2D(lum, sigma);
	Image lum_high = (lum - lum_low) * (lum - lum_low);
	Image lum_sharp = gaussianBlur_2D(lum_high, 4 * sigma);
	return lum_sharp / lum_sharp.max();
}

void painterly(const Image &im, Image &out, const Image &texture, int N, int size, float noise)
{
	// Create painterly rendering using a first layer of coarse strokes followed
	// by smaller strokes in high detail areas
	singleScalePaint(im, out, texture, size, N, noise);
	Image sharpness = sharpnessMap(im);
	singleScalePaintImportance(im, sharpness, out, texture, size / 4, N, noise);
}

Image computeTensor(const Image &im, float sigmaG, float factorSigma)
{
	// Compute xx/xy/yy Tensor of an image. (stored in that order)
	Image lum = lumiChromi(im)[0];
	Image blurred = gaussianBlur_separable(lum, sigmaG);
	Image Ix = gradientX(blurred);
	Image Iy = gradientY(blurred);
	Image M(im.width(), im.height(), 3);
	for (int x = 0; x < im.width(); x++)
	{
		for (int y = 0; y < im.height(); y++)
		{
			M(x, y, 0) = Ix(x, y) * Ix(x, y);
			M(x, y, 1) = Ix(x, y) * Iy(x, y);
			M(x, y, 2) = Iy(x, y) * Iy(x, y);
		}
	}
	Image M_weighted = gaussianBlur_separable(M, sigmaG * factorSigma);
	return M_weighted;
}

Image testAngle(const Image &im, float sigmaG, float factor)
{
	// Extracts orientation of features in im. Angles should be mapped
	// to [0,1]
	float pi = 3.1415926535897;
	Image tensor = computeTensor(im, sigmaG, factor);
	Image out(im.width(), im.height(), 1);
	Eigen::EigenSolver<Matrix> solver;
	for (int x = 0; x < im.width(); x++)
	{
		for (int y = 0; y < im.height(); y++)
		{
			Matrix M(2, 2);
			M << tensor(x, y, 0), tensor(x, y, 1), tensor(x, y, 1), tensor(x, y, 2);
			solver.compute(M);
			Vec2f evector;
			if (solver.eigenvalues()[0].real() < solver.eigenvalues()[1].real())
			{ // first smaller
				evector = solver.eigenvectors().col(0).real();
			}
			else
			{ // second smaller
				evector = solver.eigenvectors().col(1).real();
			}
			float angle = atan2(evector[1], evector[0]);
			angle = (angle < 0) ? angle + 2 * pi : angle;
			angle /= (2 * pi);
			out(x, y) = 1 - angle;
		}
	}
	return out;
}

vector<Image> rotateBrushes(const Image &im, int nAngles)
{
	// helper function
	// Returns list of nAngles images rotated by 1*2pi/nAngles
	vector<Image> rotatedBrushes;
	float pi = 3.1415926535897;
	for (int i = 0; i < nAngles; i++)
	{
		float theta = float(i) / nAngles * 2 * pi;
		Image rotated = rotate(im, theta);
		rotatedBrushes.push_back(rotated);
	}
	return rotatedBrushes;
}

void singleScaleOrientedPaint(const Image &im, const Image &importance, Image &out, const Image &tensor, const Image &texture, int size, int N, float noise, int nAngles)
{
	// Similar to singleScalePaintImportant but brush strokes are oriented
	// according to tensor
	float pi = 3.1415926535897;
	// rotated textures
	float factor = min(float(size) / texture.width(), float(size) / texture.height());
	Image scaled_texture = scaleLin(texture, factor);
	vector<Image> rotated_textures = rotateBrushes(scaled_texture, nAngles);
	// angles
	Image angle_textures(im.width(), im.height(), 1);
	Eigen::EigenSolver<Matrix> solver;
	for (int x = 0; x < im.width(); x++)
	{
		for (int y = 0; y < im.height(); y++)
		{
			Matrix M(2, 2);
			M << tensor(x, y, 0), tensor(x, y, 1), tensor(x, y, 1), tensor(x, y, 2);
			solver.compute(M);
			Vec2f evector = (solver.eigenvalues()[0].real() < solver.eigenvalues()[1].real()) ? solver.eigenvectors().col(0).real() : solver.eigenvectors().col(1).real();
			float angle = atan2(evector[1], evector[0]);
			angle = (angle < 0) ? angle + 2 * pi : angle;
			angle = 1 - angle / (2 * pi);
			angle_textures(x, y, 0) = floor(angle * nAngles);
		}
	}
	// find number of iterations
	float p_total = 0;
	for (int x = 0; x < importance.width(); x++)
	{
		for (int y = 0; y < importance.height(); y++)
		{
			if (importance(x, y, 0) > 0 && importance(x, y, 0) < 1)
			{
				p_total += importance(x, y, 0);
			}
			else if (importance(x, y, 0) >= 1)
			{
				p_total += 1;
			}
		}
	}
	float p_accept = p_total / (importance.width() * importance.height());
	// main loop
	for (int i = 0; i < N / p_accept; i++)
	{
		int x = rand() % out.width();
		int y = rand() % out.height();
		if (rand() / RAND_MAX < importance(x, y, 0))
		{
			vector<float> color = {im.smartAccessor(x, y, 0, true) * (1 - noise / 2 + noise * rand() / RAND_MAX), im.smartAccessor(x, y, 1, true) * (1 - noise / 2 + noise * rand() / RAND_MAX), im.smartAccessor(x, y, 2, true) * (1 - noise / 2 + noise * rand() / RAND_MAX)};
			brush(out, x, y, color, rotated_textures[angle_textures(x, y, 0)]);
		}
	}
	return;
}

void orientedPaint(const Image &im, Image &out, const Image &texture, int N, int size, float noise)
{
	// Similar to painterly() but strokes are oriented along the directions of maximal structure
	Image importance(out.width(), out.height(), 3);
	importance.set_color(1, 1, 1);
	Image tensor = computeTensor(im);
	singleScaleOrientedPaint(im, importance, out, tensor, texture, size, N, noise);
	Image sharpness = sharpnessMap(im);
	singleScaleOrientedPaint(im, sharpness, out, tensor, texture, size / 4, N, noise);
}
