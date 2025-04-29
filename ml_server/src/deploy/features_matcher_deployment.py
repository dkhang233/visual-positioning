import torch
from pathlib import Path
from ray import serve
from functools import partial
from hloc import match_features, matchers, pairs_from_retrieval
from hloc.utils.base_model import dynamic_load
import pdb

match_conf = match_features.confs["superglue"]

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 1, "num_gpus": 0.25})
class FeaturesMatcher:
    def __init__(self, conf=match_conf):
        self.conf = conf
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        Model = dynamic_load(matchers, self.conf["model"]["name"])
        self.model = Model(self.conf["model"]).eval().to(self.device)

    async def match(self,image_path: Path,image_retrival_q: Path, image_retrival_ref: Path, features_path_q: Path, features_path_ref: Path) -> Path:
        pairs_path = image_retrival_q.parent / "pairs.txt"
        pairs_from_retrieval.main(descriptors=image_retrival_q , db_descriptors= image_retrival_ref, output=pairs_path, num_matched=2)

        
        if not features_path_q.exists():
            raise FileNotFoundError(f"Query feature file {features_path_q}.")
        if not features_path_ref.exists():
            raise FileNotFoundError(f"Reference feature file {features_path_ref}.")
        matches_path = image_retrival_q.parent / (self.conf["output"]+ ".h5")

        pairs = match_features.parse_retrieval(pairs_path)
        pairs = [(q, r) for q, rs in pairs.items() for r in rs if q == image_path.name]
        if len(pairs) == 0:
            print("Skipping the matching.")
            return
        print(f"Matching {len(pairs)} pairs.")
        dataset = match_features.FeaturePairsDataset(pairs, features_path_q, features_path_ref)
        loader = torch.utils.data.DataLoader(
            dataset, num_workers=5, batch_size=1, shuffle=False, pin_memory=True
        )
        writer_queue = match_features.WorkQueue(partial(match_features.writer_fn, match_path=matches_path), 5)

        for idx, data in enumerate(loader):
            data = {
                k: v if k.startswith("image") else v.to(self.device, non_blocking=True)
                for k, v in data.items()
            }
            with torch.no_grad():
                pred = self.model(data)
            pair = match_features.names_to_pair(*pairs[idx])
            writer_queue.put((pair, pred))
        writer_queue.join()

        return pairs, matches_path