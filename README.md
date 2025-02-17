# NeuroSync Player

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
