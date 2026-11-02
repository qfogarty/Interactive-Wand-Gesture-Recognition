"""
Opens the Pi camera from hardware.camera in config.yaml.

The app and the reflector calibrator both use this, so they capture the same way.
"""

import time

DEFAULT_CAMERA = {
    "resolution": [640, 480],
    "exposure_time": 8000,  # microseconds; null in config means auto exposure
    "analogue_gain": 6.0,
    "brightness": -0.3,
    "frame_rate": 30,
    "lens_position": 1.0,   # dioptres; 1.0 focuses at about 1 m
}

AF_MODE_MANUAL = 0  # libcamera controls.AfModeEnum.Manual


def camera_settings(camera_cfg):
    """The settings in force: config values over defaults, for configs missing newer keys."""
    return {**DEFAULT_CAMERA, **camera_cfg}


def build_camera_controls(camera_cfg, available_controls):
    """Build Picamera2 controls, leaving out any this camera does not offer."""
    settings = camera_settings(camera_cfg)
    frame_duration = int(1_000_000 / settings["frame_rate"])

    controls = {
        "FrameDurationLimits": (frame_duration, frame_duration),
        "Brightness": settings["brightness"],
        "AfMode": AF_MODE_MANUAL,
        "LensPosition": settings["lens_position"],
    }
    if settings["exposure_time"] is not None:
        controls.update({
            "AeEnable": False,
            "ExposureTime": settings["exposure_time"],
            "AnalogueGain": settings["analogue_gain"],
        })

    return {name: value for name, value in controls.items() if name in available_controls}


def open_camera(camera_cfg):
    """Start the camera with controls applied from the first frame."""
    from picamera2 import Picamera2

    settings = camera_settings(camera_cfg)
    camera = Picamera2()
    configuration = camera.create_preview_configuration(
        main={"size": tuple(settings["resolution"]), "format": "RGB888"},
        controls=build_camera_controls(camera_cfg, camera.camera_controls),
    )
    camera.configure(configuration)
    camera.start()
    time.sleep(1)  # Allow camera to warm up
    return camera
