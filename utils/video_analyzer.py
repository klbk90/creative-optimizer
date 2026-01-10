"""
Video Analyzer using Claude 3.5 Sonnet Vision API.
"""

import os
import subprocess
import base64
import json
import re
import time
from typing import Optional, Dict
from utils.logger import setup_logger

logger = setup_logger(__name__)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def extract_video_frames(video_path: str, timestamps: list = None) -> list:
    """
    Extract frames from video using ffmpeg.

    Args:
        video_path: Path to video file
        timestamps: List of timestamps in seconds (default: [0, 3, 10])
                   - 0s: Hook (first 3 seconds)
                   - 3s: Body/Transition
                   - 10s: CTA/End

    Returns:
        List of base64-encoded frame images
    """
    if timestamps is None:
        timestamps = [0, 3, 10]  # Optimize for Hook, Body, CTA

    frames = []
    try:
        # Get duration to validate timestamps
        duration_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        duration = float(subprocess.check_output(duration_cmd).decode().strip())

        # Adjust timestamps if video is shorter
        adjusted_timestamps = [min(t, duration - 0.1) for t in timestamps]

        for i, timestamp in enumerate(adjusted_timestamps):
            output_path = f"/tmp/frame_{i}_{int(timestamp)}s.png"

            extract_cmd = [
                "ffmpeg",
                "-ss", str(timestamp),  # Seek to timestamp
                "-i", video_path,
                "-vframes", "1",  # Extract 1 frame
                "-q:v", "2",  # Quality (2 = high)
                "-y",  # Overwrite
                output_path
            ]
            subprocess.run(extract_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            with open(output_path, "rb") as f:
                frame_b64 = base64.b64encode(f.read()).decode('utf-8')
                frames.append({
                    "data": frame_b64,
                    "timestamp": timestamp,
                    "label": _get_frame_label(timestamp)
                })
            os.remove(output_path)

        logger.info(f"✅ Extracted {len(frames)} frames at {timestamps}s")
        return frames
    except Exception as e:
        logger.error(f"Frame extraction failed: {e}")
        return []


def _get_frame_label(timestamp: float) -> str:
    """Get semantic label for frame based on timestamp."""
    if timestamp <= 1:
        return "hook"
    elif timestamp <= 5:
        return "transition"
    else:
        return "cta"


def analyze_video_with_claude(video_path: str) -> Optional[Dict]:
    """Analyze video using Claude Vision API."""
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set")
        return None

    frames = extract_video_frames(video_path)
    if not frames:
        return None

    prompt = """Analyze this EdTech/Online Course UGC video from 3 key frames (Hook at 0s, Body at 3s, CTA at 10s).

Extract the following:

1. **hook_type**: problem_agitation, before_after, question, social_proof, insider_secret, urgency, transformation, pain_point, generic_intro

2. **emotion**: frustration, achievement, curiosity, trust, hope, fomo, empathy, neutral

3. **pacing**: fast, medium, slow

4. **target_audience_pain**: no_time, lack_results, fear_missing_out, overwhelmed, skepticism, tried_everything, lack_knowledge, unknown

5. **psychotype** (target audience psychological profile):
   - **Switcher**: Constantly jumping between courses/platforms. Looking for "the one" perfect solution. Impatient, easily distracted.
   - **Status Seeker**: Motivated by certificates, credentials, social proof. Wants to show off achievements. Career-focused.
   - **Skill Upgrader**: Practical learner. Wants specific skills for immediate application. ROI-driven. "Just teach me how to do X".
   - **Freedom Hunter**: Values flexibility, self-paced learning, location independence. Wants to escape 9-5. Lifestyle-focused.
   - **Safety Seeker**: Risk-averse. Needs guarantees, testimonials, step-by-step guidance. Fears failure. Wants proven methods.

Respond ONLY in valid JSON format:
{"hook_type": "...", "emotion": "...", "pacing": "...", "target_audience_pain": "...", "psychotype": "...", "reasoning": "..."}"""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        content = [{"type": "text", "text": prompt}]

        # Add frames with labels for context
        for frame in frames:
            frame_label = frame.get("label", "unknown")
            timestamp = frame.get("timestamp", 0)

            # Add context for each frame
            content.append({
                "type": "text",
                "text": f"\n[Frame at {timestamp}s - {frame_label.upper()}]:"
            })
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": frame["data"]
                }
            })
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": content}]
        )
        
        response_text = response.content[0].text
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        result = json.loads(json_match.group(1) if json_match else response_text)
        
        logger.info(f"✅ Claude analyzed: {result['hook_type']} + {result['emotion']}")
        return result
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None


def analyze_video_with_retry(video_path: str, max_retries: int = 3) -> Dict:
    """Analyze with retries."""
    for attempt in range(max_retries):
        result = analyze_video_with_claude(video_path)
        if result:
            return result
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    return {
        "hook_type": "unknown",
        "emotion": "unknown",
        "pacing": "medium",
        "target_audience_pain": "unknown",
        "psychotype": "unknown",
        "reasoning": "AI analysis failed"
    }
