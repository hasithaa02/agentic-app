from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re

YT_REGEX = re.compile(r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})")

def fetch_youtube_transcript(url_or_id: str):
    # Extract video id if url provided
    m = YT_REGEX.search(url_or_id)
    vid = m.group(1) if m else url_or_id
    try:
        transcript = YouTubeTranscriptApi.get_transcript(vid, languages=['en'])
        # transcript is list of dicts {'text':..., 'start':..., 'duration':...}
        joined = " ".join([t['text'] for t in transcript])
        return {"text": joined, "raw": transcript}
    except TranscriptsDisabled:
        return {"error": "transcripts_disabled", "message": "Transcripts disabled for this video"}
    except NoTranscriptFound:
        return {"error": "no_transcript", "message": "No transcript found for this video"}
    except Exception as e:
        return {"error": "other", "message": str(e)}
