#pragma once

#include <filesystem>
#include <list>
#include <map>
#include <string>
#include <set>
#include <vector>

// Takes a manifest in CSV format:
//  # file_basename|shocking_score_1_to_3|tags|n_iterations
//  # tags: animal, dancing, cute, funny, meme, eyecandy
// and produces randomized playlists.
class PlaylistGenerator
{
  public:
    struct PlaylistEntry
    {
      PlaylistEntry(std::filesystem::path &&f, int s,
          std::vector<std::string> &&t, int i)
        : filename(f), shock_score(s), tags(t), iterations(i)
      {}

      std::filesystem::path filename;
      int shock_score;
      std::vector<std::string> tags;
      int iterations;
    };

    PlaylistGenerator()
      : m_max_shock_score(0)
    {}

    typedef std::shared_ptr<PlaylistEntry> EntryPtr;

    bool parseManifest(const std::filesystem::path &manifest_path);

    std::list<EntryPtr> getPlaylist(const size_t length) const;

  private:
    int m_max_shock_score;

    std::set<EntryPtr> m_entry_ptr_set;
    std::map<std::string, std::list<EntryPtr>> m_tag_to_entries;
};

