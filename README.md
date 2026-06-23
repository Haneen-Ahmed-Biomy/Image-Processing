# HANEEN | Image Processing Studio 🎨✨

A modern, feature-rich desktop application for image processing and computer vision tasks. Built with Python, CustomTkinter, and OpenCV, this studio provides an intuitive graphical interface for applying a wide variety of mathematical operations, morphological transformations, and stylization filters to images in real-time.

## 🚀 Features

### Modern & Responsive UI
* **CustomTkinter Interface:** A sleek, dark-themed UI with categorized tool cards.
* **Integrated Gallery:** Upload multiple images and easily switch between them.
* **Interactive Viewport:** Real-time preview of image edits.
* **Live Histogram:** Automatically generates and updates RGB or Grayscale histograms using Matplotlib.
* **Undo/Reset System:** Easily revert mistakes or reset to the original image.

### Image Processing Capabilities (Powered by OpenCV)
* **Arithmetic & Blending:** Add, subtract, find absolute differences, and perform alpha blending between two images.
* **RGB Extraction:** Isolate Red, Green, or Blue color channels.
* **Tonal Adjustments:** Real-time sliders for Brightness and Contrast, plus Histogram Stretching, Weighted Grayscale, and Intensity Inversion.
* **Threshold & Dithering:** Apply Binary thresholding, automatic Otsu's thresholding, and Floyd-Steinberg dithering.
* **Filters & Noise Repair:** Add Salt & Pepper noise, and repair images using Median, Mean, Min, and Max filters.
* **Morphological Operations:** Erode, Dilate, Open, and Close images.
* **Stylization:** One-click filters for Sharpening, Vintage Sepia, and a Cartoonify effect.

## 🛠️ Prerequisites

Before you begin, ensure you have Python 3.8+ installed on your system. You will need to install the following dependencies:

```bash
pip install customtkinter Pillow opencv-python matplotlib numpy