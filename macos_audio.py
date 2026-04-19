import ctypes
import os
import platform
from ctypes import byref, c_char_p, c_int32, c_uint32, c_void_p, create_string_buffer
from ctypes.util import find_library


if platform.system() != "Darwin":
    raise RuntimeError("macos_audio can only be used on macOS")


class CoreAudioError(RuntimeError):
    pass


def _fourcc(value):
    result = 0
    for char in value.encode("ascii"):
        result = (result << 8) | char
    return result


def _format_status(status):
    unsigned = status & 0xFFFFFFFF
    chars = unsigned.to_bytes(4, "big", signed=False)
    if all(32 <= byte <= 126 for byte in chars):
        return f"{status} ('{chars.decode('ascii')}')"
    return str(status)


def _check_status(status, action):
    if status != 0:
        raise CoreAudioError(f"{action} failed with OSStatus {_format_status(status)}")


class AudioObjectPropertyAddress(ctypes.Structure):
    _fields_ = [
        ("mSelector", c_uint32),
        ("mScope", c_uint32),
        ("mElement", c_uint32),
    ]


CORE_AUDIO = ctypes.cdll.LoadLibrary(find_library("CoreAudio"))
CORE_FOUNDATION = ctypes.cdll.LoadLibrary(find_library("CoreFoundation"))

CORE_AUDIO.AudioObjectGetPropertyDataSize.argtypes = [
    c_uint32,
    ctypes.POINTER(AudioObjectPropertyAddress),
    c_uint32,
    c_void_p,
    ctypes.POINTER(c_uint32),
]
CORE_AUDIO.AudioObjectGetPropertyDataSize.restype = c_int32

CORE_AUDIO.AudioObjectGetPropertyData.argtypes = [
    c_uint32,
    ctypes.POINTER(AudioObjectPropertyAddress),
    c_uint32,
    c_void_p,
    ctypes.POINTER(c_uint32),
    c_void_p,
]
CORE_AUDIO.AudioObjectGetPropertyData.restype = c_int32

CORE_AUDIO.AudioObjectSetPropertyData.argtypes = [
    c_uint32,
    ctypes.POINTER(AudioObjectPropertyAddress),
    c_uint32,
    c_void_p,
    c_uint32,
    c_void_p,
]
CORE_AUDIO.AudioObjectSetPropertyData.restype = c_int32

CORE_FOUNDATION.CFStringGetCString.argtypes = [c_void_p, c_char_p, ctypes.c_long, c_uint32]
CORE_FOUNDATION.CFStringGetCString.restype = ctypes.c_bool
CORE_FOUNDATION.CFRelease.argtypes = [c_void_p]
CORE_FOUNDATION.CFRelease.restype = None


K_AUDIO_OBJECT_SYSTEM_OBJECT = 1
K_AUDIO_OBJECT_PROPERTY_SCOPE_GLOBAL = _fourcc("glob")
K_AUDIO_OBJECT_PROPERTY_SCOPE_OUTPUT = _fourcc("outp")
K_AUDIO_OBJECT_PROPERTY_ELEMENT_MAIN = 0
K_AUDIO_HARDWARE_PROPERTY_DEVICES = _fourcc("dev#")
K_AUDIO_HARDWARE_PROPERTY_DEFAULT_OUTPUT_DEVICE = _fourcc("dOut")
K_AUDIO_OBJECT_PROPERTY_NAME = _fourcc("lnam")
K_AUDIO_DEVICE_PROPERTY_HOG_MODE = _fourcc("oink")
K_AUDIO_DEVICE_PROPERTY_STREAMS = _fourcc("stm#")
K_CF_STRING_ENCODING_UTF8 = 0x08000100
K_HOG_MODE_NONE = -1


def _address(selector, scope=K_AUDIO_OBJECT_PROPERTY_SCOPE_GLOBAL, element=K_AUDIO_OBJECT_PROPERTY_ELEMENT_MAIN):
    return AudioObjectPropertyAddress(selector, scope, element)


def _get_data_size(object_id, selector, scope=K_AUDIO_OBJECT_PROPERTY_SCOPE_GLOBAL):
    address = _address(selector, scope)
    data_size = c_uint32(0)
    status = CORE_AUDIO.AudioObjectGetPropertyDataSize(
        c_uint32(object_id),
        byref(address),
        0,
        None,
        byref(data_size),
    )
    _check_status(status, f"AudioObjectGetPropertyDataSize for selector {selector}")
    return data_size.value


def _get_u32_property(object_id, selector, scope=K_AUDIO_OBJECT_PROPERTY_SCOPE_GLOBAL):
    address = _address(selector, scope)
    value = c_uint32()
    data_size = c_uint32(ctypes.sizeof(value))
    status = CORE_AUDIO.AudioObjectGetPropertyData(
        c_uint32(object_id),
        byref(address),
        0,
        None,
        byref(data_size),
        byref(value),
    )
    _check_status(status, f"AudioObjectGetPropertyData for selector {selector}")
    return value.value


def _get_pid_property(object_id, selector, scope=K_AUDIO_OBJECT_PROPERTY_SCOPE_GLOBAL):
    address = _address(selector, scope)
    value = c_int32()
    data_size = c_uint32(ctypes.sizeof(value))
    status = CORE_AUDIO.AudioObjectGetPropertyData(
        c_uint32(object_id),
        byref(address),
        0,
        None,
        byref(data_size),
        byref(value),
    )
    _check_status(status, f"AudioObjectGetPropertyData for selector {selector}")
    return value.value


