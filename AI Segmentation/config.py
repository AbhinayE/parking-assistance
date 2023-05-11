import lib.Mask_RCNN.mrcnn.config
import lib.Mask_RCNN.mrcnn.utils
from lib.Mask_RCNN.mrcnn.model import MaskRCNN


class Config(lib.Mask_RCNN.mrcnn.config.Config):
    NAME = "model_config"
    IMAGES_PER_GPU = 1
    GPU_COUNT = 1
    NUM_CLASSES = 81
