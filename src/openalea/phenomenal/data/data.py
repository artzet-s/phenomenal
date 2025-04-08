# -*- python -*-
#
#       Copyright INRIA - CIRAD - INRA
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
# ==============================================================================
from __future__ import division, print_function, absolute_import

import collections
import glob
import json
import os
import pathlib

import numpy
from PIL import Image

from openalea.phenomenal.calibration import (
    Chessboard,
    Chessboards,
    Calibration,
    CalibrationSetup,
    OldCalibrationCamera,
)
from openalea.phenomenal.mesh import read_ply_to_vertices_faces
from openalea.phenomenal.object import VoxelGrid

# ==============================================================================

datadir = os.path.dirname(__file__).split("src")[0]


def data_dir(name_dir, dtype="bin"):
    return os.path.join(datadir, "doc", "examples", name_dir, f"{dtype}/")


def _path_images(name_dir, dtype="bin"):
    """According to the plant number return a dict[id_camera][angle] containing
    filename of file.

    Parameters
    ----------

    dtype :  "bin" or "raw" or "chessboard"

    Returns
    -------
    d : dict of dict of string
        dict[id_camera][angle] = filename
    """
    data_directory = os.path.join(datadir, "doc", "examples", name_dir, f"{dtype}/")

    d = collections.defaultdict(dict)
    for id_camera in ["side", "top"]:
        filenames = glob.glob(os.path.join(str(data_directory), id_camera, "*"))
        for filename in filenames:
            angle = int(pathlib.Path(filename).stem)
            d[id_camera][angle] = filename

    return d


def path_bin_images(name_dir):
    """According to the plant number return a dict[id_camera][angle] containing
    filename of the binary image.

    Returns
    -------
    d : dict of dict of string
        dict[id_camera][angle] = filename
    """
    return _path_images(name_dir, dtype="bin")


def path_raw_images(name_dir):
    """
    According to the plant number return a dict[id_camera][angle] containing
    filename of the raw image.

    :return: dict[id_camera][angle] of filename
    """
    return _path_images(name_dir, dtype="raw")


def path_chessboard_images(name_dir):
    """
    According to the plant number return a dict[id_camera][angle] containing
    filename of the raw image.

    :return: dict[id_camera][angle] of filename
    """
    return _path_images(name_dir, dtype="chessboard")


def raw_images(name_dir):
    """
    According to the plant number return a dict[id_camera][angle] of
    numpy array of the loader raw image.

    :return: dict[id_camera][angle] of loaded RGB image
    """

    d = path_raw_images(name_dir)
    for id_camera in d:
        for angle in d[id_camera]:
            d[id_camera][angle] = numpy.asarray(
                Image.open(d[id_camera][angle]).convert('RGB'), dtype=numpy.uint8
            )
    return d


def bin_images(name_dir):
    """
    According to the plant number return a dict[id_camera][angle] of
    numpy array of the loader binary image.
    A binary image is a numpy array of uint8 type.

    :return: dict[id_camera][angle] of loaded grayscale image
    """

    d = path_bin_images(name_dir)
    for id_camera in d:
        for angle in d[id_camera]:
            d[id_camera][angle] = numpy.asarray(
                Image.open(d[id_camera][angle]).convert("L"), dtype=numpy.uint8
            )
    return d


def chessboard_images(name_dir):
    """
    According to the plant number return a dict[id_camera][angle] of
    numpy array of the loader binary image.
    A binary image is a numpy array of uint8 type.

    :return: dict[id_camera][angle] of loaded grayscale image
    """

    d = path_chessboard_images(name_dir)
    for id_camera in d:
        for angle in d[id_camera]:
            d[id_camera][angle] = numpy.asarray(Image.open(d[id_camera][angle]).convert('RGB'))
    return (d,)


# ==============================================================================


def chessboards(name_dir):
    """
    According to name_dir return a dict[id_camera] of camera
    calibration object

    :return: dict[id_camera] of camera calibration object
    """
    data_directory = os.path.join(
        datadir, "doc", "examples", name_dir, "chessboard/points/"
    )

    chessboards = []
    for id_chessboard in [1, 2]:
        chessboards.append(
            Chessboard.load(
                os.path.join(str(data_directory), f"chessboard_{id_chessboard}.json")
            )
        )

    return chessboards


def image_points(name_dir):
    """
    According to name_dir return a dict[id_camera] of camera
    calibration object

    :return: dict[id_camera] of camera calibration object
    """
    data_directory = os.path.join(
        datadir, "doc", "examples", name_dir, "chessboard/points/"
    )

    chessboards = {}
    keep = [42] + list(range(0, 360, 30))
    for id_chessboard in ["target_1", "target_2"]:
        chessboard = Chessboard.load(
            os.path.join(str(data_directory), f"image_points_{id_chessboard}.json")
        )
        for rotation in list(chessboard.image_points["side"]):
            if rotation not in keep:
                chessboard.image_points["side"].pop(rotation)
        chessboards[id_chessboard] = chessboard

    return chessboards


