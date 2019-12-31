#include "PlaylistGenerator.h"

#include <iostream>

// Testbed main used for developing on my mac :)

using namespace std;

int main()
{
  PlaylistGenerator g;
  if (!g.parseManifest(filesystem::path("manifest.txt"))) {
    return 1;
  }
  const auto playlist = g.getPlaylist(100);
  for (const auto &entry : playlist) {
    // TODO
  }
  return 0;
}