def _get_cfstring_property(object_id, selector, scope=K_AUDIO_OBJECT_PROPERTY_SCOPE_GLOBAL):
    address = _address(selector, scope)
    value = c_void_p()
    data_size = c_uint32(ctypes.sizeof(value))
    status = CORE_AUDIO.AudioObjectGetPropertyData(
        c_uint32(object_id),
        byref(address),
        0,
        None,
        byref(data_size),
        byref(value),
    )
    _check_status(status, f"AudioObjectGetPropertyData for selector {selector}")

    if not value.value:
        return ""

    try:
        buffer = create_string_buffer(512)
        success = CORE_FOUNDATION.CFStringGetCString(
            value,
            buffer,
            len(buffer),
            K_CF_STRING_ENCODING_UTF8,
        )
        if not success:
            raise CoreAudioError("CFStringGetCString failed")
        return buffer.value.decode("utf-8")
    finally:
        CORE_FOUNDATION.CFRelease(value)


def _get_device_ids():
    data_size = _get_data_size(K_AUDIO_OBJECT_SYSTEM_OBJECT, K_AUDIO_HARDWARE_PROPERTY_DEVICES)
    count = data_size // ctypes.sizeof(c_uint32)
    buffer = (c_uint32 * count)()
    address = _address(K_AUDIO_HARDWARE_PROPERTY_DEVICES)
    actual_size = c_uint32(data_size)
    status = CORE_AUDIO.AudioObjectGetPropertyData(
        c_uint32(K_AUDIO_OBJECT_SYSTEM_OBJECT),
        byref(address),
        0,
        None,
        byref(actual_size),
        byref(buffer),
    )
    _check_status(status, "AudioObjectGetPropertyData for device list")
    return [buffer[index] for index in range(count)]


def _device_has_output_streams(device_id):
    try:
        return _get_data_size(device_id, K_AUDIO_DEVICE_PROPERTY_STREAMS, K_AUDIO_OBJECT_PROPERTY_SCOPE_OUTPUT) > 0
    except CoreAudioError:
        return False


def list_output_devices():
    devices = []
    for device_id in _get_device_ids():
        if not _device_has_output_streams(device_id):
            continue
        devices.append(
            {
                "id": int(device_id),
                "name": _get_cfstring_property(device_id, K_AUDIO_OBJECT_PROPERTY_NAME),
                "hog_pid": _get_pid_property(device_id, K_AUDIO_DEVICE_PROPERTY_HOG_MODE),
            }
        )
    return devices


def get_default_output_device():
    device_id = _get_u32_property(K_AUDIO_OBJECT_SYSTEM_OBJECT, K_AUDIO_HARDWARE_PROPERTY_DEFAULT_OUTPUT_DEVICE)
    return {
        "id": int(device_id),
        "name": _get_cfstring_property(device_id, K_AUDIO_OBJECT_PROPERTY_NAME),
        "hog_pid": _get_pid_property(device_id, K_AUDIO_DEVICE_PROPERTY_HOG_MODE),
    }


def find_output_device_by_name(name):
    normalized = (name or "").strip().lower()
    if not normalized:
        return get_default_output_device()

    exact_match = None
    prefix_match = None
    for device in list_output_devices():
        device_name = device["name"].strip().lower()
        if device_name == normalized:
            exact_match = device
            break
        if normalized in device_name or device_name in normalized:
            prefix_match = device

    if exact_match is not None:
        return exact_match
    if prefix_match is not None:
        return prefix_match
    raise CoreAudioError(f"Output device not found in Core Audio for name: {name}")


def get_hog_mode_pid(device_name=None, device_id=None):
    if device_id is None:
        device_id = find_output_device_by_name(device_name)["id"]
    return _get_pid_property(device_id, K_AUDIO_DEVICE_PROPERTY_HOG_MODE)


def acquire_hog_mode(device_name=None, device_id=None):
    if device_id is None:
        device = find_output_device_by_name(device_name)
        device_id = device["id"]
    current_pid = get_hog_mode_pid(device_id=device_id)
    own_pid = os.getpid()
    if current_pid not in (K_HOG_MODE_NONE, own_pid):
        raise CoreAudioError(f"Device is already in hog mode by PID {current_pid}")

    address = _address(K_AUDIO_DEVICE_PROPERTY_HOG_MODE)
    value = c_int32(own_pid)
    status = CORE_AUDIO.AudioObjectSetPropertyData(
        c_uint32(device_id),
        byref(address),
        0,
        None,
        c_uint32(ctypes.sizeof(value)),
        byref(value),
    )
    _check_status(status, "AudioObjectSetPropertyData for hog mode acquire")
    return get_hog_mode_pid(device_id=device_id)


def release_hog_mode(device_name=None, device_id=None):
    if device_id is None:
        device = find_output_device_by_name(device_name)
        device_id = device["id"]
    current_pid = get_hog_mode_pid(device_id=device_id)
    own_pid = os.getpid()
    if current_pid not in (K_HOG_MODE_NONE, own_pid):
        raise CoreAudioError(f"Cannot release hog mode owned by PID {current_pid}")

    address = _address(K_AUDIO_DEVICE_PROPERTY_HOG_MODE)
    value = c_int32(K_HOG_MODE_NONE)
    status = CORE_AUDIO.AudioObjectSetPropertyData(
        c_uint32(device_id),
        byref(address),
        0,
        None,
        c_uint32(ctypes.sizeof(value)),
        byref(value),
    )
    _check_status(status, "AudioObjectSetPropertyData for hog mode release")
    return get_hog_mode_pid(device_id=device_id)
