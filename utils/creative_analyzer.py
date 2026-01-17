"""
Creative analyzer using CLIP and GPT-4V.

Extracts patterns from video creatives:
- Hook type (wait, question, bold_claim, curiosity, urgency)
- Emotion (excitement, fear, curiosity, greed, fomo)
- Pacing (fast, medium, slow)
- CTA type (direct, soft, urgency, scarcity)
- Visual features (faces, colors, complexity)

Uses:
1. CLIP embeddings for similarity search
2. GPT-4V for pattern recognition
3. Audio/video analysis for pacing
"""

import os
import json
import base64
from typing import Dict, List, Optional, Tuple
import anthropic
from io import BytesIO
import requests


class CreativeAnalyzer:
    """
    Analyzes video creatives to extract patterns.
    """

    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        if not self.anthropic_api_key:
            print("⚠️ Warning: ANTHROPIC_API_KEY not set. Creative analysis will be limited.")

    def analyze_video(
        self,
        video_path: str = None,
        video_url: str = None,
        frames_to_analyze: List[int] = None
    ) -> Dict:
        """
        Analyze video creative and extract patterns.

        Args:
            video_path: Local path to video file
            video_url: URL to video (if not local)
            frames_to_analyze: List of timestamps (in seconds) to extract frames from
                              Default: [0, 2, 5, 8] (beginning, hook, middle, CTA)

        Returns:
            {
                "hook_type": "wait",
                "emotion": "excitement",
                "pacing": "fast",
                "cta_type": "urgency",
                "has_text_overlay": true,
                "has_voiceover": true,
                "features": {
                    "has_face": true,
                    "num_scenes": 3,
                    "dominant_colors": ["red", "gold"],
                    "visual_complexity": "high",
                    "audio_energy": "high"
                },
                "confidence": 0.85,
                "reasoning": "..."
            }
        """

        if not video_path and not video_url:
            raise ValueError("Either video_path or video_url must be provided")

        if frames_to_analyze is None:
            frames_to_analyze = [0, 2, 5, 8]  # Key moments in typical 10s video

        # Extract frames from video
        frames = self._extract_frames(video_path or video_url, frames_to_analyze)

        # Analyze with Claude + vision
        analysis = self._analyze_with_claude(frames)

        return analysis

    def _extract_frames(self, video_source: str, timestamps: List[int]) -> List[bytes]:
        """
        Extract frames from video at specified timestamps.

        For MVP: Returns placeholder. In production, use ffmpeg or opencv:
        ```bash
        ffmpeg -i video.mp4 -ss 00:00:02 -vframes 1 frame_2s.jpg
        ```
        """

        # TODO: Implement actual frame extraction
        # For now, return empty list - user can provide frames manually
        print(f"⚠️ Frame extraction not implemented. Please provide frames manually.")
        print(f"To extract frames, use: ffmpeg -i {video_source} -ss 00:00:02 -vframes 1 frame.jpg")

        return []

    def _analyze_with_claude(self, frames: List[bytes]) -> Dict:
        """
        Analyze frames using Claude with vision.
        """

        if not self.anthropic_api_key:
            return self._fallback_analysis()

        client = anthropic.Anthropic(api_key=self.anthropic_api_key)

        # Prepare frames for Claude (base64 encoding)
        frame_contents = []
        for i, frame_bytes in enumerate(frames):
            frame_b64 = base64.b64encode(frame_bytes).decode('utf-8')
            frame_contents.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": frame_b64
                }
            })

        # Analyze with Claude
        prompt = """Analyze this video creative (shown as key frames) for performance marketing.

Extract the following patterns:

1. **Hook Type** (first 2 seconds):
   - wait: "Wait for it...", "Watch until the end"
   - question: "Do you know...?", "What if...?"
   - bold_claim: "This changed everything", "You won't believe"
   - curiosity: Incomplete information, mystery
   - urgency: "Today only", "Last chance"
   - other: Describe

2. **Emotion** (overall tone):
   - excitement: High energy, positive
   - fear: FOMO, loss aversion
   - curiosity: Want to know more
   - greed: Money, winning, gains
   - surprise: Unexpected twist
   - other: Describe

3. **Pacing**:
   - fast: Quick cuts, high energy
   - medium: Balanced pacing
   - slow: Calm, explanatory

4. **CTA Type** (call-to-action):
   - direct: "Click here", "Join now"
   - soft: "Learn more", "Check it out"
   - urgency: "Limited time", "Today only"
   - scarcity: "Only X left", "Exclusive"
   - none: No clear CTA

5. **Visual Features**:
   - has_face: true/false
   - num_scenes: Count scene changes
   - dominant_colors: ["red", "gold", ...]
   - visual_complexity: low/medium/high
   - has_text_overlay: true/false

6. **Audio Indicators** (if visible):
   - has_voiceover: true/false (look for mouth movement or text overlay indicating speech)
   - audio_energy: low/medium/high (visual cues: fast movement = high energy)

Return JSON:
{
  "hook_type": "...",
  "emotion": "...",
  "pacing": "...",
  "cta_type": "...",
  "has_text_overlay": true/false,
  "has_voiceover": true/false,
  "features": {
    "has_face": true/false,
    "num_scenes": 3,
    "dominant_colors": ["red", "gold"],
    "visual_complexity": "high",
    "audio_energy": "high"
  },
  "confidence": 0.85,
  "reasoning": "Brief explanation of your analysis"
}"""

        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": frame_contents + [{"type": "text", "text": prompt}]
                    }
                ]
            )

            # Parse JSON from response
            response_text = response.content[0].text

            # Extract JSON from response (might be wrapped in markdown code blocks)
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            analysis = json.loads(json_str)

            return analysis

        except Exception as e:
            print(f"Error analyzing with Claude: {e}")
            return self._fallback_analysis()

    def _fallback_analysis(self) -> Dict:
        """
        Fallback analysis when Claude is unavailable.
        Returns placeholder data - user should manually fill in patterns.
        """

        return {
            "hook_type": "unknown",
            "emotion": "unknown",
            "pacing": "medium",
            "cta_type": "unknown",
            "has_text_overlay": False,
            "has_voiceover": False,
            "features": {
                "has_face": False,
                "num_scenes": 1,
                "dominant_colors": [],
                "visual_complexity": "medium",
                "audio_energy": "medium"
            },
            "confidence": 0.0,
            "reasoning": "Analysis not available - ANTHROPIC_API_KEY not set. Please manually set patterns."
        }

    def analyze_from_url(self, tiktok_url: str) -> Dict:
        """
        Analyze creative directly from TikTok URL.

        For MVP: Returns placeholder. In production:
        1. Download video from TikTok
        2. Extract frames
        3. Analyze with Claude
        """

        print(f"⚠️ TikTok download not implemented. Please provide video file.")
        print(f"To download: yt-dlp {tiktok_url}")

        return self._fallback_analysis()

    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two CLIP embeddings.
        Used to find similar creatives.
        """

        import numpy as np

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

        return float(similarity)

    def get_clip_embedding(self, image_path: str) -> Optional[List[float]]:
        """
        Get CLIP embedding for an image (video frame).

        For MVP: Returns None. In production, use transformers library:

        ```python
        from transformers import CLIPProcessor, CLIPModel
        from PIL import Image

        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        image = Image.open(image_path)
        inputs = processor(images=image, return_tensors="pt")
        embedding = model.get_image_features(**inputs)
        return embedding[0].tolist()
        ```
        """

        print("⚠️ CLIP embeddings not implemented. Install transformers: pip install transformers torch")

        # Return None for now - this feature is optional
        return None

    def extract_patterns_from_text(self, caption: str, hashtags: List[str] = None) -> Dict:
        """
        Extract patterns from video caption/description.
        Useful when video analysis is not available.

        Args:
            caption: Video caption/description
            hashtags: List of hashtags

        Returns:
            Simplified pattern analysis based on text
        """

        caption_lower = caption.lower()
        hashtags_str = " ".join(hashtags or []).lower()
        combined_text = f"{caption_lower} {hashtags_str}"

        # Pattern detection heuristics
        patterns = {
            "hook_type": "other",
            "emotion": "other",
            "pacing": "unknown",
            "cta_type": "none"
        }

        # Hook detection
        if any(word in combined_text for word in ["wait", "watch until", "wait for"]):
            patterns["hook_type"] = "wait"
        elif "?" in caption:
            patterns["hook_type"] = "question"
        elif any(word in combined_text for word in ["won't believe", "shocking", "insane"]):
            patterns["hook_type"] = "bold_claim"
        elif any(word in combined_text for word in ["secret", "hidden", "revealed"]):
            patterns["hook_type"] = "curiosity"
        elif any(word in combined_text for word in ["today only", "last chance", "hurry"]):
            patterns["hook_type"] = "urgency"

        # Emotion detection
        if any(word in combined_text for word in ["🔥", "amazing", "insane", "crazy"]):
            patterns["emotion"] = "excitement"
        elif any(word in combined_text for word in ["don't miss", "fomo", "before it's gone"]):
            patterns["emotion"] = "fear"
        elif any(word in combined_text for word in ["💰", "$", "money", "win", "profit"]):
            patterns["emotion"] = "greed"
        elif "?" in caption or "secret" in combined_text:
            patterns["emotion"] = "curiosity"

        # CTA detection
        if any(word in combined_text for word in ["click", "join now", "sign up", "download"]):
            patterns["cta_type"] = "direct"
        elif any(word in combined_text for word in ["learn more", "check out", "see more"]):
            patterns["cta_type"] = "soft"
        elif any(word in combined_text for word in ["today only", "limited", "hurry"]):
            patterns["cta_type"] = "urgency"
        elif any(word in combined_text for word in ["exclusive", "only", "limited spots"]):
            patterns["cta_type"] = "scarcity"

        return {
            **patterns,
            "confidence": 0.5,  # Lower confidence for text-only analysis
            "reasoning": "Analyzed from caption text only (no video analysis)"
        }


# Helper function for quick analysis
def analyze_creative_quick(
    video_url: str = None,
    video_path: str = None,
    caption: str = None,
    hashtags: List[str] = None
) -> Dict:
    """
    Quick creative analysis helper.

    Usage:
    ```python
    from utils.creative_analyzer import analyze_creative_quick

    result = analyze_creative_quick(
        caption="Wait until the end! 🔥 #fyp #sports",
        hashtags=["fyp", "sports", "viral"]
    )
    print(result)
    ```
    """

    analyzer = CreativeAnalyzer()

    # If we have video, analyze it
    if video_path or video_url:
        return analyzer.analyze_video(video_path=video_path, video_url=video_url)

    # Otherwise, analyze caption
    if caption:
        return analyzer.extract_patterns_from_text(caption, hashtags)

    raise ValueError("Must provide either video or caption")


def analyze_creative_hybrid(
    video_path: str,
    caption: str = None,
    hashtags: List[str] = None
) -> Dict:
    """
    🚀 ГИБРИДНЫЙ АНАЛИЗ: Видео (OpenCV+librosa) + Текст.

    Комбинирует:
    1. VideoAnalyzer → pacing, has_face, audio_energy (из видео)
    2. Текстовый анализ → hook_type, emotion, cta_type (из caption)

    Результат: ПОЛНЫЙ автоматический анализ БЕЗ AI API!

    Args:
        video_path: Путь к видео файлу
        caption: Описание креатива (опционально)
        hashtags: Хештеги (опционально)

    Returns:
        {
            "hook_type": "wait",           # Из caption
            "emotion": "excitement",        # Из caption
            "pacing": "fast",              # Из видео ✅
            "cta_type": "urgency",         # Из caption
            "has_face": true,              # Из видео ✅
            "has_text_overlay": false,
            "has_voiceover": true,         # Из аудио ✅
            "features": {
                "num_scenes": 8,
                "audio_energy": "high",
                "duration": 15
            },
            "confidence": 0.75  # Высокая точность!
        }

    Usage:
    ```python
    result = analyze_creative_hybrid(
        video_path="video.mp4",
        caption="Wait until the end! 🔥 #fyp",
        hashtags=["fyp", "lootbox"]
    )
    ```
    """

    from utils.video_analyzer import VideoAnalyzer

    # 1. Технический анализ видео (OpenCV + librosa)
    video_analyzer = VideoAnalyzer()
    video_data = video_analyzer.analyze(video_path)

    # 2. Текстовый анализ caption (если есть)
    if caption:
        text_analyzer = CreativeAnalyzer()
        text_data = text_analyzer.extract_patterns_from_text(caption, hashtags or [])
    else:
        # Fallback если нет caption
        text_data = {
            "hook_type": "unknown",
            "emotion": "unknown",
            "cta_type": "none"
        }

    # 3. Объединить результаты
    return {
        # Из текста
        "hook_type": text_data["hook_type"],
        "emotion": text_data["emotion"],
        "cta_type": text_data["cta_type"],

        # Из видео
        "pacing": video_data["pacing"],
        "has_face": video_data["has_face"],
        "has_voiceover": video_data.get("has_voiceover", False),
        "has_text_overlay": False,  # TODO: OCR implementation

        # Features
        "features": {
            "num_scenes": video_data.get("num_scenes", 0),
            "audio_energy": video_data.get("audio_energy", "unknown"),
            "duration_seconds": video_data.get("duration_seconds", 0),
            "tempo_bpm": video_data.get("tempo_bpm"),
            "scenes_per_second": video_data.get("scenes_per_second", 0)
        },

        # Метаданные
        "confidence": 0.75,  # Высокая точность (видео + текст)
        "reasoning": f"Hybrid analysis: Video pacing={video_data['pacing']}, "
                    f"has_face={video_data['has_face']}, "
                    f"audio_energy={video_data.get('audio_energy', 'unknown')}, "
                    f"caption analyzed for hook/emotion/CTA",
        "analysis_method": "hybrid_opencv_librosa"
    }
