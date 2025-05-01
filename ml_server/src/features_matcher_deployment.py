import torch
import time
import numpy as np
from pathlib import Path
from ray import serve
from ray.serve.handle import DeploymentResponse
from hloc import match_features, matchers
from hloc.pairs_from_retrieval import pairs_from_score_matrix, get_descriptors
from hloc.utils.base_model import dynamic_load
from hloc.utils.io import list_h5_names
import h5py
import pdb

from exception_handler import LocalizaionFailed

match_conf = match_features.confs["superglue"]
num_matched = 2

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 1, "num_gpus": 0.25})
class FeaturesMatcher:
    def __init__(self, conf=match_conf):
        self.conf = conf
        device = "cuda" if torch.cuda.is_available() else "cpu"
        Model = dynamic_load(matchers, self.conf["model"]["name"])
        self.model = Model(self.conf["model"]).eval().to(device)
        self.db_image_retrival = None


    def _preprocess_data(self, pairs:list , features_q: dict, features_ref_path: Path):
        dataset = []
        with h5py.File(features_ref_path, "r") as fd:
            for name0, name1 in pairs:
                grp1 = fd[name1]
                data = {}
                for k, v in features_q.items():
                    data[k + "0"] = torch.from_numpy(v.__array__().copy()).float()
                # some matchers might expect an image but only use its size
                data["image0"] = torch.empty((1,) + tuple(features_q["image_size"])[::-1])
                for k, v in grp1.items():
                    data[k + "1"] = torch.from_numpy(v.__array__()).float()
                data["image1"] = torch.empty((1,) + tuple(grp1["image_size"])[::-1])

                for k in data:
                    data[k] = data[k].unsqueeze(0)
                dataset.append(data)
        return dataset


    async def match(self,image_path: Path,image_retrival_q: DeploymentResponse, image_retrival_ref: Path, features_q: DeploymentResponse, features_ref: Path) -> Path:
        pairs_path = image_path.parent / "pairs.txt"

        db_names_h5 = list_h5_names(image_retrival_ref)
        query_names_h5 = [image_path.name]

        if self.db_image_retrival is None:
            self.db_image_retrival = get_descriptors(db_names_h5, image_retrival_ref)
        query_desc = torch.from_numpy(np.stack([image_retrival_q["global_descriptor"]], 0)).float()

        device = "cuda" if torch.cuda.is_available() else "cpu"
        sim = torch.einsum("id,jd->ij", query_desc.to(device), self.db_image_retrival.to(device))
        del query_desc

        # Avoid self-matching
        mask = np.array(query_names_h5)[:, None] == np.array(db_names_h5)[None]
        pairs = pairs_from_score_matrix(sim, mask, num_select=2, min_score=0.2)
        pairs = [(query_names_h5[i], db_names_h5[j]) for i, j in pairs]

        print(f"Found {len(pairs)} pairs.")
        with open(pairs_path, "w") as f:
            f.write("\n".join(" ".join([i, j]) for i, j in pairs))

        if not features_ref.exists():
            raise FileNotFoundError(f"Reference feature file {features_ref}.")

        print(len(pairs))
        if len(pairs) == 0:
            print("Skipping the matching.")
            raise LocalizaionFailed()
        
        print(f"Matching {len(pairs)} pairs.")
        # dataset = match_features.CustomFeaturePairsDataset(pairs, features_q_res[0], features_path_ref)
        # loader = torch.utils.data.DataLoader(
        #     dataset, num_workers=5, batch_size=1, shuffle=False, pin_memory=True
        # )

        dataset = self._preprocess_data(pairs, features_q[0], features_ref)
        local_matches = {}
        for idx, data in enumerate(dataset):
            device = "cuda" if torch.cuda.is_available() else "cpu"
            data = {
                k: v if k.startswith("image") else v.to(device, non_blocking=True)
                for k, v in data.items()
            }
            start = time.perf_counter()
            print(f"Start extracting features: {start}")
            with torch.no_grad():
                pred = self.model(data)
            end = time.perf_counter()
            with open(image_path.parent / "inference_time.txt", "a", encoding="utf-8") as f:
                f.write(f"superglue {end - start}\n")
            local_matches[match_features.names_to_pair(*pairs[idx])] = pred
            del pred
            
        return pairs, local_matches
    

   