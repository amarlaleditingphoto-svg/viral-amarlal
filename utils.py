import os
import pytube
import speech_recognition as sr
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, vfx, ColorClip, concatenate_videoclips

def download_youtube(url, upload_folder, session_id):
    """Download a YouTube video and return the path to the downloaded file"""
    try:
        yt = pytube.YouTube(url)
        # Get highest resolution stream with both video and audio
        video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        # Create a unique filename
        filename = f"{session_id}_{yt.title.replace(' ', '_')[:30]}.mp4"
        file_path = os.path.join(upload_folder, filename)
        
        # Download the video
        video_stream.download(output_path=upload_folder, filename=filename)
        return file_path
    except Exception as e:
        raise Exception(f"Failed to download YouTube video: {str(e)}")

def generate_subtitles(audio_path):
    """Generate subtitles from audio file using speech recognition"""
    try:
        recognizer = sr.Recognizer()
        subtitles = []
        
        # Load audio file
        audio = AudioSegment.from_wav(audio_path)
        
        # Process in 10-second chunks for better accuracy
        chunk_duration = 10000  # 10 seconds in milliseconds
        
        for i in range(0, len(audio), chunk_duration):
            chunk = audio[i:i+chunk_duration]
            chunk_file = f"temp_chunk_{i}.wav"
            chunk.export(chunk_file, format="wav")
            
            with sr.AudioFile(chunk_file) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data)
                    start_time = i / 1000  # Convert to seconds
                    end_time = min((i + chunk_duration) / 1000, len(audio) / 1000)
                    subtitles.append((start_time, end_time, text))
                except:
                    # If speech recognition fails, just skip this chunk
                    pass
            
            # Clean up temporary file
            os.remove(chunk_file)
        
        return subtitles
    except Exception as e:
        print(f"Error generating subtitles: {str(e)}")
        return []

def save_clip(video_path, start_time, end_time, output_path, subtitles, vertical=True):
    """Save a clip from the video with optional subtitles and vertical format"""
    try:
        # Load the video
        clip = VideoFileClip(video_path).subclip(start_time, end_time)
        
        # Convert to vertical format (9:16 aspect ratio) if requested
        if vertical:
            # Calculate target dimensions for 9:16 aspect ratio
            target_aspect_ratio = 9/16
            current_aspect_ratio = clip.w / clip.h
            
            if current_aspect_ratio > target_aspect_ratio:
                # Video is too wide, crop the sides
                new_width = int(clip.h * target_aspect_ratio)
                crop_x1 = (clip.w - new_width) // 2
                clip = clip.crop(x1=crop_x1, y1=0, x2=crop_x1 + new_width, y2=clip.h)
            elif current_aspect_ratio < target_aspect_ratio:
                # Video is too tall, crop the top and bottom
                new_height = int(clip.w / target_aspect_ratio)
                crop_y1 = (clip.h - new_height) // 2
                clip = clip.crop(x1=0, y1=crop_y1, x2=clip.w, y2=crop_y1 + new_height)
        
        # Add subtitles if available
        if subtitles:
            # Filter subtitles for this clip's time range
            clip_subtitles = [
                (max(0, st - start_time), min(et - start_time, end_time - start_time), text)
                for st, et, text in subtitles
                if et > start_time and st < end_time
            ]
            
            # Create TextClips for each subtitle
            subtitle_clips = []
            for st, et, text in clip_subtitles:
                txt_clip = TextClip(
                    text, 
                    fontsize=24, 
                    color='white',
                    bg_color='black',
                    font='Arial',
                    size=(clip.w, None),
                    method='caption'
                )
                txt_clip = txt_clip.set_position(('center', 'bottom')).set_start(st).set_end(et)
                subtitle_clips.append(txt_clip)
            
            # Combine video with subtitles
            if subtitle_clips:
                clip = CompositeVideoClip([clip] + subtitle_clips)
        
        # Write the final clip to the output path
        clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        clip.close()
        
        return output_path
    except Exception as e:
        raise Exception(f"Error saving clip: {str(e)}")

def apply_filter(input_path, output_path, filter_name):
    """Apply a filter to the video"""
    try:
        clip = VideoFileClip(input_path)
        
        # Apply the selected filter
        if filter_name == 'grayscale':
            clip = clip.fx(vfx.blackwhite)
        elif filter_name == 'bright':
            clip = clip.fx(vfx.colorx, 1.5)
        elif filter_name == 'dark':
            clip = clip.fx(vfx.colorx, 0.7)
        elif filter_name == 'contrast':
            clip = clip.fx(vfx.lum_contrast, contrast=1.5)
        elif filter_name == 'sepia':
            clip = clip.fx(vfx.sepia)
        elif filter_name == 'vignette':
            clip = clip.fx(vfx.vignette)
        elif filter_name == 'blur':
            clip = clip.fx(vfx.gaussian_blur, sigma=1)
        
        # Write the filtered clip to the output path
        clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        clip.close()
        
        return output_path
    except Exception as e:
        raise Exception(f"Error applying filter: {str(e)}")