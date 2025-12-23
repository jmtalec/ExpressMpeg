
import asyncio
import os
import pathlib
import threading

from PyQt6.QtWidgets import QMessageBox
from ffmpeg_progress_yield import FfmpegProgress

from utils import Handler, settings, appIcon

from PyQt6.QtWidgets import QApplication


async def run_ffmpeg(input_path, output_path, framerate, widget, handler):
    """ Run ffmpeg command asynchronously using asyncio.to_thread """
    cmd = ['ffmpeg', '-y', '-i', input_path, "-r", str(framerate), output_path]
    ff = FfmpegProgress(cmd)

    progress = 0
    old_progress = None
    running = True

    def run():
        nonlocal progress, running
        try:
            for p in ff.run_command_with_progress():
                progress = p
                if handler.close:
                    break
        except RuntimeError as f:
            print(f)
        running = False

    t = threading.Thread(target=run)
    t.start()

    while running:
        if progress != old_progress:
            widget.set_progress(progress)
            old_progress = progress
        await asyncio.sleep(0)



async def update_app(handler):
    while handler.converting:
        QApplication.processEvents()
        await asyncio.sleep(0)

async def process(input_path, handler: Handler, semaphore: asyncio.Semaphore):
    async with semaphore:
        path = pathlib.Path(input_path)
        if not path.exists:
            qms = QMessageBox(
                        QMessageBox.Icon.Critical,
                        "Erreur lors du traitement d'un fichier",
                        f"Fichier introuvable:  {path}!\nVeuillez en choisir un nouveau dans Réglages.",
                        QMessageBox.StandardButton.Ok
                        )
            qms.setWindowIcon(appIcon)
            qms.exec()
            widget.trash()
            return 
        output_format, send_to_output = handler.audio_options[path.suffix]
        widget = handler.app.file_widgets[input_path]
    
        if send_to_output:
            output_folder = pathlib.Path(settings["output_folder"])
            file_output_folder = output_folder.joinpath(path.parent.name)
            try:
                os.mkdir(file_output_folder)
            except FileExistsError:
                pass
            except OSError:
                if not handler.output_folder_error:
                    qms = QMessageBox(
                        QMessageBox.Icon.Critical,
                        "Erreur lors de la création du dossier de sortie",
                        "Dossier de sortie introuvable !\nVeuillez en choisir un nouveau dans Réglages.",
                        QMessageBox.StandardButton.Ok
                        )
                    qms.setWindowIcon(appIcon)
                    qms.exec()
                widget.trash()
                handler.output_folder_error = True 
                return 

            file_output = str(file_output_folder.joinpath(path.name).with_suffix(output_format))
            process = run_ffmpeg(path, file_output, settings["frame_rate"], widget, handler)
            await process
        
        else:
            file_output = path.with_suffix(output_format)
            process = run_ffmpeg(path, file_output, settings["frame_rate"], widget, handler)
            await process
            os.remove(input_path)
        
        widget.trash()
    
async def convert_files(handler: Handler):
    audio_list = handler.audio_list.copy()
    semaphore = asyncio.Semaphore(settings["n_processes"])  # Contrôle du nombre de processus concurrents
    tasks = [process(file, handler, semaphore) for file in audio_list]
    await asyncio.gather(*tasks)
    handler.converting = False
