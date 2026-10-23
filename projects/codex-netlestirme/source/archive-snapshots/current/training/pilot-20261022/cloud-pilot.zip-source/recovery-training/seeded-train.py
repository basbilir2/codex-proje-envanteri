"""Single-GPU entry point for the unmodified, pinned upstream training script."""
import runpy
from accelerate.utils import set_seed
from pathlib import Path
set_seed(42)
runpy.run_path(str(Path(__file__).resolve().parent / 'DiffSynth-Studio/examples/qwen_image/model_training/train.py'), run_name='__main__')
