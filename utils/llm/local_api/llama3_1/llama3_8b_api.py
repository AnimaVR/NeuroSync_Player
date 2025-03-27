# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

from flask import Flask, request, jsonify, Response
from llama import Llama
import os
import sys
import subprocess
import torch

app = Flask(__name__)
ckpt_dir = os.path.join(os.path.dirname(__file__), 'ckpt')
tokenizer_path = os.path.join(os.path.dirname(__file__), 'tokenizer.model')
generator = Llama.build(
    ckpt_dir=ckpt_dir,
    tokenizer_path=tokenizer_path,
    max_seq_len=8192,
    max_batch_size=1,
)

@app.route('/generate_llama', methods=['POST'])
def generate():
    if request.method == 'POST':
        data = request.get_json(force=True)
        
        messages = data.get('messages', '')
        print("Prompt:\n", messages)

        max_new_tokens = data.get('max_new_tokens', 1000)
        temperature = data.get('temperature', 1)
        top_p = data.get('top_p', 0.9)

        try:
            result = generator.chat_completion(
                [messages],
                max_gen_len=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
            )[0]
            
            result_content = result['generation']['content']
            print("Assistant Response:\n", result_content)
            
            response = {
                'assistant': {
                    'role': 'assistant',
                    'content': result_content
                }
            }
            return jsonify(response)
        except torch.OutOfMemoryError:
            handle_oom_error()
            return jsonify({"error": "Out of memory. Please reduce the response length and try again."}), 500


@app.route('/generate_stream', methods=['POST'])
def generatestream():
    if request.method == 'POST':
        data = request.get_json(force=True)

        messages = data.get('messages', '')
        if not messages:
            return jsonify({"error": "No messages provided"}), 400

        # Verify each message has 'role' and 'content'
        for msg in messages:
            if 'role' not in msg or 'content' not in msg:
                return jsonify({"error": "Each message must have 'role' and 'content'"}), 400

        max_new_tokens = data.get('max_new_tokens', 1000)
        temperature = data.get('temperature', 1)
        top_p = data.get('top_p', 0.9)

        def generate_stream():
            try:
                stream = generator.stream_chat_completion(
                    [messages],
                    max_gen_len=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                )
                response = ""
                for token in stream:
                    response += token
                    yield f"{token}"
                print("Assistant Response:\n", response)
            except torch.OutOfMemoryError:
                handle_oom_error()
                yield "Out of memory. Please reduce the response length and try again."

        return Response(generate_stream(), content_type='text/plain')


def handle_oom_error():
    print("CUDA OutOfMemoryError encountered. Restarting Flask server...", file=sys.stderr)
    try:
        # Restart the current Python script
        subprocess.Popen([sys.executable] + sys.argv)
        os._exit(1)  # Forcefully exit the current process
    except Exception as e:
        print(f"Failed to restart server: {e}", file=sys.stderr)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)
