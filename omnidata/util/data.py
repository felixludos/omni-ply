import sys, os
import numpy as np
# import torch
# import cv2
from io import BytesIO
# from PIL import Image



_pytorch_types = {
	# 'float': torch.float,
	# 'int': torch.int,
	# 'byte': torch.uint8,
	# 'long': torch.long,
	# 'float16': torch.float16,
	# 'double': torch.float64,
}
def pytorch_type(t):
	return _pytorch_types.get(t,t)



def jpeg_to_str(path):
	with open(path, 'rb') as f:
		return f.read()



def str_to_jpeg(s, ret_PIL=False):
	img = Image.open(BytesIO(s))
	if ret_PIL:
		return img
	return np.array(img)
















