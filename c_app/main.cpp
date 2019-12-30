#include <led-matrix.h>
#include <content-streamer.h>
#include <Magick++.h>

#include <chrono>
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
using namespace std::chrono;
using namespace Magick;
using rgb_matrix::RGBMatrix;
using rgb_matrix::FrameCanvas;

class FramePacer
{
  public:
    FramePacer()
      : m_now(high_resolution_clock::now())
    {}

    // Return true if we're on pace, false if we're behind by > 2 frames.
    bool waitFrame(const microseconds frame_dur_us) {
      bool on_pace = true;
      while (true) {
        auto now = high_resolution_clock::now();
        auto delta_us = duration_cast<microseconds>(now - m_now);
        if (delta_us > frame_dur_us) {
          if (delta_us > 2 * frame_dur_us) {
            on_pace = false;
          }
          break;
        }
        usleep(1000);
      }
      m_now += frame_dur_us;
      return on_pace;
    }

  private:
    high_resolution_clock::time_point m_now;
};

list<filesystem::path> getFilesFromFilename(const filesystem::path &filename)
{
  list<filesystem::path> files;
  if (filesystem::exists(filename)) {
    files.push_back(move(filename));
  } else {
    for (int i = 0; i < 1000; i++) {
      ostringstream oss;
      oss << setfill('0') << setw(3) << i << "_" << filename.filename().string();
      filesystem::path cur_file(filename);
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
static void InterruptHandler(int /*signo*/) {
  interrupt_received = true;
}

vector<Image> loadFile(const std::string &filename) {
  list<Image> image_ls;
  try {
    // Read a file into image object
    cout << "Reading from " << filename << "... " << flush;
    readImages(&image_ls, filename);
    cout << "done" << endl;
  } catch (Exception &error_) {
    cout << "Caught exception: " << error_.what() << endl;
  }
  if (image_ls.size() > 0) {
    cout << "  Width:           " << image_ls.front().columns() << endl;
    cout << "  Height:          " << image_ls.front().rows() << endl;
    cout << "  Depth:           " << image_ls.front().depth() << endl;
    cout << "  #   of frames:   " << image_ls.size() << endl;
    cout << "  Frame dur (ms):  " << image_ls.front().animationDelay() * 10 << endl;
    cout << "  Iterations:      " << image_ls.front().animationIterations() << endl;
  }
  vector<Image> image_vec;
  if (image_ls.size() > 1) {
    cout << "Coalescing GIF frames... " << flush;
    Magick::coalesceImages(&image_vec, image_ls.begin(), image_ls.end());
    cout << "done" << endl;
  } else {
    image_vec.push_back(move(image_ls.front()));
  }
  return image_vec;
}

void sendImagesToStream(const vector<Image> &images,
    FrameCanvas *canvas_off_p,
    rgb_matrix::StreamWriter *stream_writer_p) {
  cout << "Converting to RGBMatrix format... " << flush;
  for (const auto &image : images) {
    canvas_off_p->Clear(); // TODO is this necessary?
    for (size_t y = 0; y < image.rows(); y++) {
      for (size_t x = 0; x < image.columns(); x++) {
        const Magick::Color &c = image.pixelColor(x, y);
        canvas_off_p->SetPixel(x, y,
            c.quantumRed(),
            c.quantumGreen(),
            c.quantumBlue());
      }
    }
    const auto delay_us = image.animationDelay() * 10000;
    stream_writer_p->Stream(*canvas_off_p, delay_us);
    if (interrupt_received) {
      break;
    }
  }
  cout << "done" << endl;
}

unique_ptr<RGBMatrix> createMatrix(char **argv, const bool convert_to_stream)
{
  unique_ptr<RGBMatrix> matrix_p(nullptr);
  signal(SIGTERM, InterruptHandler);
  signal(SIGINT, InterruptHandler);

  RGBMatrix::Options matrix_options;
  rgb_matrix::RuntimeOptions runtime_opt;
  auto fake_argc = 1; // don't want to actually pass args to RGBMatrix
  if (!rgb_matrix::ParseOptionsFromFlags(&fake_argc, &argv, &matrix_options,
        &runtime_opt)) {
    cerr << "Failed to parse args" << endl;
    return matrix_p;
  }

  matrix_options.hardware_mapping = "adafruit-hat-pwm";  // or e.g. "adafruit-hat"
  matrix_options.rows = 64;
  matrix_options.cols = 64;
  matrix_options.chain_length = 1;
  matrix_options.parallel = 1;
  matrix_options.show_refresh_rate = false;
  runtime_opt.do_gpio_init = !convert_to_stream;
  matrix_p.reset(CreateMatrixFromOptions(matrix_options, runtime_opt));

  return matrix_p;
}

int main(int argc,char **argv)
{
  if (2 != argc) {
    cerr << "Usage: " << argv[0] << " filename" << endl;
    return 1;
  }
  filesystem::path filename(argv[1]);
  cout << "Filename: " << filename.string() << endl;
  const bool convert_to_stream = (filename.extension().string() != ".stream");
  if (convert_to_stream) {
    cout << "Converting file to .stream files" << endl;
  } else {
    cout << "Rendering to matrix" << endl;
  }

  // Set up ImageMagick
  InitializeMagick(argv[0]);

  // Set up RGBMatrix
  auto matrix_p = createMatrix(argv, convert_to_stream);
  auto canvas_off_p = matrix_p->CreateFrameCanvas();
  if (!matrix_p || !canvas_off_p) {
    cerr << "Failed to get matrix or off-screen canvas" << endl;
  }

  for (const auto &cur_file : getFilesFromFilename(filename)) {
    if (interrupt_received) {
      break;
    }
    if (convert_to_stream) {
      cerr << "Converting " << cur_file.string() << endl;
      // Convert PIL into RGBMatrix form
      auto new_file(cur_file);
      new_file.replace_extension(".stream");
      const int stream_fd = open(new_file.string().c_str(), O_CREAT|O_WRONLY, 0644);
      if (-1 == stream_fd) {
        cerr << "Failed to create " << new_file.string() << ": " << strerror(errno) << endl;
        return 1;
      }
      auto stream_p = make_unique<rgb_matrix::FileStreamIO>(stream_fd);
      // Write out stream
      auto stream_writer_p = make_unique<rgb_matrix::StreamWriter>(stream_p.get());
      const auto images = loadFile(cur_file.string());
      sendImagesToStream(images, canvas_off_p, stream_writer_p.get());
    } else {
      cerr << "Displaying " << cur_file.string() << endl;
      // Open RGBMatrix stream file for reading
      const int stream_fd = open(cur_file.string().c_str(), O_RDONLY);
      if (-1 == stream_fd) {
        cerr << "Failed to open " << cur_file.string() << ": " << strerror(errno) << endl;
        return 1;
      }
      rgb_matrix::FileStreamIO stream(stream_fd);
      // Display stream
      rgb_matrix::StreamReader image_stream_reader(&stream);
      uint32_t delay_us = 0;
      class FramePacer pacer;
      while (!interrupt_received &&
          image_stream_reader.GetNext(canvas_off_p, &delay_us)) {
        if (!pacer.waitFrame(microseconds(delay_us))) {
          cerr << "skipping frame" << endl;
          continue;
        }
        canvas_off_p = matrix_p->SwapOnVSync(canvas_off_p);
        // TODO sleep until next frame
      }
    }
  }
  return 0;
}

