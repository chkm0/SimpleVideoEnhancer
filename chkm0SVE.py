import os
import subprocess
import random
from tkinter import Tk, filedialog
from tqdm import tqdm, trange
from PIL import Image, ImageDraw, ImageFont
import time

def run_command(command):
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

def get_frame_rate(video_path):
    command = ['ffprobe', '-v', '0', '-of', 'csv=p=0', '-select_streams', 'v:0',
               '-show_entries', 'stream=r_frame_rate', video_path]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    frame_rate = eval(result.stdout.strip())
    return frame_rate

def get_video_duration(video_path):
    command = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
               '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    duration = float(result.stdout.strip())
    return duration

def take_screenshot(video_path, screenshot_path, timestamp):
    command = [
        'ffmpeg', '-i', video_path, '-ss', str(timestamp), '-vframes', '1',
        '-q:v', '2', '-y', screenshot_path
    ]
    run_command(command)

def create_comparison_image(old_screenshot_paths, new_screenshot_paths, output_path, enhancements):
    old_images = [Image.open(path) for path in old_screenshot_paths]
    new_images = [Image.open(path) for path in new_screenshot_paths]
    
    width, height = old_images[0].size
    num_screenshots = len(old_images)
    comparison_image = Image.new('RGB', (width * num_screenshots, height))
    
    for i in range(num_screenshots):
        comparison_image.paste(old_images[i], (i * width, 0))
        comparison_image.paste(new_images[i], (i * width + width // 2, 0))
    
    draw = ImageDraw.Draw(comparison_image)
    font = ImageFont.load_default()
    for i in range(num_screenshots):
        draw.text((i * width + 10, height - 10), f"Video OLD {i+1}", (255, 255, 255), font=font)
        draw.text((i * width + width // 2 + 10, height - 10), f"Video NEW {i+1}", (255, 255, 255), font=font)
    
    text_x_position = width * num_screenshots + 10
    text_y_position = height // 2
    draw.text((text_x_position, text_y_position), "Enhancements:", (255, 255, 255), font=font)
    text_y_position += 10
    for enhancement in enhancements:
        draw.text((text_x_position, text_y_position), enhancement, (255, 255, 255), font=font)
        text_y_position += 10
    
    comparison_image.save(output_path)
    
    for path in old_screenshot_paths + new_screenshot_paths:
        os.remove(path)

def enhance_video(video_path, output_path, use_hardware_acceleration):
    frame_rate = get_frame_rate(video_path)
    
    filters = [
        'hqdn3d',
        'unsharp=5:5:0.8:3:3:0.4',
        'eq=contrast=1.1:brightness=0.05:saturation=1.2',
    ]
    
    if frame_rate < 60:
        filters.append('minterpolate=fps=60')

    if use_hardware_acceleration:
        vaapi_check_command = ['ffmpeg', '-hide_banner', '-hwaccels']
        vaapi_check_result = subprocess.run(vaapi_check_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if 'vaapi' in vaapi_check_result.stdout:
            command = [
                'ffmpeg',
                '-vaapi_device', '/dev/dri/renderD128',
                '-i', video_path,
                '-vf', ','.join(filters),
                '-c:v', 'h264_vaapi',
                '-preset', 'fast',
                '-b:v', '8M',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            run_command(command)
        else:
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vf', ','.join(filters),
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-b:v', '8M',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            run_command(command)
    else:
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vf', ','.join(filters),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-b:v', '8M',
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        run_command(command)

def process_videos(target_directory):
    files = [f for f in os.listdir(target_directory) if f.lower().endswith(('.avi', '.mov', '.mkv', '.flv', '.wmv', '.mp4'))]
    progress_bar = tqdm(files, unit='file', bar_format="{l_bar}%s{bar}%s{r_bar}")

    for file in progress_bar:
        file_path = os.path.join(target_directory, file)
        filename, file_extension = os.path.splitext(file)
        output_path = os.path.join(target_directory, f"enhanced_{filename}.mp4")
        
        use_hardware_acceleration = False
        vaapi_check_command = ['ffmpeg', '-hide_banner', '-hwaccels']
        vaapi_check_result = subprocess.run(vaapi_check_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if 'vaapi' in vaapi_check_result.stdout:
            use_hardware_acceleration = True

        enhance_video(file_path, output_path, use_hardware_acceleration)
        
        timestamps = [random.randint(1, int(get_video_duration(file_path)) - 1) for _ in range(3)]
        old_screenshot_paths = [os.path.join(target_directory, f"{filename}_old_{i}.png") for i in range(3)]
        new_screenshot_paths = [os.path.join(target_directory, f"{filename}_new_{i}.png") for i in range(3)]
        
        for i in range(3):
            take_screenshot(file_path, old_screenshot_paths[i], timestamps[i])
            take_screenshot(output_path, new_screenshot_paths[i], timestamps[i])
        
        enhancements = ["60fps interpolation", "Denoised", "Sharpened", "Color corrected"]
        create_comparison_image(old_screenshot_paths, new_screenshot_paths, os.path.join(target_directory, f"{filename}_comparison.png"), enhancements)

        progress_bar.set_description_str(f"Enhancing {file}")

    print("Video enhancement complete. Enjoy your video.")

def random_color():
    return "\033[1;" + str(random.randint(30, 37)) + "m"

def print_completion_message():
    colors = ['\033[95m', '\033[94m', '\033[92m', '\033[93m', '\033[91m']
    completion_message = "simple video enhance skript by chkm0, give a shoutout"
    blinking_colors = random.choices(colors, k=len(completion_message))
    for i, char in enumerate(completion_message):
        print(random.choice(blinking_colors) + char + '\033[0m', end='', flush=True)
        time.sleep(0.001)
    print('\n')
    ascii_art = """
    ███████╗██╗  ██╗██████╗ ██╗██████╗ ████████╗    ██████╗ ██╗   ██╗     ██████╗██╗  ██╗██╗  ██╗███╗   ███╗ ██████╗
    ██╔════╝██║ ██╔╝██╔══██╗██║██╔══██╗╚══██╔══╝    ██╔══██╗╚██╗ ██╔╝    ██╔════╝██║  ██║██║ ██╔╝████╗ ████║██╔═████╗
    ███████╗█████╔╝ ██████╔╝██║██████╔╝   ██║       ██████╔╝ ╚████╔╝     ██║     ███████║█████╔╝ ██╔████╔██║██║██╔██║
    ╚════██║██╔═██╗ ██╔══██╗██║██╔═══╝    ██║       ██╔══██╗  ╚██╔╝      ██║     ██╔══██║██╔═██╗ ██║╚██╔╝██║████╔╝██║
    ███████║██║  ██╗██║  ██║██║██║        ██║       ██████╔╝   ██║       ╚██████╗██║  ██║██║  ██╗██║ ╚═╝ ██║╚██████╔╝
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝        ╚═╝       ╚═════╝    ╚═╝        ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ 
    """
    for i, line in enumerate(ascii_art.split('\n')):
        blinking_colors = random.choices(colors, k=len(line))
        for char in line:
            print(random.choice(blinking_colors) + char + '\033[0m', end='', flush=True)
            time.sleep(0.001)
        if i < len(ascii_art.split('\n')) - 1:
            print()
    print('\n')

def animate_progress_bar(files):
    for _ in trange(len(files), unit='file', bar_format="{l_bar}%s{bar}%s{r_bar}"):
        progress_text = random_color() + "enhancing video..." + '\033[0m'
        tqdm.write(progress_text)
        time.sleep(0.001)

if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    target_directory = filedialog.askdirectory()
    root.destroy()
    if target_directory:
        files = [f for f in os.listdir(target_directory) if f.lower().endswith(('.avi', '.mov', '.mkv', '.flv', '.wmv', '.mp4'))]
        animate_progress_bar(files)
        process_videos(target_directory)
        print_completion_message()
    print(random_color() + "Press any key to exit...")
    input()
