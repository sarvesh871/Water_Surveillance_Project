# Package Cleanup / Inventory

This distribution removes macOS `__MACOSX` resource-fork files and `._*` metadata from the original archive. No core backend source, datasets, trained models, or the existing data log were discarded.

Included:
- Backend source and Flask dashboard
- Original datasets and collected CSV log
- Saved model artifacts required for inference
- Model training/comparison/data-inspection scripts
- Existing validation and diagnostic scripts, grouped under `backend/tests/`
- ESP32 Arduino firmware in `hardware/esp32/`
- README, dependency list, and dataset/model caveats

The Python files, datasets, and model files remain colocated in `backend/` because the current code uses script-relative paths. This is intentional to reduce risk of breaking the current project.
