#!/usr/bin/env python3.12.9

import torch

print(f'PyTorch version: {torch.__version__}')
print(f'CUDNN version: {torch.backends.cudnn.version()}')
torch.cuda.is_available()
print("Number of GPU: ", torch.cuda.device_count())
print("GPU Name: ", torch.cuda.get_device_name())


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('Using device:', device)
