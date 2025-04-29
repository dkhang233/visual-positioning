import logging
from pathlib import Path
import os
import cv2
import numpy as np

from hloc.utils.read_write_model import (
    qvec2rotmat,
    read_cameras_binary,
    read_cameras_text,
    read_images_binary,
    read_images_text,
    read_model,
    write_model,
)

logger = logging.getLogger(__name__)


def scale_sfm_images(full_model, scaled_model, image_dir):
    """Duplicate the provided model and scale the camera intrinsics so that
    they match the original image resolution - makes everything easier.
    """
    logger.info("Scaling the COLMAP model to the original image size.")
    scaled_model.mkdir(exist_ok=True)
    cameras, images, points3D = read_model(full_model)

    scaled_cameras = {}
    for id_, image in images.items():
        name = image.name
        img = cv2.imread(str(image_dir / name))
        assert img is not None, image_dir / name
        h, w = img.shape[:2]

        cam_id = image.camera_id
        if cam_id in scaled_cameras:
            assert scaled_cameras[cam_id].width == w
            assert scaled_cameras[cam_id].height == h
            continue

        camera = cameras[cam_id]
        assert camera.model == "SIMPLE_RADIAL"
        sx = w / camera.width
        sy = h / camera.height
        assert sx == sy, (sx, sy)
        scaled_cameras[cam_id] = camera._replace(
            width=w, height=h, params=camera.params * np.array([sx, sx, sy, 1.0])
        )

    write_model(scaled_cameras, images, points3D, scaled_model)


def create_query_list_with_intrinsics(
    model, out, list_file=None, ext=".bin", image_dir=None
):
    """Create a list of query images with intrinsics from the colmap model."""
    if ext == ".bin":
        images = read_images_binary(model / "images.bin")
        cameras = read_cameras_binary(model / "cameras.bin")
    else:
        images = read_images_text(model / "images.txt")
        cameras = read_cameras_text(model / "cameras.txt")

    name2id = {image.name: i for i, image in images.items()}
    if list_file is None:
        names = list(name2id)
    else:
        with open(list_file, "r") as f:
            names = f.read().rstrip().split("\n")
    data = []
    for name in names:
        image = images[name2id[name]]
        camera = cameras[image.camera_id]
        w, h, params = camera.width, camera.height, camera.params

        # if image_dir is not None:
        #     # Check the original image size and rescale the camera intrinsics
        #     img = cv2.imread(str(image_dir / name))
        #     assert img is not None, image_dir / name
        #     h_orig, w_orig = img.shape[:2]
        #     # assert camera.model == "SIMPLE_RADIAL"
        #     sx = w_orig / w
        #     sy = h_orig / h
        #     assert sx == sy, (sx, sy)
        #     w, h = w_orig, h_orig
        #     params = params * np.array([sx, sx, sy, 1.0])

        p = [name, camera.model, w, h] + params.tolist()
        data.append(" ".join(map(str, p)))
    with open(out, "w") as f:
        f.write("\n".join(data))


def evaluate(model, results, list_file=None, ext=".bin", only_localized=False):
    predictions = {}
    test_names = []
    with open(results, "r") as f:
        for data in f.read().rstrip().split("\n"):
            data = data.split()
            name = data[0]
            q, t = np.split(np.array(data[1:], float), [4])
            predictions[name] = (qvec2rotmat(q), t)
            test_names.append(name)
    if ext == ".bin":
        images = read_images_binary(model / "images.bin")
    else:
        images = read_images_text(model / "images.txt")
    name2id = {image.name: i for i, image in images.items()}

    if list_file is None:
        test_names = list(name2id)
    else:
        with open(list_file, "r") as f:
            test_names = f.read().rstrip().split("\n")

    errors_t = []
    errors_R = []
    quality = []
    for name in test_names:
        if name not in predictions:
            if only_localized:
                continue
            e_t = np.inf
            e_R = 180.0
        else:
            image = images[name2id[name]]
            R_gt, t_gt = image.qvec2rotmat(), image.tvec
            R, t = predictions[name]
            e_t = np.linalg.norm(-R_gt.T @ t_gt + R.T @ t, axis=0)
            cos = np.clip((np.trace(np.dot(R_gt.T, R)) - 1) / 2, -1.0, 1.0)
            e_R = np.rad2deg(np.abs(np.arccos(cos)))
            errors_t.append(e_t)
            errors_R.append(e_R)
            quality.append([name, e_t, e_R])

    errors_t = np.array(errors_t)
    errors_R = np.array(errors_R)
    
    top_error_images = results.parent / "top_error_images.txt"
    with open(top_error_images, "w") as f:
        for name, e_t, e_R in sorted(quality, key=lambda q: q[1] , reverse=True):
            f.write(f"{name} {e_t:.3f} {e_R:.3f}\n")



    med_t = np.median(errors_t)
    med_R = np.median(errors_R)
    out = f"Results for file {results.name}:"
    out += f"\nMedian errors: {med_t:.3f}m, {med_R:.3f}deg"

    out += "\nPercentage of test images localized within:"
    threshs_t = [0.01, 0.02, 0.03, 0.05, 0.25, 0.5, 5.0]
    threshs_R = [1.0, 2.0, 3.0, 5.0, 2.0, 5.0, 10.0]
    for th_t, th_R in zip(threshs_t, threshs_R):
        ratio = np.mean((errors_t < th_t) & (errors_R < th_R))
        out += f"\n\t{th_t*100:.0f}cm, {th_R:.0f}deg : {ratio*100:.2f}%"

    out_file = results.parent / "eval.txt"
    logger.info(out)
    with open(out_file, "w") as f:
        f.write(out)


def create_reference_sfm(full_model, ref_model, blacklist=None, ext=".bin"):
    """Create a new COLMAP model with only training images."""
    logger.info("Creating the reference model.")
    ref_model.mkdir(exist_ok=True)
    cameras, images, points3D = read_model(full_model, ext)

    if blacklist is not None:
        with open(blacklist, "r") as f:
            blacklist = f.read().rstrip().split("\n")

    images_ref = dict()
    for id_, image in images.items():
        if blacklist and image.name in blacklist:
            continue
        images_ref[id_] = image

    points3D_ref = dict()
    for id_, point3D in points3D.items():
        ref_ids = [i for i in point3D.image_ids if i in images_ref]
        if len(ref_ids) == 0:
            continue
        points3D_ref[id_] = point3D._replace(image_ids=np.array(ref_ids))

    write_model(cameras, images_ref, points3D_ref, ref_model, ".bin")
    logger.info(f"Kept {len(images_ref)} images out of {len(images)}.")


def split_data(
        sfm_dir: Path,
        output: Path,
        ref_per_query: int
):
    assert sfm_dir.exists(), sfm_dir
    if not output.exists():
        os.makedirs(output)
    db_file = output / "db_list.txt"
    query_file = output / "query_list.txt"

    db_list = []
    query_list = []
    count = 0

    # Read the images name is used for sfm
    images = read_images_binary(sfm_dir /  "images.bin")
    name_list = [image.name for image in images.values()] 

    for filename in sorted(name_list):
        if count == ref_per_query:
            query_list.append(filename)
            count = 0
            continue

        db_list.append(filename)
        count += 1

    with open(db_file, "w") as f:
        for i in range(len(db_list)):
            f.write(f"{db_list[i]}\n")
    with open(query_file, "w") as f:
        for i in range(len(query_list)):
            f.write(f"{query_list[i]}\n")


