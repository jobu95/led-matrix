#include <led-matrix.h>
#include <content-streamer.h>
#include <Magick++.h>

#include <errno.h>
#include <fcntl.h>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <memory>
#include <signal.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

using namespace std;
using namespace Magick;
using rgb_matrix::RGBMatrix;
using rgb_matrix::FrameCanvas;

list<filesystem::path> getFilesFromFilename(const string &filename)
{
  list<filesystem::path> files;
  if (filesystem::path filepath(filename); filesystem::exists(filepath)) {
    files.push_back(move(filepath));
  } else {
    for (int i = 0; i < 1000; i++) {
      ostringstream oss;
      oss << setfill('0') << setw(3) << i << "_" << filepath.filename().string();
      filesystem::path cur_file(filepath);
      cur_file.replace_filename(oss.str());
      if (!filesystem::exists(cur_file)) {
        break;
      }
      files.push_back(move(cur_file));
    }
  }
  return files;
}

volatile bool interrupt_received = false;
static void InterruptHandler(int signo) {
  interrupt_received = true;
}

list<Image> loadFile(const std::string &filename) {
  list<Image> images;
  try {
    // Read a file into image object
    cout << "Reading from " << filename << "... " << flush;
    readImages(&images, filename);
    cout << "done" << endl;
  } catch (Exception &error_) {
    cout << "Caught exception: " << error_.what() << endl;
  }
  if (images.size() > 0) {
    cout << "  Width:           " << images.front().columns() << endl;
    cout << "  Height:          " << images.front().rows() << endl;
    cout << "  Depth:           " << images.front().depth() << endl;
    cout << "  #   of frames:   " << images.size() << endl;
    cout << "  Frame dur (ms):  " << images.front().animationDelay() * 10 << endl;
    cout << "  Iterations:      " << images.front().animationIterations() << endl;
    cout << "Converting to RGBMatrix format... " << flush;
  }
  return images;
}

void sendImagesToStream(const list<Image> &images,
    FrameCanvas *canvas_off_p,
    rgb_matrix::StreamWriter *stream_writer_p) {
  for (const auto &image : images) {
    for (auto y = 0; y < image.rows(); y++) {
      for (auto x = 0; x < image.columns(); x++) {
        const Magick::Color &c = image.pixelColor(x, y);
        canvas_off_p->SetPixel(x, y,
            c.quantumRed(),
            c.quantumGreen(),
            c.quantumBlue());
      }
    }
    const auto delay_us = image.animationDelay() * 1000;
    stream_writer_p->Stream(*canvas_off_p, delay_us);
    if (interrupt_received) {
      break;
    }
  }
  cout << "done" << endl;
}

void convertFileToStreamFile(const std::string &file_in, const std::string &file_out) {
  const auto images = loadFile(file_in);

}

int main(int argc,char **argv)
{
  if (2 != argc) {
    cerr << "Usage: " << argv[0] << " filename" << endl;
    return 1;
  }
  string filename(argv[1]);
  cout << "Filename: " << filename << endl;

  const auto files = getFilesFromFilename(filename);

  // Set up ImageMagick
  InitializeMagick(argv[0]);

  // Set up RGBMatrix
  signal(SIGTERM, InterruptHandler);
  signal(SIGINT, InterruptHandler);
  unique_ptr<RGBMatrix> matrix_p(nullptr);
  {
    RGBMatrix::Options defaults;
    defaults.hardware_mapping = "adafruit-hat-pwm";  // or e.g. "adafruit-hat"
    defaults.rows = 64;
    defaults.cols = 64;
    defaults.chain_length = 1;
    defaults.parallel = 1;
    defaults.show_refresh_rate = false;
    matrix_p.reset(rgb_matrix::CreateMatrixFromFlags(&argc, &argv, &defaults));
    if (matrix_p == nullptr) {
      return 1;
    }
  }

  FrameCanvas *canvas_off_p = matrix_p->CreateFrameCanvas();

  for (const auto &cur_file : files) {
    if (interrupt_received) {
      break;
    }
    // Convert PIL into RGBMatrix form
    const auto images = loadFile(cur_file.string());
    unique_ptr<rgb_matrix::StreamIO> stream_p;
    if (true) {
      stream_p = make_unique<rgb_matrix::MemStreamIO>();
    } else {
      const int stream_fd = open("out.stream", O_CREAT|O_WRONLY, 0644);
      if (-1 == stream_fd) {
        cerr << "Failed to create out.stream: " << strerror(errno) << endl;
        return 1;
      }
      stream_p = make_unique<rgb_matrix::FileStreamIO>(stream_fd);
    }
    auto stream_writer_p = make_unique<rgb_matrix::StreamWriter>(stream_p.get());

    // TODO remove stream_writer_p raw ptr
    sendImagesToStream(images, canvas_off_p, stream_writer_p.get());

    rgb_matrix::StreamReader image_stream_reader(stream_p.get());
    uint32_t delay_us = 0;
    while (!interrupt_received &&
        image_stream_reader.GetNext(canvas_off_p, &delay_us)) {
      canvas_off_p = matrix_p->SwapOnVSync(canvas_off_p);
      // TODO sleep until next frame
    }
  }
  return 0;
}

