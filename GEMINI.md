# Milonga Music Player

A specialized music player designed for Tango DJs and Milonga events. It provides features tailored for high-quality audio playback and playlist management during tango dance events.

## Project Overview

- **Purpose**: A zrob commit music player specifically designed for Milonga (Tango events).
- **Core Technologies**:
  - **Language**: Python 3
  - **GUI Framework**: `customtkinter` (a modern wrapper around `tkinter`)
  - **Audio Backend**: `pygame.mixer`
  - **Audio Processing**: `pyloudnorm` (loudness normalization), `pydub` (audio manipulation), `mutagen` (metadata), `scipy` (filtering).
  - **Packaging**: `cx-Freeze` (for Windows builds), standard `setuptools` (`setup.py`).
- **Key Features**:
  - **Drag-and-Drop Playlist**: Easily add files to the current playlist.
  - **Playback Controls**: Start, stop, pause, and next track with automated smooth fade-out.
  - **Loudness Normalization**: Ensures consistent volume levels across different recordings using `pyloudnorm`.
  - **Silence Detection**: Automatically identifies and skips silence at the beginning and end of tracks.
  - **Genre Color Coding**: Visual categorization of tracks (Tango, Vals, Milonga, Cortina).
  - **Genre-Based Equalization**: Automatic application of EQ presets based on track genre.
  - **Low-Pass Filtering**: Support for per-track low-pass filters via comments (e.g., `H:4000` for 4kHz).

## Architecture

- `milonga.py`: The entry point of the application.
- `milonga_app.py`: Contains the `MilongaApp` class, the main orchestrator for the GUI and application state.
- `player.py`: Encapsulates all audio playback logic, including `pygame` initialization, device management, and audio processing (normalization, filtering).
- `config.py`: Manages application settings, stored in a `.plist` file (on macOS) or equivalent Application Support directory.
- `gui_builder.py`: Responsible for constructing the `customtkinter` GUI components.
- `app_state.py`: Manages the internal state of the application (current songs, settings, etc.).
- `utils.py`: General utility functions for audio conversion and file handling.
- `macos_audio.py`: Specific integration for macOS audio features (e.g., "hog mode").

## Building and Running

### Prerequisites

- Python 3.x
- `ffmpeg` and `ffprobe` (executable binaries expected in the `./ffmpeg/` directory or system PATH for some features).

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

Execute the main script:
```bash
python milonga.py
```
Or use the provided shell script on macOS/Linux:
```bash
./run_milonga.sh
```

### Packaging

- **Windows**: Use `python setup_windows.py build` (requires `cx-Freeze`).
- **macOS/General**: Standard `setup.py` is available.

## Development Conventions

- **GUI**: Layout is handled primarily in `gui_builder.py` using `customtkinter`'s grid system.
- **State Management**: The application uses an `AppState` object to track songs and settings, passed through `MilongaApp`.
- **Audio Logic**: Avoid direct `pygame` calls in GUI code; use the abstraction layer in `player.py`.
- **Settings**: Configuration is managed via `config.py`. Settings are automatically loaded and merged with defaults on startup.
- **Audio Files**: The player supports `.mp3`, `.ogg`, `.aif`, `.aiff`, `.m4a`, and `.flac`. Non-standard files may be converted to `.mp3` automatically and stored in the application support directory.

## File Structure

- `icons/`: UI icons for playback controls.
- `themes/`: Custom GUI themes (e.g., `tango.json`).
- `ffmpeg/`: Local directory for ffmpeg binaries.
- `Application Support`: Settings and temporary/converted files are stored in `~/Library/Application Support/Milonga` (on macOS).
