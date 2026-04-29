# -*- coding: utf-8 -*-
"""虚拟女友 - Flask 主入口"""

import os
import json
import sys
import threading
import base64
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from config import *
from ai_engine import AIEngine
from memory import Memory
from character_manager import CharacterManager, Character
from voice import VoiceEngine

# ============================================================
# 应用初始化
# ============================================================
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'virtual-girlfriend-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局实例
ai_engine = AIEngine(API_KEY, BASE_URL, MODEL)
memory = Memory()
char_mgr = CharacterManager()
voice_engine = VoiceEngine(TTS_VOICE)

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'settings.json')

# 当前活动的会话
active_conversations = {}


def load_settings() -> dict:
    """加载用户设置"""
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_settings(settings: dict):
    """保存用户设置"""
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def apply_settings(settings: dict):
    """应用设置到 AI 引擎"""
    api_key = settings.get('api_key', API_KEY)
    base_url = settings.get('base_url', BASE_URL)
    model = settings.get('model', MODEL)
    max_token = settings.get('max_token', MAX_TOKEN)
    temperature = settings.get('temperature', TEMPERATURE)
    ai_engine.update_config(api_key, base_url, model, max_token, temperature)

    # 语音设置
    tts_voice = settings.get('tts_voice', TTS_VOICE)
    voice_engine.set_voice(tts_voice)


# 启动时加载设置
apply_settings(load_settings())


# ============================================================
# API 路由
# ============================================================
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/characters', methods=['GET'])
def api_list_characters():
    """获取角色列表"""
    chars = char_mgr.list_characters()
    if not chars:
        # 创建默认角色
        char_mgr.create_default_character()
        chars = char_mgr.list_characters()
    return jsonify([c.to_dict() for c in chars])


@app.route('/api/characters', methods=['POST'])
def api_save_character():
    """保存角色"""
    data = request.json
    char = Character.from_dict(data)
    char_mgr.save_character(char)
    return jsonify({"status": "ok", "name": char.name})


@app.route('/api/characters/<name>', methods=['GET'])
def api_get_character(name: str):
    """获取角色详情"""
    char = char_mgr.get_character(name)
    if char:
        return jsonify(char.to_dict())
    return jsonify({"error": "角色不存在"}), 404


@app.route('/api/characters/<name>', methods=['DELETE'])
def api_delete_character(name: str):
    """删除角色"""
    if char_mgr.delete_character(name):
        return jsonify({"status": "ok"})
    return jsonify({"error": "删除失败"}), 404


@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """获取设置"""
    return jsonify(load_settings())


@app.route('/api/settings', methods=['POST'])
def api_save_settings():
    """保存设置"""
    settings = request.json
    save_settings(settings)
    apply_settings(settings)
    return jsonify({"status": "ok"})


@app.route('/api/conversation/<character_name>', methods=['GET'])
def api_get_conversation(character_name: str):
    """获取与指定角色的聊天记录"""
    conv_id = memory.get_or_create_conversation(character_name)
    history = memory.get_chat_history(conv_id)
    return jsonify(history)


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """非流式聊天（备用）"""
    data = request.json
    character_name = data.get('character', '小暖')
    user_message = data.get('message', '')
    image_data = data.get('image', None)

    char = char_mgr.get_character(character_name)
    if not char:
        return jsonify({"error": "角色不存在"}), 404

    conv_id = memory.get_or_create_conversation(character_name)
    history = memory.get_history(conv_id)

    # 构建上下文格式
    context_history = []
    for h in history:
        if h.get('role') == 'user':
            context_history.append({"user": h['content']})
        elif h.get('role') == 'assistant':
            if context_history:
                context_history[-1]['ai'] = h['content']

    reply = ai_engine.chat_once(char.prompt, context_history, user_message, image_data)

    # 保存消息
    memory.add_message(conv_id, 'user', user_message, 'text', image_data)
    memory.add_message(conv_id, 'assistant', reply)

    return jsonify({"reply": reply})


