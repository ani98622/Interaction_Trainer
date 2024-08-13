import whisper
from pydub import AudioSegment
import noisereduce as nr
import numpy as np,io,os

def reduce_noise_in_audio(input_data, format=None) -> bytes:
    if isinstance(input_data, bytes):
        audio = AudioSegment.from_file(io.BytesIO(input_data), format=format)
    elif isinstance(input_data, str) and os.path.isfile(input_data):
        audio = AudioSegment.from_file(input_data)
    else:
        raise ValueError("Input must be a file path or bytes")

    samples = np.array(audio.get_array_of_samples())
    reduced_noise = nr.reduce_noise(samples, sr=audio.frame_rate)
    max_amplitude = np.max(np.abs(reduced_noise))
    normalized_reduced_noise = (reduced_noise / max_amplitude) * np.iinfo(samples.dtype).max
    reduced_audio = AudioSegment(
        normalized_reduced_noise.astype(samples.dtype).tobytes(), 
        frame_rate=audio.frame_rate, 
        sample_width=audio.sample_width, 
        channels=audio.channels
    )

    target_dBFS = audio.dBFS
    change_in_dBFS = target_dBFS - reduced_audio.dBFS
    reduced_audio = reduced_audio.apply_gain(change_in_dBFS)
    audio_io = io.BytesIO()
    reduced_audio.export(audio_io, format="wav")
    audio_io.seek(0)

    # Return bytes
    return audio_io.getvalue()
 

def mark_pauses(transcription, pause_threshold=1):
    words = transcription['segments']
    highlighted_transcript = ""
    temp = words[0]["words"]
    for i in range(len(temp)-1):
        highlighted_transcript += f"{temp[i]['word']}[{temp[i]['start']}-{temp[i]['end']}]"
        pause_duration =temp[i + 1]['start'] - temp[i]['end']
        if pause_duration > pause_threshold:
            highlighted_transcript += "[PAUSE] "
  
    # highlighted_transcript += f"{temp[-1]['word']}[{temp[-1]['start']}-{temp[-1]['end']}]"
    return highlighted_transcript

def return_text(path):
    model = whisper.load_model("base")
    result = model.transcribe(path,
                          temperature=0.4,
                          condition_on_previous_text=False,
                          word_timestamps=True,)
    
    highlighted_transcript = mark_pauses(result)
    return highlighted_transcript


