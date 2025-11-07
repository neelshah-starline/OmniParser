@echo off
REM Define the files to download
set files=icon_detect/train_args.yaml icon_detect/model.pt icon_detect/model.yaml icon_caption/config.json icon_caption/generation_config.json icon_caption/model.safetensors
REM Loop through each file and download it using huggingface-cli
for %%f in (%files%) do (
    huggingface-cli download microsoft/OmniParser-v2.0 %%f --local-dir weights
)
REM Move the icon_caption directory to icon_caption_florence
move weights\icon_caption weights\icon_caption_florence
REM Keep the terminal open at the end
pause
