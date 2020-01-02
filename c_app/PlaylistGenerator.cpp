#include "PlaylistGenerator.h"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <time.h>

using namespace std;

static vector<string> tokenize(const string &line, const char delim)
{
  vector<string> tokens;
  istringstream line_iss(line);
  string token;
  while (getline(line_iss, token, delim)) {
    tokens.push_back(token);
  }
  return tokens;
}

static void parseManifestCommonError(const std::string &line)
{
  cerr << "Line: " << line << endl;
  cerr << "Skipping line" << endl;
}

bool PlaylistGenerator::parseManifest(const filesystem::path &manifest_path)
{
  if (!filesystem::exists(manifest_path)) {
    cerr << "Manifest does not exist at " << manifest_path.string() << endl;
    return false;
  }

  ifstream manifest_ifs(manifest_path.string().c_str());
  string line;
  while (getline(manifest_ifs, line)) {
    if (line.size() == 0 || line[0] == '#') {
      continue;
    }
    const auto tokens = tokenize(line, '|');
    if (tokens.size() != 4) {
      cerr << "Invalid manifest line, does not have 3 members, has " <<
        tokens.size() << endl;
      parseManifestCommonError(line);
      continue;
    }
    auto filename    = filesystem::path(tokens[0]);
    filename.replace_extension(".stream");
    auto shock_score = 0;
    try {
      shock_score = stoi(tokens[1]);
    } catch (const exception &error) {
      cerr << "Invalid manifest line, non-integer shock score: " << error.what() << endl;
      parseManifestCommonError(line);
      continue;
    }
    m_max_shock_score = max(shock_score, m_max_shock_score);
    auto tags        = tokenize(tokens[2], ',');
    if (tags.size() == 0) {
      cerr << "Invalid manifest line, has no tags" << endl;
      parseManifestCommonError(line);
      continue;
    }
    auto iterations = 0;
    try {
      iterations = stoi(tokens[3]);
    } catch (const exception &error) {
      cerr << "Invalid manifest line, non-integer iterations: " << error.what() << endl;
      parseManifestCommonError(line);
      continue;
    }
    // Done parsing line, store result
    auto entry_p = make_shared<PlaylistEntry>(move(filename), shock_score,
        move(tags), iterations);
    m_entry_ptr_set.insert(entry_p);
    for (auto tag : entry_p->tags) {
      m_tag_to_entries[tag].push_back(entry_p);
    }
  }

  return true;
}

static auto goodEnoughRand(const size_t cap)
{
  uniform_int_distribution<size_t> distribution(0, cap);
  random_device rd;
  default_random_engine generator(rd());
  return distribution(generator);
}

static auto getWeight(const PlaylistGenerator::EntryPtr &ptr, const int max_shock_score,
    const std::string &current_tag)
{
  // Shocking videos are given a lower weight, less shocking videos are given a
  // higher weight.
  const auto shock_weight = (max_shock_score - ptr->shock_score + 1);
  // Videos that match the current tag are 4x more likely to be picked than
  // non-matching videos.
  const bool matches = (find(ptr->tags.begin(), ptr->tags.end(), current_tag) != ptr->tags.end());
  const auto match_factor = matches ? 4 : 1;
  // Return the product of match factor + shock weight.
  return match_factor * shock_weight;
}

static string pickRandomTag(const PlaylistGenerator::EntryPtr &entry_p)
{
  const auto which_tag = goodEnoughRand(entry_p->tags.size());
  auto tag_iter = entry_p->tags.begin();
  if (which_tag > 0) {
    advance(tag_iter, which_tag - 1);
  }
  return *tag_iter;
}

std::list<PlaylistGenerator::EntryPtr> PlaylistGenerator::getPlaylist(
    const size_t length) const
{
  // pick first video randomly
  const size_t n_videos = m_entry_ptr_set.size();
  const auto which_video = goodEnoughRand(n_videos);
  auto entry_iter = m_entry_ptr_set.begin();
  if (which_video > 0) {
    advance(entry_iter, which_video - 1);
  }
  list<EntryPtr> playlist;
  playlist.push_back(*entry_iter);
  // pick first tag randomly
  auto cur_tag = pickRandomTag(*entry_iter);
  set<EntryPtr> cur_tag_history;

  while (playlist.size() < length) {
    const auto &cur_entry = playlist.back();
    cerr << "Entry: " << cur_entry->filename.string() << endl;
    cerr << "Tag:   " << cur_tag << endl;
    cur_tag_history.insert(cur_entry);

    // find all videos that haven't been played yet under the current tag
    set<EntryPtr> candidates;
    set_difference(m_entry_ptr_set.begin(), m_entry_ptr_set.end(),
        cur_tag_history.begin(), cur_tag_history.end(),
        inserter(candidates, candidates.begin()));

    // assign each next hop a weight based on shock scores & whether the tag
    // matches our "current" tag.
    // Add up weights, and pick random number in [0, sum_weights]. Whichever
    // video owns the integer in that range gets picked.
    std::vector<decltype(cur_entry->shock_score)> weights;
    decltype(cur_entry->shock_score) weights_sum = 0;
    for (const auto &candidate : candidates) {
      const auto weight = getWeight(candidate, m_max_shock_score, cur_tag);
      weights.push_back(weight);
      weights_sum += weight;
    }
    const auto which_number = goodEnoughRand(weights_sum);
    size_t i = 0;
    size_t acc = 0;
    for (const auto &candidate : candidates) {
      acc += weights[i++];
      if (acc > which_number) {
        playlist.push_back(candidate);
        break;
      }
    }

    // update tag if needed
    const auto& next_entry = playlist.back();
    cerr << "Next entry: " << next_entry->filename.string() << endl;
    if (find(next_entry->tags.begin(), next_entry->tags.end(), cur_tag) ==
        next_entry->tags.end()) {
      cerr << "Picking new tag" << endl;
      // previous tag is no longer in use. Pick first tag we have in common.
      // TODO randomizing this choice would be ideal.
      for (const auto &cur_entry_tag : cur_entry->tags) {
        if (const auto tag_iter =
            find(next_entry->tags.begin(), next_entry->tags.end(), cur_entry_tag);
            tag_iter != next_entry->tags.end()) {
          cur_tag = cur_entry_tag;
          cur_tag_history.clear();
          break;
        }
      }
      // If no tags in common, pick first tag from next entry.
      if (const auto tag_iter =
          find(next_entry->tags.begin(), next_entry->tags.end(), cur_tag);
          tag_iter == next_entry->tags.end()) {
        cur_tag = pickRandomTag(next_entry);
      }
    }
    cerr << "Next tag: " << cur_tag << endl;
  }

  return playlist;
}

