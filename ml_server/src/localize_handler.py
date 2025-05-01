from ray import serve
from ray.serve.handle import DeploymentHandle
from fastapi import UploadFile
import pdb
import os
import uuid
import time
from pathlib import Path
from datetime import date
import pycolmap
import numpy as np
import json
from collections import defaultdict
from hloc.localize_sfm import QueryLocalizer
from hloc import match_features



sfm_path = Path("/media/slam/Storage500GB/Minh-Khang-Workspace/hloc-glomap/data/lab/pro-lab/hloc-data/colmap-superpoint_aachen-superglue/sparse/0")
image_retrival_ref = Path("/media/slam/Storage500GB/Minh-Khang-Workspace/hloc-glomap/data/lab/pro-lab/hloc-data/colmap-superpoint_aachen-superglue/global-feats-netvlad.h5")
feature_ref = Path("/media/slam/Storage500GB/Minh-Khang-Workspace/hloc-glomap/data/lab/pro-lab/hloc-data/colmap-superpoint_aachen-superglue/features.h5")

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 2, "num_gpus": 0.25})
class LocalizeHandler:
    def __init__(self, features_extractor: DeploymentHandle, image_retrival: DeploymentHandle, features_matcher: DeploymentHandle):
        self.features_extractor = features_extractor
        self.image_retrival = image_retrival
        self.features_matcher = features_matcher
        self.reconstruction = pycolmap.Reconstruction(sfm_path)
        
    async def localize(self, query_img: UploadFile) -> dict:
        # Trích xuất các thông tin cần thiết
        img = await query_img.read()  
       

        # Create the folder if it doesn't exist
        folder_path = os.path.join("data", "query_data", date.today().strftime("%Y-%m-%d"), uuid.uuid4().__str__())
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Save the uploaded image
        image_path = Path(os.path.join(folder_path, query_img.filename))

        with open(image_path, "wb") as f:
            f.write(img)
        # Call the feature extractor service and image retrival service
        retrieval_response = self.image_retrival.extract.remote(image_path)
        feature_response = self.features_extractor.extract.remote(image_path)
        pairs, local_matches =  await self.features_matcher.match.remote(image_path, retrieval_response, image_retrival_ref, feature_response, feature_ref)
        feature_response = await feature_response

        query_camera = pycolmap.infer_camera_from_image(image_path.__str__())

        db_names = [ref_id for _,ref_id in pairs]
        ref_ids = []
        for r in db_names:
            image = self.reconstruction.find_image_with_name(r)
            if image is not None:  # Check if the image actually exists in the reconstruction
                ref_ids.append(image.image_id)
            
        conf = {
            'estimation': {'ransac': {'max_error': 12}},
            'refinement': {'refine_focal_length': True, 'refine_extra_params': True},
        }

        localizer = QueryLocalizer(self.reconstruction, conf)

        kpq = feature_response[0]["keypoints"].copy()
        kpq += 0.5  # COLMAP coordinates

        kp_idx_to_3D = defaultdict(list)
        kp_idx_to_3D_to_db = defaultdict(lambda: defaultdict(list))
        num_matches = 0
        for i, db_id in enumerate(ref_ids):
            image = localizer.reconstruction.images[db_id]
            if image.num_points3D == 0:
                print(f"No 3D points found for {image.name}.")
                continue
            points3D_ids = np.array(
                [p.point3D_id if p.has_point3D() else -1 for p in image.points2D]
            )

            matches = local_matches[match_features.names_to_pair(image_path.name, image.name)]['matches0'].cpu()[0]
            idx = np.where(matches != -1)[0]
            matches = np.stack([idx, matches[idx]], -1)

            matches = matches[points3D_ids[matches[:, 1]] != -1].tolist()

            num_matches += len(matches)

            for idx, m in matches:
                id_3D = points3D_ids[m]
                kp_idx_to_3D_to_db[idx][id_3D].append(i)
                # avoid duplicate observations
                if id_3D not in kp_idx_to_3D[idx]:
                    kp_idx_to_3D[idx].append(id_3D)

        idxs = list(kp_idx_to_3D.keys())
        mkp_idxs = [i for i in idxs for _ in kp_idx_to_3D[i]]
        mp3d_ids = [j for i in idxs for j in kp_idx_to_3D[i]]

        
        ret = localizer.localize(kpq, mkp_idxs, mp3d_ids, query_camera)
        if ret is not None:
            ret["camera"] = query_camera

        # mostly for logging and post-processing
        # mkp_to_3D_to_db = [
        #     (j, kp_idx_to_3D_to_db[i][j]) for i in idxs for j in kp_idx_to_3D[i]
        # ]

        # log = {
        #     "db": ref_ids,
        #     "PnP_ret": ret,
        #     "keypoints_query": kpq[mkp_idxs],
        #     "points3D_ids": mp3d_ids,
        #     "points3D_xyz": None,  # we don't log xyz anymore because of file size
        #     "num_matches": num_matches,
        #     "keypoint_index_to_db": (mkp_idxs, mkp_to_3D_to_db),
        # }

        pose = ret['cam_from_world']

        res = {
            'R': pose.rotation.quat.tolist(),
            't': pose.translation.tolist(),
            'K' : query_camera.calibration_matrix().tolist()
        }

        with open(image_path.parent / "result.txt", "w") as f:
           json.dump(res, f, indent=4)
       
        return res