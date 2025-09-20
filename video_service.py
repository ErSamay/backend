import subprocess
import os
import json
from typing import Optional, Dict, Any
import tempfile
from PIL import Image, ImageDraw, ImageFont

class VideoService:
    @staticmethod
    def get_video_info(file_path: str) -> Dict[str, Any]:
        """Get video metadata using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                raise ValueError("No video stream found")
            
            return {
                'duration': float(data['format'].get('duration', 0)),
                'size': int(data['format'].get('size', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': eval(video_stream.get('r_frame_rate', '0/1'))
            }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return {}

    @staticmethod
    def trim_video(input_path: str, output_path: str, start_time: float, end_time: float) -> bool:
        """Trim video using ffmpeg"""
        try:
            duration = end_time - start_time
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error trimming video: {e}")
            return False

    @staticmethod
    def add_text_overlay(input_path: str, output_path: str, text: str, 
                        x: int, y: int, start_time: float, end_time: Optional[float],
                        font_size: int = 24, font_color: str = "white", 
                        font_family: str = "Arial") -> bool:
        """Add text overlay to video using ffmpeg"""
        try:
            # Prepare the drawtext filter
            drawtext_filter = f"drawtext=text='{text}':x={x}:y={y}:fontsize={font_size}:fontcolor={font_color}"
            
            if font_family != "Arial":
                drawtext_filter += f":fontfile=/usr/share/fonts/truetype/liberation/{font_family}.ttf"
            
            # Add timing if specified
            if start_time > 0 or end_time:
                if end_time:
                    drawtext_filter += f":enable='between(t,{start_time},{end_time})'"
                else:
                    drawtext_filter += f":enable='gte(t,{start_time})'"
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', drawtext_filter,
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error adding text overlay: {e}")
            return False

    @staticmethod
    def add_image_overlay(input_path: str, output_path: str, overlay_path: str,
                         x: int, y: int, start_time: float, end_time: Optional[float]) -> bool:
        """Add image overlay to video using ffmpeg"""
        try:
            # Prepare the overlay filter
            overlay_filter = f"overlay={x}:{y}"
            
            # Add timing if specified
            if start_time > 0 or end_time:
                if end_time:
                    overlay_filter += f":enable='between(t,{start_time},{end_time})'"
                else:
                    overlay_filter += f":enable='gte(t,{start_time})'"
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-i', overlay_path,
                '-filter_complex', f'[0:v][1:v]{overlay_filter}[v]',
                '-map', '[v]',
                '-map', '0:a?',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error adding image overlay: {e}")
            return False

    @staticmethod
    def add_video_overlay(input_path: str, output_path: str, overlay_path: str,
                         x: int, y: int, start_time: float, end_time: Optional[float]) -> bool:
        """Add video overlay using ffmpeg"""
        try:
            # Similar to image overlay but with video
            overlay_filter = f"overlay={x}:{y}"
            
            if start_time > 0 or end_time:
                if end_time:
                    overlay_filter += f":enable='between(t,{start_time},{end_time})'"
                else:
                    overlay_filter += f":enable='gte(t,{start_time})'"
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-i', overlay_path,
                '-filter_complex', f'[0:v][1:v]{overlay_filter}[v]',
                '-map', '[v]',
                '-map', '0:a?',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error adding video overlay: {e}")
            return False

    @staticmethod
    def add_watermark(input_path: str, output_path: str, watermark_path: str,
                     x: int, y: int, opacity: float = 1.0, scale: float = 1.0) -> bool:
        """Add watermark to video using ffmpeg"""
        try:
            # Build the filter chain
            filter_chain = ""
            
            # Scale watermark if needed
            if scale != 1.0:
                filter_chain += f"[1:v]scale=iw*{scale}:ih*{scale}[scaled];"
                watermark_input = "[scaled]"
            else:
                watermark_input = "[1:v]"
            
            # Add opacity if needed
            if opacity < 1.0:
                if filter_chain:
                    filter_chain += f"{watermark_input}format=rgba,colorchannelmixer=aa={opacity}[transparent];"
                else:
                    filter_chain += f"[1:v]format=rgba,colorchannelmixer=aa={opacity}[transparent];"
                watermark_input = "[transparent]"
            
            # Add overlay
            filter_chain += f"[0:v]{watermark_input}overlay={x}:{y}[v]"
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-i', watermark_path,
                '-filter_complex', filter_chain,
                '-map', '[v]',
                '-map', '0:a?',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error adding watermark: {e}")
            return False