def do_calibration(name_dir):
    """Regenerate calibration of cameras"""
    data_directory = os.path.join(name_dir, "calibration")

    cbs = dict(zip(("target_1", "target_2"), chessboards(name_dir)))
    # add missing info
    cb = cbs["target_1"]
    cb.facing_angles = {"side": 48, "top": 48}
    cb.image_sizes = {"side": (2056, 2454), "top": (2454, 2056)}
    cb.check_order()
    #
    cb = cbs["target_2"]
    cb.facing_angles = {"side": 228, "top": 228}
    cb.image_sizes = {"side": (2056, 2454), "top": (2454, 2056)}
    cb.check_order()

    chess_targets = Chessboards(cbs)
    image_sizes = chess_targets.image_sizes()
    image_resolutions = chess_targets.image_resolutions()
    facings = chess_targets.facings()
    target_points = chess_targets.target_points()
    image_points = chess_targets.image_points()
    # distance and inclination of objects
    cameras_guess = {"side": (5500, 90), "top": (2500, 0)}
    targets_guess = {"target_1": (100, 45), "target_2": (100, 45)}
    setup = CalibrationSetup(
        cameras_guess,
        targets_guess,
        image_resolutions,
        image_sizes,
        facings,
        clockwise_rotation=True,
    )
    cameras, targets = setup.setup_calibration(
        reference_camera="side", reference_target="target_1"
    )
    calibration = Calibration(
        targets=targets,
        cameras=cameras,
        target_points=target_points,
        image_points=image_points,
        reference_camera="side",
        clockwise_rotation=True,
    )
    calibration.calibrate()
    calibration.dump(os.path.join(data_directory, "calibration_cameras.json"))


def calibrations(name_dir):
    """
    According to name_dir return a dict[id_camera] of camera
    calibration object

    :return: dict[id_camera] of camera calibration object
    """

    data_directory = os.path.join(name_dir, "calibration/")

    calibration = {}
    for id_camera in ["side", "top"]:
        calibration[id_camera] = OldCalibrationCamera.load(
            os.path.join(data_directory, f"calibration_camera_{id_camera}.json")
        )

    return calibration


def new_calibrations(name_dir):
    """
    According to name_dir return a camera
    calibration object

    """

    file_name = os.path.join(name_dir, "calibration", "calibration_cameras.json")
    return Calibration.load(file_name)


def voxel_grid(name_dir, plant_number=1, voxels_size=4):
    """
    According to the plant number and the voxel size desired return the
    voxel_grid of the plant.

    :param plant_number: number of the plant desired (int)
    :param voxels_size: diameter of each voxel in mm (int)
    :return: voxel_grid object
    """
    vg = VoxelGrid.read(
        os.path.join(name_dir, f"plant_{plant_number}/voxels/{voxels_size}.npz")
    )

    return vg


# ==============================================================================


def tutorial_data_binarization_mask(name_dir):
    """
    Return the list of required images to process the notebook tutorial on
    binarization. The images are already load with opencv in unchanged format.
    images = ["mask_hsv.png", "mask_clean_noise.png", "mask_mean_shift.png"]

    :return: list of image
    """

    data_directory = os.path.join(datadir, "doc", "examples", name_dir, "plant_6/mask/")
    masks = []
    for filename in ["mask_hsv.png", "mask_mean_shift.png"]:
        masks.append(numpy.asarray(Image.open(os.path.join(data_directory, filename))))

    return masks


# ==============================================================================


def synthetic_plant(name_dir, registration_point=(0, 0, 750)):
    """According to name_dir return the mesh plant and skeleton of the
     synthetic plant.

    Parameters
    ----------
    name_dir : str
        Name of the synthetic plant directory

    registration_point: 3-tuple, optional
        Position of the pot in the scene
    Returns
    -------
        out : vertices, faces, meta_data

    """
    filename = os.path.join(name_dir, "synthetic_plant.ply")

    vertices, faces, _ = read_ply_to_vertices_faces(filename)
    vertices = numpy.array(vertices) * 10 - numpy.array([registration_point])

    with open(filename.replace("ply", "json"), "r", encoding="UTF8") as infile:
        meta_data = json.load(infile)

    return vertices, faces, meta_data


# ==============================================================================


def mesh_mccormik_plant(name_dir):
    """According to name_dir return the mesh of plant from the McCormik paper"""

    filename = os.path.join(name_dir, "segmentedMesh.ply")

    vertices, faces, colors = read_ply_to_vertices_faces(filename)

    return vertices, faces, colors
