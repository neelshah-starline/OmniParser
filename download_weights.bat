@echo off
echo Downloading OmniParser model weights...
echo.

REM Create weights directory if it doesn't exist
if not exist weights mkdir weights

REM Download icon detection model files
echo Downloading icon detection model files...
hf download microsoft/OmniParser-v2.0 icon_detect/train_args.yaml --local-dir weights
hf download microsoft/OmniParser-v2.0 icon_detect/model.pt --local-dir weights
hf download microsoft/OmniParser-v2.0 icon_detect/model.yaml --local-dir weights

REM Download icon caption model files
echo.
echo Downloading icon caption model files...
hf download microsoft/OmniParser-v2.0 icon_caption/config.json --local-dir weights
hf download microsoft/OmniParser-v2.0 icon_caption/generation_config.json --local-dir weights
hf download microsoft/OmniParser-v2.0 icon_caption/model.safetensors --local-dir weights

REM Move the icon_caption directory to icon_caption_florence
echo.
echo Organizing directories...
move weights\icon_caption weights\icon_caption_florence

echo.
echo Download complete! Model weights are ready.
echo.
pause
