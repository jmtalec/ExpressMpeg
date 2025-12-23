import pathlib
import platform
import subprocess
import re
import json
import os

from PyQt6.QtWidgets import QFileIconProvider
from PyQt6.QtGui import QFont, QFontDatabase, QIcon

__version__ = "2.10.0"

CREATE_NO_WINDOW = 0x08000000

appIcon = QIcon(":/favicon/favicon/favicon.ico")

def load_font(font):
    font_id = QFontDatabase.addApplicationFont(font)
    if font_id != -1:
        font_name = QFontDatabase.applicationFontFamilies(font_id)[0]
        font = QFont(font_name)
        return font
    else:
        return QFont()

expressmpeg_font = load_font(":/font/src/expressmpeg_font.ttf")
app_font = load_font(":/font/src/segoeui.ttf")


icon_provider = QFileIconProvider()

frame_rates = [11025, 22050, 44100, 48000, 96000, 192000]

audio_formats_and_descriptions = {
    ".3ga" :  "3GPP Audio File",
    ".aac" :  "Advanced Audio Codec",
    ".ac3" :  "Dolby Digital Audio",
    ".aiff" :  "Audio Interchange File Format",
    ".alac" :  "Apple Lossless Audio Codec",
    ".amr" :  "Adaptive Multi-Rate Audio Codec",
    ".ape" :  "Monkey's Audio",
    ".au" :  "Sun Microsystems AU format",
    ".caf" :  "Core Audio Format",
    ".dts" :  "Digital Theater Systems Audio",
    ".flac" :  "Free Lossless Audio Codec",
    ".gsm" :  "GSM Full Rate Audio",
    ".m4a" :  "MPEG-4 Audio",
    ".m4b" :  "MPEG-4 Audio Book",
    ".m4p" :  "MPEG-4 Protected Audio",
    ".mka" :  "Matroska Audio",
    ".mlp" :  "Meridian Lossless Packing",
    ".mp2" :  "MPEG Audio Layer II",
    ".mp3" :  "MPEG Audio Layer III",
    ".mp4" :  "MPEG Audio Layer IV",
    ".mpc" :  "Musepack",
    ".oga" :  "Ogg Audio Container",
    ".ogg" :  "Ogg Vorbis",
    ".opus" :  "Opus Audio Codec",
    ".qcp" :  "Qualcomm PureVoice Audio",
    ".ra" :  "RealAudio",
    ".shn" :  "Shorten Lossless Audio",
    ".snd" :  "Generic Sound File",
    ".spx" :  "Speex Audio",
    ".tta" :  "True Audio Codec",
    ".voc" :  "Creative Voice File",
    ".vqf" :  "TwinVQ Audio",
    ".wav" :  "Waveform Audio File Format",
    ".wma" :  "Windows Media Audio",
    ".wv" :  "WavPack Audio",
    ".xa" :  "PlayStation Audio Format",
}

audio_formats = list(audio_formats_and_descriptions.keys())


def get_description():
    file_types = str(";").join(['*'+x for x in audio_formats_and_descriptions])[:-1]
    descriptions = str(";;").join(["(*"+x+") "+audio_formats_and_descriptions[x] for x in audio_formats_and_descriptions])
    return f"All supported files ({file_types});;{descriptions})"

class Handler:
    def __init__(self, app):
        self.app = app
        self.audio_list = []
        self.converting = False
        self.pause = False
        self.populating = False
        self.close = False
        self.output_folder_error = False
        self.audio_options = dict(zip(audio_formats, [{"output_format" : None, "send_to_output": False} for x in audio_formats]))

    def audio_types(self):
        return tuple({get_file_type(t) for t in self.audio_list})

def open_folder(folder):
        abs_folder = os.path.abspath(folder)
        subprocess.Popen(
            f'explorer.exe "{abs_folder}"', creationflags=CREATE_NO_WINDOW
            )

def save_settings(changes: dict):
    for key in changes:
        settings[key] = changes[key]
    with open("./settings.json", "w") as fp:
        json.dump(settings, fp)

def load_settings() -> dict:
    with open("./settings.json", "r") as f:
        return json.load(f)

settings = load_settings()

def _isWin11():
    if platform.system() != "Windows":
        return False

    try:
        output = subprocess.run(
            ['wmic', 'os', 'get', 'Caption'], 
            capture_output=True, 
            text=True, 
            creationflags=subprocess.CREATE_NO_WINDOW
        ).stdout
        return "11" in re.findall(r"\d+", output)[0]
    except (IndexError, AttributeError):
        return False

isWin11 = _isWin11()

def get_file_type(file):
    return pathlib.Path(file).suffix
