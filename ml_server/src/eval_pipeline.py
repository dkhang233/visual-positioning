import argparse
from pathlib import Path
import logging
from hloc import (
    extract_features,
    localize_sfm,
    logger,
    match_features,
    pairs_from_retrieval,
    pairs_from_covisibility,
    triangulation
)
from eval_utils import create_query_list_with_intrinsics, evaluate, create_reference_sfm, split_data

import pdb

logging.basicConfig(level=logging.INFO)

def eval_model(images,
    gt_dir,
    outputs,
    results,
    ref_per_query,
    num_covis,
    num_loc
    ):
    gt_model = gt_dir / "sparse/0"

    outputs.mkdir(exist_ok=True, parents=True)

    sub_gt_model = outputs / "sub_gt_model"
    ref_sfm = outputs / "sfm_superpoint+superglue"
    query_list = outputs / "query_list_with_intrinsics.txt"
    sfm_pairs = outputs / f"pairs-db-covis{num_covis}.txt"
    loc_pairs = outputs / f"pairs-query-netvlad{num_loc}.txt"

    feature_conf = {
        "output": "feats-superpoint-n4096-r1024",
        "model": {
            "name": "superpoint",
            "nms_radius": 3,
            "max_keypoints": 4096,
        },
        "preprocessing": {
            "grayscale": True,
            "resize_max": 1024,
        },
    }

    matcher_conf = match_features.confs["superglue"]
    retrieval_conf = extract_features.confs["netvlad"]


    [ref_list, test_list] = split_data(gt_model, outputs, ref_per_query)

    # Create reference model
    create_reference_sfm(gt_model , sub_gt_model , test_list, ext=".bin")

    # Create query list with intrinsics
    create_query_list_with_intrinsics(
        gt_model, query_list, test_list, ext=".bin", image_dir=images
    )

    with open(test_list, "r") as f:
        query_seqs = {q.split("/")[0] for q in f.read().rstrip().split("\n")}


    # Extract global descriptors
    global_descriptors = extract_features.main(retrieval_conf, images, outputs)

    # Extract local features
    features = extract_features.main(feature_conf, images, outputs, as_half=True)

    # Ghép cặp cho các ảnh dùng tọa reference model
    pairs_from_covisibility.main(sub_gt_model, sfm_pairs, num_matched=num_covis)

    # Matching features cho các ảnh tạo reference model
    sfm_matches = match_features.main(
        matcher_conf, sfm_pairs, feature_conf["output"], outputs
    )

    # Tạo reference model
    triangulation.main(
        ref_sfm, sub_gt_model, images, sfm_pairs, features, sfm_matches
    )

    pdb.set_trace()

    # Ghép các cặp ảnh cho các ảnh query
    pairs_from_retrieval.main(
        global_descriptors,
        loc_pairs,
        num_loc,
        db_model=sub_gt_model,
        query_prefix=query_seqs,
    )

    # Matching features cho các ảnh tạo query
    loc_matches = match_features.main(
        matcher_conf, loc_pairs, feature_conf["output"], outputs
    )

    if results is None:
        results = outputs / "result.txt"

    # Localize các ảnh query
    localize_sfm.main(
        ref_sfm,
        query_list,
        loc_pairs,
        features,
        loc_matches,
        results,
        covisibility_clustering=False,
        prepend_camera_name=False,
    )

    logger.info(f'Evaluate result')
    evaluate(
        gt_model,
        results,
        ext=".bin"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--images",
        type=Path,
        required=True,
        help="Path to the images directory",
    )
    parser.add_argument(
        "--gt_dir",
        type=Path,
        required=True,
        help="Path to the ground truth directory",
    )
    parser.add_argument(
        "--outputs",
        type=Path,
        required=True,
        help="Path to the outputs directory",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=None,
        help="Path to the results file, default: outputs/result.txt",
    )
    parser.add_argument(
        "--ref_per_query",
        type=int,
        default=4,
        help="Number of reference images per query image, default: %(default)s",
    )
    parser.add_argument(
        "--num_covis",
        type=int,
        default=20,
        help="Number of image pairs for SfM, default: %(default)s",
    )
    parser.add_argument(
        "--num_loc",
        type=int,
        default=10,
        help="Number of image pairs for loc, default: %(default)s",
    )
    args = parser.parse_args()
    eval_model(args.images,
        args.gt_dir,
        args.outputs,
        args.results,
        args.ref_per_query,
        args.num_covis,
        args.num_loc
    )

# python dkhang/evaluate-model/eval_pipeline.py --images /media/slam/Storage500GB/Minh-Khang-Workspace/hloc-glomap/data/lab/pro-lab/images --gt_dir /media/slam/Storage500GB/Minh-Khang-Workspace/hloc-glomap/data/lab/pro-lab/hloc-data/colmap-superpoint_aachen-superglue --outputs /media/slam/Storage500GB/Minh-Khang-Workspace/hloc-glomap/data/lab/evaluate-pro-lab 