@socketio.on('chat_message')
def handle_chat_message(data):
    """WebSocket 流式聊天"""
    character_name = data.get('character', '小暖')
    user_message = data.get('message', '')
    image_data = data.get('image', None)

    char = char_mgr.get_character(character_name)
    if not char:
        emit('chat_error', {"error": "角色不存在"})
        return

    conv_id = memory.get_or_create_conversation(character_name)
    history = memory.get_history(conv_id)

    # 构建上下文
    context_history = []
    for h in history:
        if h.get('role') == 'user' and not h.get('image'):
            context_history.append({"user": h['content']})
        elif h.get('role') == 'assistant':
            if context_history and 'ai' not in context_history[-1]:
                context_history[-1]['ai'] = h['content']

    # 保存用户消息
    memory.add_message(conv_id, 'user', user_message, 'text', image_data)

    # 流式输出
    full_reply = ""
    for chunk in ai_engine.chat_stream(char.prompt, context_history, user_message, image_data):
        full_reply += chunk
        emit('chat_chunk', {"chunk": chunk, "done": False})

    # 保存 AI 回复
    memory.add_message(conv_id, 'assistant', full_reply)

    # TTS 语音合成
    audio_data = None
    if ENABLE_TTS:
        audio_data = voice_engine.synthesize(full_reply)

    emit('chat_chunk', {
        "chunk": "",
        "done": True,
        "full_reply": full_reply,
        "audio": audio_data
    })


@socketio.on('generate_image')
def handle_generate_image(data):
    """AI 生成图片"""
    prompt = data.get('prompt', '')
    if not prompt:
        emit('image_result', {"error": "请提供图片描述"})
        return

    url = ai_engine.generate_image(
        prompt,
        api_key=load_settings().get('painting_api_key', PAINTING_API_KEY),
        base_url=load_settings().get('painting_base_url', PAINTING_BASE_URL),
        model=load_settings().get('painting_model', PAINTING_MODEL)
    )

    if url:
        emit('image_result', {"url": url, "prompt": prompt})
    else:
        emit('image_result', {"error": "图片生成失败"})


@socketio.on('synthesize_speech')
def handle_synthesize_speech(data):
    """TTS 语音合成"""
    text = data.get('text', '')
    if not text:
        return
    audio = voice_engine.synthesize(text)
    emit('speech_result', {"audio": audio})


# ============================================================
# PyWebView 窗口
# ============================================================
def create_window():
    """创建桌面窗口"""
    try:
        import webview

        window = webview.create_window(
            title='虚拟女友',
            url='http://localhost:{}'.format(PORT),
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            min_size=(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT),
            resizable=True,
            text_select=True,
        )
        webview.start(
            gui='cef',
            private_mode=False,
            debug=False
        )
    except ImportError:
        print("PyWebView 未安装，请在浏览器中访问 http://localhost:{}".format(PORT))
        input("按 Enter 退出...")


# ============================================================
# 启动入口
# ============================================================
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='虚拟女友')
    parser.add_argument('--no-window', action='store_true', help='不显示桌面窗口，仅启动 Web 服务')
    args = parser.parse_args()

    # 确保默认角色存在
    if not char_mgr.list_characters():
        char_mgr.create_default_character()

    if args.no_window:
        print(f"服务启动: http://localhost:{PORT}")
        socketio.run(app, host='127.0.0.1', port=PORT, debug=False, allow_unsafe_werkzeug=True)
    else:
        # 启动 Flask 服务线程
        flask_thread = threading.Thread(
            target=lambda: socketio.run(app, host='127.0.0.1', port=PORT,
                                        debug=False, use_reloader=False,
                                        allow_unsafe_werkzeug=True),
            daemon=True
        )
        flask_thread.start()
        print(f"正在启动虚拟女友... (http://localhost:{PORT})")
        create_window()
