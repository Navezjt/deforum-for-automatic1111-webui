import math, os, subprocess
import cv2
import hashlib
import numpy as np
import torch
import gc
import torchvision.transforms as T
from einops import rearrange, repeat
from PIL import Image
from midas.dpt_depth import DPTDepthModel
from midas.transforms import Resize, NormalizeImage, PrepareForNet
import torchvision.transforms.functional as TF
from .general_utils import checksum
from modules import lowvram, devices
from modules.shared import opts
from .ZoeDepth import ZoeDepth

class MidasModel:
    _instance = None

    def __new__(cls, *args, **kwargs):
        keep_in_vram = kwargs.get('keep_in_vram', False)
        use_zoe_depth = kwargs.get('use_zoe_depth', False)
        Width = kwargs.get('Width', 512)
        Height = kwargs.get('Height', 512)
        model_switched = cls._instance and cls._instance.use_zoe_depth != use_zoe_depth
        resolution_changed = cls._instance and (cls._instance.Width != Width or cls._instance.Height != Height)

        if cls._instance is None or (not keep_in_vram and not hasattr(cls._instance, 'midas_model')) or model_switched or resolution_changed:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(models_path=args[0], device=args[1], half_precision=True, keep_in_vram=keep_in_vram, use_zoe_depth=use_zoe_depth, Width=Width, Height=Height)
        elif cls._instance.should_delete and keep_in_vram:
            cls._instance._initialize(models_path=args[0], device=args[1], half_precision=True, keep_in_vram=keep_in_vram, use_zoe_depth=use_zoe_depth, Width=Width, Height=Height)
        cls._instance.should_delete = not keep_in_vram
        return cls._instance

    def _initialize(self, models_path, device, half_precision=True, keep_in_vram=False, use_zoe_depth=False, Width=512, Height=512):
        self.keep_in_vram = keep_in_vram
        self.Width = Width
        self.Height = Height
        self.depth_min = 1000
        self.depth_max = -1000
        self.device = device
        self.use_zoe_depth = use_zoe_depth
        
        if self.use_zoe_depth:
            self.zoe_depth = ZoeDepth(self.Width, self.Height)
        if not self.use_zoe_depth:
            model_file = os.path.join(models_path, 'dpt_large-midas-2f21e586.pt')
            if not os.path.exists(model_file):
                from basicsr.utils.download_util import load_file_from_url
                load_file_from_url(r"https://github.com/intel-isl/DPT/releases/download/1_0/dpt_large-midas-2f21e586.pt", models_path)
                if checksum(model_file) != "fcc4829e65d00eeed0a38e9001770676535d2e95c8a16965223aba094936e1316d569563552a852d471f310f83f597e8a238987a26a950d667815e08adaebc06":
                    raise Exception(r"Error while downloading dpt_large-midas-2f21e586.pt. Please download from here: https://github.com/intel-isl/DPT/releases/download/1_0/dpt_large-midas-2f21e586.pt and place in: " + models_path)

            if not self.keep_in_vram or not hasattr(self, 'midas_model'):
                print("Loading MiDaS model...")
                self.midas_model = DPTDepthModel(
                    path=model_file,
                    backbone="vitl16_384",
                    non_negative=True,
                )

                normalization = NormalizeImage(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])

                self.midas_transform = T.Compose([
                    Resize(384, 384, resize_target=None, keep_aspect_ratio=True, ensure_multiple_of=32,
                           resize_method="minimal", image_interpolation_method=cv2.INTER_CUBIC),
                    normalization,
                    PrepareForNet()
                ])

            self.midas_model.eval().to(self.device, memory_format=torch.channels_last if self.device == torch.device("cuda") else None)
            if half_precision:
                self.midas_model = self.midas_model.half()

    def predict(self, prev_img_cv2, midas_weight, half_precision) -> torch.Tensor:
        DEBUG_MODE = opts.data.get("deforum_debug_mode_enabled", False)
        
        img_pil = Image.fromarray(cv2.cvtColor(prev_img_cv2.astype(np.uint8), cv2.COLOR_RGB2BGR))
        
        if self.use_zoe_depth:
            depth_tensor = self.zoe_depth.predict(img_pil).to(self.device)

        else:
            w, h = prev_img_cv2.shape[1], prev_img_cv2.shape[0]

            img_midas = prev_img_cv2.astype(np.float32) / 255.0
            img_midas_input = self.midas_transform({"image": img_midas})["image"]
            sample = torch.from_numpy(img_midas_input).float().to(self.device).unsqueeze(0)

            if self.device.type == "cuda" or self.device.type == "mps":
                sample = sample.to(memory_format=torch.channels_last)
                if half_precision:
                    sample = sample.half()

            with torch.no_grad():
                midas_depth = self.midas_model.forward(sample)
            midas_depth = torch.nn.functional.interpolate(
                midas_depth.unsqueeze(1),
                size=img_midas.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze().cpu().numpy()
            
            if DEBUG_MODE:
                print("Midas depth tensor before 50/19 calculation:")
                print(torch.from_numpy(np.expand_dims(midas_depth, axis=0)).squeeze())

            torch.cuda.empty_cache()
            midas_depth = np.subtract(50.0, midas_depth) / 19.0
            depth_tensor = torch.from_numpy(np.expand_dims(midas_depth, axis=0)).squeeze().to(self.device)
        
        if DEBUG_MODE:
            print("Shape of depth_tensor:", depth_tensor.shape)
            print("Tensor data:")
            print(depth_tensor)

        w, h = prev_img_cv2.shape[1], prev_img_cv2.shape[0]

        return depth_tensor

    def to_image(self, depth: torch.Tensor):
        depth = depth.cpu().numpy()
        depth = np.expand_dims(depth, axis=0) if len(depth.shape) == 2 else depth
        self.depth_min = min(self.depth_min, depth.min())
        self.depth_max = max(self.depth_max, depth.max())
        denom = max(1e-8, self.depth_max - self.depth_min)
        temp = rearrange((depth - self.depth_min) / denom * 255, 'c h w -> h w c')
        temp = repeat(temp, 'h w 1 -> h w c', c=3)
        return Image.fromarray(temp.astype(np.uint8))

    def save(self, filename: str, depth: torch.Tensor):
        self.to_image(depth).save(filename)

    def to(self, device):
        self.device = device
        if self.use_zoe_depth:
            self.zoe_depth.zoe.to(device)
        else:
            self.midas_model.to(device)
        gc.collect()
        torch.cuda.empty_cache()

    def delete_model(self):
        if self.use_zoe_depth:
            self.zoe_depth.delete()
            del self.zoe_depth
        else:
            del self.midas_model
        gc.collect()
        torch.cuda.empty_cache()
        devices.torch_gc()