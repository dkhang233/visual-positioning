from pathlib import Path
from collections import defaultdict
import pdb

from hloc import extract_features, extractors, matchers, pairs_from_retrieval, match_features, visualization,localize_sfm
# from hloc.extract_features import ImageDataset
# from hloc.fast_localize import localize
# from hloc.utils import viz_3d, io
# from hloc.utils.base_model import dynamic_load
# from hloc.utils.io import list_h5_names
# from hloc.utils.parsers import names_to_pair

import pycolmap
# import numpy as np
# from scipy.spatial.transform import Rotation
# import torch


def main():
    LOCAL_FEATURE_EXTRACTOR = 'superpoint_aachen'
    GLOBAL_DESCRIPTOR_EXTRACTOR = 'netvlad'
    MATCHER = 'superglue'

    img_path = '/media/slam/Storage500GB/Minh-Khang-Workspace/hloc-glomap/data/lab/pro-lab/images' 
    dataset_path = '/media/slam/Storage500GB/Minh-Khang-Workspace/hloc-glomap/data/lab/evaluate-pro-lab/hloc-data'
    query_path = Path('/media/slam/Storage500GB/Minh-Khang-Workspace/hloc-glomap/data/lab/evaluate-pro-lab/query')

    img_path = Path(img_path)

    local_feature_conf = extract_features.confs[LOCAL_FEATURE_EXTRACTOR]
    global_descriptor_conf = extract_features.confs[GLOBAL_DESCRIPTOR_EXTRACTOR]
    match_features_conf = match_features.confs[MATCHER]

    dataset = Path(dataset_path)
    db_global_descriptors_path = (dataset / global_descriptor_conf['output']).with_suffix('.h5')
    db_local_features_path = (dataset / "features").with_suffix('.h5')

    # Use the scaled reconstruction if it exists
    # db_reconstruction = dataset / 'scaled_sfm_reconstruction'
    # if not db_reconstruction.exists():
    #     db_reconstruction = dataset / 'sfm_reconstruction'
    db_reconstruction = dataset / 'sparse/0'
    # db_image_dir = Path("/media/slam/Storage500GB/Minh-Khang-Workspace/hloc-glomap/data/lab/pro-lab/images")

    query_image_names = []
    with open(query_path.parent / "query_list.txt", "r") as f:
        query_image_names = [line.strip() for line in f.readlines()]  
    
    # Query data
    query_global_matches_path = query_path / 'global_match_pairs.txt'
    query_local_match_path = query_path / 'local_match_data.h5'
    query_results = query_path / 'query_results.txt'

    # Extarct local features and global descriptor for the new image
    query_local_features_path = extract_features.main(
        conf = local_feature_conf,
        image_dir = img_path,
        export_dir = query_path,
        image_list = query_image_names
    )

    query_global_descriptor_path = extract_features.main(
        conf = global_descriptor_conf,
        image_dir = img_path,
        export_dir = query_path,
        image_list = query_image_names
    )

    ## Use global descriptor matching to get candidate matches
    pairs_from_retrieval.save_global_candidates_for_query(
        db_descriptors = db_global_descriptors_path,
        query_descriptor = query_global_descriptor_path,
        query_image_names = query_image_names,
        num_matched = 10,
        output_file_path = query_global_matches_path
    )


    ## Match the query image against the candidate pairs from above
    match_features.match_from_paths(
        conf = match_features_conf,
        pairs_path = query_global_matches_path,
        match_path = query_local_match_path,
        feature_path_q = query_local_features_path,
        feature_path_ref = db_local_features_path
    )


    ## Now we have global candidate and thier mathces. We use this, along with SfM reconstruction to localize the image.
    reconstruction = pycolmap.Reconstruction(db_reconstruction.__str__())

    # camera = pycolmap.infer_camera_from_image(img_path / query_image_names[0])
    camera = reconstruction.cameras[1]


    conf = {
        'estimation': {'ransac': {'max_error': 12}},
        'refinement': {'refine_focal_length': True, 'refine_extra_params': True}
    }

    localizer = localize_sfm.QueryLocalizer(reconstruction, conf)
    cam_from_world = {}


    for query_image_name in query_image_names:
        ref_ids = []

        print(query_image_name)
        with open(query_global_matches_path, "r") as f:
            pairss = [line.strip().split() for line in f.readlines()] 
            for pair in pairss:
                if pair[0] == query_image_name and reconstruction.find_image_with_name(pair[1]) is not None:
                    ref_ids.append(reconstruction.find_image_with_name(pair[1]).image_id)

        # pdb.set_trace()


        ret, log = localize_sfm.pose_from_cluster(
            localizer = localizer, 
            qname = query_image_name, 
            query_camera = camera, 
            db_ids = ref_ids, 
            features_path = db_local_features_path, 
            matches_path = query_local_match_path,
            features_q_path = query_local_features_path
        )

        cam_from_world[query_image_name] = ret["cam_from_world"]

        with open(query_results, "w") as f:
            for query, t in cam_from_world.items():
                qvec = " ".join(map(str, t.rotation.quat[[3, 0, 1, 2]]))
                tvec = " ".join(map(str, t.translation))
                name = query.split("/")[-1]
                f.write(f"{name} {qvec} {tvec}\n")


if __name__ == "__main__":
    main()