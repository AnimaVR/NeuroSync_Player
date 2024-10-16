# NeuroSync Player

## Overview

The **NeuroSync Player** allows for real-time streaming of facial blendshapes into Unreal Engine 5 using LiveLink. This player integrates seamlessly with the **NeuroSync audio-to-face blendshape model**, enabling facial animation from audio input.

### Features:
- Real-time facial animation
- Integration with Unreal Engine 5 via LiveLink
- Supports blendshapes generated from audio inputs

## Get Started

Refer to our [YouTube channel](https://www.youtube.com/@animaai_mai) where we showcase the latest progress on the training, player and tools.

## NeuroSync Model

To generate facial blendshapes from audio, you'll need the **NeuroSync audio-to-face blendshape transformer model**. You can:

- [Apply for Alpha API access](https://neurosync.info) to use the model without locally hosting it.
- - Or, if you'd like to host the model locally, you can set up the [NeuroSync Local API](https://github.com/AnimaVR/NeuroSync_Local_API).
    - [Download the model from Hugging Face](https://huggingface.co/AnimaVR/NEUROSYNC_Audio_To_Face_Blendshape)

### Switching Between Local and Non-Local API

The player can connect to either the **local API** or the **alpha API** depending on your needs. To switch between the two, simply change the boolean value in the `utils/neurosync_api_connect.py` file:


Visit [neurosync.info](https://neurosync.info) for more information or to sign up for alpha access.
