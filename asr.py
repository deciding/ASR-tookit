import io
import os
import argparse

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

# Instantiates a client
client = speech.SpeechClient()

parser=argparse.ArgumentParser()
parser.add_argument('-i', '--input', required=True, help='input file to asr')
args=parser.parse_args()

# The name of the audio file to transcribe
file_name = os.path.join(
    os.path.dirname(__file__),
    #'resources',
    #'estimate_0008_00211_14_29.wav'
    args.input
    )

# Loads the audio into memory
with io.open(file_name, 'rb') as audio_file:
    content = audio_file.read()
    audio = types.RecognitionAudio(content=content)

config = types.RecognitionConfig(
    encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
    #sample_rate_hertz=8000,
    language_code='en-US',
    enable_automatic_punctuation=True)

# SHORT
response = client.recognize(config, audio)
# Each result is for a consecutive portion of the audio. Iterate through
# them to get the transcripts for the entire audio file.
for result in response.results:
    # The first alternative is the most likely one for this portion.
    print(u'Transcript: {}'.format(result.alternatives[0].transcript))
    print('Confidence: {}'.format(result.alternatives[0].confidence))

# LONG, but slow
operation = client.long_running_recognize(config, audio)
response = operation.result(timeout=1800)
# Each result is for a consecutive portion of the audio. Iterate through
# them to get the transcripts for the entire audio file.
for result in response.results:
    # The first alternative is the most likely one for this portion.
    print(u'Transcript: {}'.format(result.alternatives[0].transcript))
    print('Confidence: {}'.format(result.alternatives[0].confidence))
