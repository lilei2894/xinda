import threading
from collections import defaultdict

_stream_data = defaultdict(dict)
_stream_lock = threading.Lock()

def set_stream_data(record_id: str, key: str, value):
    with _stream_lock:
        _stream_data[record_id][key] = value

def get_stream_data(record_id: str):
    with _stream_lock:
        return dict(_stream_data.get(record_id, {}))

def append_stream_text(record_id: str, key: str, text: str, page: int = None):
    with _stream_lock:
        if page:
            page_key = f"{key}_page_{page}"
            if page_key not in _stream_data[record_id]:
                _stream_data[record_id][page_key] = ""
            _stream_data[record_id][page_key] += text
        else:
            if key not in _stream_data[record_id]:
                _stream_data[record_id][key] = ""
            _stream_data[record_id][key] += text

def get_stream_page_text(record_id: str, key: str, page: int) -> str:
    with _stream_lock:
        page_key = f"{key}_page_{page}"
        return _stream_data.get(record_id, {}).get(page_key, "")

def clear_stream_data(record_id: str):
    with _stream_lock:
        if record_id in _stream_data:
            del _stream_data[record_id]

def set_stream_status(record_id: str, status: str):
    with _stream_lock:
        _stream_data[record_id]['status'] = status