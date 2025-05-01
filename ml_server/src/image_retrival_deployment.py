from ray import serve
import torch
import pdb
from pathlib import Path
import numpy as np
import h5py
import time
from hloc.extract_features import resize_image
from hloc.utils.io import read_image
from hloc import extract_features, extractors
from hloc.utils.base_model import dynamic_load

retrieval_conf = extract_features.confs["netvlad"]
_default_preprocessing_conf = {
    'globs': ['*.jpg', '*.png', '*.jpeg', '*.JPG', '*.PNG'],
    'grayscale': False,
    'resize_max': None,
    'resize_force': False,
    'interpolation': 'cv2_area',  # pil_linear is more accurate but slower
}


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 1, "num_gpus": 0.25})
class ImageRetrival:
    def __init__(self, conf=retrieval_conf):
        self.conf = conf
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        Model = dynamic_load(extractors, self.conf["model"]["name"])
        self.model = Model(self.conf["model"]).eval().to(self.device)

    def _get_processed_image(self, query_dir, query_img_name, preprocessing_conf):
        preprocessing_conf = {**_default_preprocessing_conf, **preprocessing_conf}

        image = read_image(query_dir / query_img_name, preprocessing_conf['grayscale'])
        image = image.astype(np.float32)
        size = image.shape[:2][::-1]

        if preprocessing_conf['resize_max'] and (preprocessing_conf['resize_force']
                                    or max(size) > preprocessing_conf['resize_max']):
            scale = preprocessing_conf['resize_max'] / max(size)
            size_new = tuple(int(round(x*scale)) for x in size)
            image = resize_image(image, size_new, preprocessing_conf['interpolation'])

        if preprocessing_conf['grayscale']:
            image = image[None]
        else:
            image = image.transpose((2, 0, 1))  # HxWxC to CxHxW
        image = image / 255.

        data = {
            'image': torch.from_numpy(image),
            'original_size': torch.from_numpy(np.array(size)),
        }
        return data

    async def extract(self, image_path: Path) -> Path:
         # Extract features
        data = self._get_processed_image(image_path.parent, image_path.name, self.conf["preprocessing"])
        start = time.perf_counter()
        with torch.no_grad():
            pred = self.model({"image": data["image"].unsqueeze(0).to(self.device, non_blocking=True)})
        end = time.perf_counter()
        with open(image_path.parent / "inference_time.txt", "a", encoding="utf-8") as f:
            f.write(f"netvlad {end - start}\n")
        pred = {k: v[0].cpu().numpy() for k, v in pred.items()}

        pred["image_size"] = data["original_size"].numpy()

        for k in pred:
            dt = pred[k].dtype
            if (dt == np.float32) and (dt != np.float16):
                pred[k] = pred[k].astype(np.float16)
                
        return pred