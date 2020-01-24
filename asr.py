import io
import os
import argparse
from glob import glob
from tqdm import tqdm
from jiwer import wer

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

# python asr.py -i input, wav with 16k/8k hz, 16bit, and signed integer PCM encoding, single channel
# python asr.py -d input, folder

# Instantiates a client
client = speech.SpeechClient()
config = types.RecognitionConfig(
    encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=8000,
    language_code='en-US')
    #enable_automatic_punctuation=True)
streaming_config = types.StreamingRecognitionConfig(config=config)

parser=argparse.ArgumentParser()
parser.add_argument('-i', '--input', help='input file to asr')
parser.add_argument('-d', '--input_dir', help='input file to asr')
args=parser.parse_args()

if args.input is not None:
    with io.open(args.input, 'rb') as audio_file:
        content = audio_file.read()
        audio = types.RecognitionAudio(content=content)

    stream = [content]
    requests = (types.StreamingRecognizeRequest(audio_content=chunk)
                        for chunk in stream)

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

    #Straming
    # streaming_recognize returns a generator.
    responses = client.streaming_recognize(streaming_config, requests)

    for response in responses:
        # Once the transcription has settled, the first result will contain the
        # is_final result. The other results will be for subsequent portions of
        # the audio.
        for result in response.results:
            print('Finished: {}'.format(result.is_final))
            print('Stability: {}'.format(result.stability))
            alternatives = result.alternatives
            print('Confidence: {}'.format(alternatives[0].confidence))
            print(u'Transcript: {}'.format(alternatives[0].transcript))
            ## The alternatives are ordered from most likely to least.
            #for alternative in alternatives:
            #    print('Confidence: {}'.format(alternative.confidence))
            #    print(u'Transcript: {}'.format(alternative.transcript))
    exit()

def generate_txt_files(wav_files):
    def text_postprocess(text):
        text=text.replace('.', '')
        text=text.replace(',', '')
        text=text.lower()
        return text

    for file_name in tqdm(wav_files):
        # Loads the audio into memory
        with io.open(file_name, 'rb') as audio_file:
            content = audio_file.read()
            #audio = types.RecognitionAudio(content=content)

        # SHORT
        #response = client.recognize(config, audio)
        ## Each result is for a consecutive portion of the audio. Iterate through
        ## them to get the transcripts for the entire audio file.
        #if len(response.results) > 1:
        #    print("More than one portion %s" % file_name)
        #    texts=[]
        #    for result in response.results:
        #        texts.append(result.alternatives[0].transcript)
        #    text=' '.join(texts)
        #elif len(response.results) == 0:
        #    print("No transcript %s" % file_name)
        #    text=''
        #else:
        #    text=response.results[0].alternatives[0].transcript

        # Streaming
        stream = [content]
        requests = (types.StreamingRecognizeRequest(audio_content=chunk)
                            for chunk in stream)
        responses_itr = client.streaming_recognize(streaming_config, requests)
        responses=[]
        for response in responses_itr:
            responses.append(response)
        # Each result is for a consecutive portion of the audio. Iterate through
        # them to get the transcripts for the entire audio file.
        if len(responses) > 0:
            if len(responses) >1:
                print("More than one response %s" % file_name)
            texts=[]
            for response in responses:
                if len(response.results) > 0:
                    if len(response.results) >1:
                        print("More than one result %s" % file_name)
                    for result in response.results:
                        texts.append(result.alternatives[0].transcript)
                else:
                    print("No result %s" % file_name)
            text=' '.join(texts)
        else:
            print("No response %s" % file_name)
            text=''

        text=text_postprocess(text)
        wav_parent=os.path.dirname(file_name)
        wav_name=os.path.basename(file_name)
        wav_id='_'.join(wav_name.split('_')[:3])
        text_file="%s/%s.txt" % (wav_parent, wav_id)
        with open(text_file, 'w') as f:
            f.write(text.lower())

import pdb;pdb.set_trace()
estimate_wavs=glob("%s/estimate*.wav" % args.input_dir)
target_wavs=glob("%s/target*.wav" % args.input_dir)
#generate_txt_files(estimate_wavs)
#generate_txt_files(target_wavs)


estimate_txts=glob("%s/estimate*.txt" % args.input_dir)
target_txts=glob("%s/target*.txt" % args.input_dir)
trans_txts=glob("%s/trans*.txt" % args.input_dir)

estimate_txts.sort()
target_txts.sort()
trans_txts.sort()
assert len(estimate_txts) == len(target_txts) == len(trans_txts)
#import pdb;pdb.set_trace()
estimate_contents, target_contents, trans_contents=[], [], []
for file_name in estimate_txts:
    with open(file_name) as f:
        text=f.readline().strip()
        text=text.replace('.', '')
        text=text.replace(',', '')
        text=text.lower()
        estimate_contents.append(text)
for file_name in target_txts:
    with open(file_name) as f:
        text=f.readline().strip()
        text=text.replace('.', '')
        text=text.replace(',', '')
        text=text.lower()
        target_contents.append(text)
for file_name in trans_txts:
    with open(file_name) as f:
        text=f.readline().strip()
        text=text.replace('.', '')
        text=text.replace(',', '')
        text=text.lower()
        trans_contents.append(text)

error_estimate=wer(trans_contents, estimate_contents)
print("Estimate WER: %.2f" % error_estimate)
error_target=wer(trans_contents, target_contents)
print("Target WER: %.2f" % error_target)
