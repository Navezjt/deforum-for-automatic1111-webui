import torch
import cv2
import os
import numpy as np
import torchvision.transforms as transforms
from PIL import Image
from lib.multi_depth_model_woauxi import RelDepthModel
from lib.net_tools import load_ckpt

class LeReSDepth:
    def __init__(self, width=448, height=448, models_path, checkpoint_name='res101.pth', backbone='resnext101'):
        self.width = width
        self.height = height
        self.models_path = models_path
        self.checkpoint_name = checkpoint_path
        self.backbone = backbone
        
        self.depth_model = RelDepthModel(backbone=self.backbone)
        self.depth_model.eval()
        self.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        self.depth_model.to(self.DEVICE)
        load_ckpt(os.path.join(self.models_path, self.checkpoint_name), self.depth_model, None, None)

    @staticmethod
    def scale_torch(img):
        if len(img.shape) == 2:
            img = img[np.newaxis, :, :]
        if img.shape[2] == 3:
            transform = transforms.Compose([transforms.ToTensor(),
                                            transforms.Normalize((0.485, 0.456, 0.406) , (0.229, 0.224, 0.225))])
            img = transform(img)
        else:
            img = img.astype(np.float32)
            img = torch.from_numpy(img)
        return img

    def predict(self, image):
        resized_image = cv2.resize(image, (self.width, self.height))
        img_torch = self.scale_torch(resized_image)[None, :, :, :]
        pred_depth = self.depth_model.inference(img_torch).cpu().numpy().squeeze()
        pred_depth_ori = cv2.resize(pred_depth, (image.shape[1], image.shape[0]))
        return pred_depth_ori

    def save_raw_depth(self, depth, filepath):
        depth_normalized = (depth / depth.max() * 60000).astype(np.uint16)
        cv2.imwrite(filepath, depth_normalized)

    def save_colored_depth(self, depth, filepath):
        plt.imsave(filepath, depth, cmap='rainbow')

    def delete(self):
        del self.depth_model
        torch.cuda.empty_cache()
