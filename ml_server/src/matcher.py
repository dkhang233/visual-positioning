from hloc import pairs_from_retrieval
from pathlib import Path
from hloc.utils.io import list_h5_names
import h5py
import torch
import numpy as np
from hloc import match_features

image_retrival_ref = Path("/media/slam/Storage500GB/Minh-Khang-Workspace/hloc-glomap/data/lab/pro-lab/hloc-data/colmap-superpoint_aachen-superglue/global-feats-netvlad.h5")
image_retrival_q = Path("data/lab/query/global-feats-netvlad.h5")
pairs_path = image_retrival_q.parent / "pairs.txt"

def main():
    path = Path("/media/slam/Storage500GB/Minh-Khang-Workspace/hloc-glomap/data/lab/query/local_match_data.h5")
    with h5py.File(str(path), "r", libver="latest") as hfile:
        pair = match_features.names_to_pair("lab_query.jpg", "frame_00009.jpg")
        matches = hfile[pair]["matches0"].__array__()
        scores = hfile[pair]["matching_scores0"].__array__()
    idx = np.where(matches != -1)[0]
    matches = np.stack([idx, matches[idx]], -1)
    scores = scores[idx]
    return matches, scores


if __name__ == "__main__":
    main()