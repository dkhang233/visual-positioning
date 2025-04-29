from ray import serve
import torch
from hloc import extract_features, extractors
from hloc.utils.base_model import dynamic_load
import pdb
from pathlib import Path
import numpy as np
import h5py

retrieval_conf = extract_features.confs["netvlad"]


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 1, "num_gpus": 0.25})
class ImageRetrival:
    def __init__(self, conf=retrieval_conf):
        self.conf = conf
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        Model = dynamic_load(extractors, self.conf["model"]["name"])
        self.model = Model(self.conf["model"]).eval().to(self.device)

    async def extract(self, image_path: Path) -> Path:
        # Preprocess the image
        dataset = extract_features.ImageDataset(image_path.parent, self.conf["preprocessing"], [image_path.name])
        loader = torch.utils.data.DataLoader(
        dataset, num_workers=1, shuffle=False, pin_memory=True
        )

        h5_path = image_path.parent / (self.conf["output"] + ".h5")
        for idx, data in enumerate(loader):
        # Extract features
            with torch.no_grad():
                pred = self.model({"image": data["image"].to(self.device, non_blocking=True)})
            pred = {k: v[0].cpu().numpy() for k, v in pred.items()}

            pred["image_size"] = original_size = data["original_size"][0].numpy()

            if "keypoints" in pred:
                size = np.array(data["image"].shape[-2:][::-1])
                scales = (original_size / size).astype(np.float32)
                pred["keypoints"] = (pred["keypoints"] + 0.5) * scales[None] - 0.5
                if "scales" in pred:
                    pred["scales"] *= scales.mean()
                # add keypoint uncertainties scaled to the original resolution
                uncertainty = getattr(self.model, "detection_noise", 1) * scales.mean()

            for k in pred:
                dt = pred[k].dtype
                if (dt == np.float32) and (dt != np.float16):
                    pred[k] = pred[k].astype(np.float16)

            with h5py.File(str(h5_path), "a", libver="latest") as fd:
                try:
                    if image_path.name in fd:
                        del fd[image_path.name]
                    grp = fd.create_group(image_path.name)
                    for k, v in pred.items():
                        grp.create_dataset(k, data=v)
                    if "keypoints" in pred:
                        grp["keypoints"].attrs["uncertainty"] = uncertainty
                except OSError as error:
                    if "No space left on device" in error.args[0]:
                        print(
                            "Out of disk space: storing features on disk can take "
                            "significant space, did you enable the as_half flag?"
                        )
                        del grp, fd[image_path.name]
                    raise error
            del pred
        return h5_path