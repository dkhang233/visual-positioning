from ray import serve
import torch
from hloc import extract_features, extractors
from hloc.utils.base_model import dynamic_load
import pdb
from pathlib import Path
import numpy as np
import h5py



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


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 1, "num_gpus": 0.25})
class FeaturesExtractor:
    def __init__(self, conf=feature_conf):
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
















    # def _get_processed_image(self, image_path):
    #     # Preprocess the image
    #     preprocessing_conf = {**self._default_preprocessing_conf, **self.conf["preprocessing"]}

    #     if preprocessing_conf["grayscale"]:
    #         mode = cv2.IMREAD_GRAYSCALE
    #     else:
    #         mode = cv2.IMREAD_COLOR

    #     image = read_image(image_path, mode | cv2.IMREAD_IGNORE_ORIENTATION)
    #     if image is None:
    #         raise ValueError(f"Cannot read image {image_path}.")
    #     if not preprocessing_conf["grayscale"] and len(image.shape) == 3:
    #         image = image[:, :, ::-1]  # BGR to RGB

    #     image = image.astype(np.float32)
    #     size = image.shape[:2][::-1]

    #     if preprocessing_conf["resize_max"] and (
    #         preprocessing_conf["resize_force"] or max(size) > preprocessing_conf["resize_max"]
    #     ):
    #         scale = preprocessing_conf["resize_max"] / max(size)
    #         size_new = tuple(int(round(x * scale)) for x in size)
    #         image = extract_features.resize_image(image, size_new, preprocessing_conf["interpolation"])

    #     if preprocessing_conf["grayscale"]:
    #         image = image[None]
    #     else:
    #         image = image.transpose((2, 0, 1))  # HxWxC to CxHxW
    #     image = image / 255.0

    #     data = {
    #         'image': torch.from_numpy(image),
    #         'original_size': torch.from_numpy(np.array(size)),
    #     }
    #     return data