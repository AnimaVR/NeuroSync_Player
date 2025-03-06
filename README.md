# NeuroSync Player

### **06/03/2025 Bug fixes + update to llm_to_face.py + added twitch_llm.py for connecting your llm to twitch**

- Text to audio when using Elevenlabs was returning static. Bug left over from OpenAI realtime addition, fixed.
- Realtime audio loading then needed correcting, temporary fix added.
- Refactored everything to keep it in its own place. Some things are still messy and are a WIP.

*Updates*

- llm_to_face.py updated to add push to talk, with whisper integration (you need to supply your own api destination) for <1 sec responses from an LLM locally with animation and speech.
      - this means we go voice in to voice + face animation out, if you have the GPU memory for Llama3, whisper, someTTS + neurosync + unreal project.
      - its better/faster/cheaper than OpenAI realtime api by a long way.

- Added Llama3.1 api samples to help you get started with LLM integration locally.

- twitch_llm.py added to allow connection of llm powered metahuman to the chat so it can respond to its viewers.

### **01/03/2025 WIP OpenAI realtime API integration**

*Work in progress* so dont expect it to be perfect, but we are exploring how to stream the realtime api with the face data - it works, with some caveats : 

- It's expensive, first and foremost. Actually waaaay too expensive to use daily. (local realtime api demo inc ;) )
- its push to talk, hold right ctrl to speak then release
- Boundries can have occasional skips, needs some blending work
- No long term memory
- Set voice

Generally, i prefer the chunk at the sentence option while using a normal, cheaper, local LLM - but people keep asking for this, so here is the start, to get you started. ;)

FYI : Realtime is very much reliant on short inputs to get short answers with very little context - outside of this, chunking at the sentence from a normal LLM is still faster to respond with animation than the realtime api. Have a play though, its down to your use case.

### **21/02/2025 Scaling UP! | New 228m parameter model + config added**

A milestone has been hit and previous research has got us to a point where scaling the model up is now possible with much faster training and better quality overall.

Going from 4 layers and 4 heads to 8 layers and 16 heads means updating your code and model, please ensure you have the latest versions of the api and player as the new model requires some architectural changes.

Enjoy!

### **19/02/2025 Trainer updates**

- **Trainer**: Use [NeuroSync Trainer Lite](https://github.com/AnimaVR/NeuroSync_Trainer_Lite) for training and fine-tuning.

- **Simplified Loss** Removed second order smoothness loss (left code in if you want to research the differences, mostly it just squeezes the end result resulting in choppy animation without smoothing)
- **Mixed Precision** Less memory usage and faster training
- **Data augmentation** Interpolate a slow set and a fast set of data from your data to help with fine detail reproduction, uses a lot of memory so /care - generally just adding the fast is best as adding slow over saturates the data with slow and noisey data (more work to do here... obv's!)


## NEW : llm_to_face.py *Streaming + queue added for faster response times as well as local tts option*

Toy demo of how one might talk to an AI using Neurosync with context added for multi-turn.

Use a local llm or OpenAI api, just set the bool and add your key.

**Demo Build**: [Download the demo build](https://drive.google.com/drive/folders/1q-CYauPqyWfvs8NamW4QuC1H1r02RYMQ?usp=sharing) to test NeuroSync with an Unreal Project (aka, free realistic AI companion when used with llm_to_face.py *wink* )

## [Train your own model](https://github.com/AnimaVR/NeuroSync_Trainer_Lite)

## Talk to a NeuroSync prototype live on Twitch : [Visit Mai](https://www.twitch.tv/mai_anima_ai)

## Overview

The **NeuroSync Player** allows for real-time streaming of facial blendshapes into Unreal Engine 5 using LiveLink - enabling facial animation from audio input.

![Alt text](/utils/neurosyncclose.jpg)

### Features:
- Real-time facial animation
- Integration with Unreal Engine 5 via LiveLink
- Supports blendshapes generated from audio inputs

## NeuroSync Model

To generate facial blendshapes from audio, you'll need the **NeuroSync audio-to-face blendshape transformer model**. You can:

- [Apply for Alpha API access](https://neurosync.info) to use the model without locally hosting it.
- - Or, if you'd like to host the model locally, you can set up the [NeuroSync Local API](https://github.com/AnimaVR/NeuroSync_Local_API).
    - [Download the model from Hugging Face](https://huggingface.co/AnimaVR/NEUROSYNC_Audio_To_Face_Blendshape)

### Switching Between Local and Non-Local API

The player can connect to either the **local API** or the **alpha API** depending on your needs. To switch between the two, simply change the boolean value in the `utils/neurosync_api_connect.py` file:

Visit [neurosync.info](https://neurosync.info) to sign up for alpha access.
