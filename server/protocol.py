import struct

# Struct layout:
# <  : little-endian
# H  : uint16 (buttons bitmask, 2 bytes)
# h  : int16 (left stick x, 2 bytes)
# h  : int16 (left stick y, 2 bytes)
# h  : int16 (right stick x, 2 bytes)
# h  : int16 (right stick y, 2 bytes)
# B  : uint8 (left trigger, 1 byte)
# B  : uint8 (right trigger, 1 byte)
# Total = 12 bytes
INPUT_FRAME_FORMAT = '<HhhhhBB'
INPUT_FRAME_SIZE = struct.calcsize(INPUT_FRAME_FORMAT)

RUMBLE_FRAME_FORMAT = '<BBB'
RUMBLE_FRAME_SIZE = struct.calcsize(RUMBLE_FRAME_FORMAT)
RUMBLE_OPCODE = 0x01

def clamp_int16(val: int) -> int:
    return max(-32768, min(32767, int(val)))

def clamp_uint8(val: int) -> int:
    return max(0, min(255, int(val)))

def clamp_uint16(val: int) -> int:
    return max(0, min(65535, int(val)))

def pack_input_frame(buttons: int, lx: int, ly: int, rx: int, ry: int, lt: int, rt: int) -> bytes:
    """Packs controller state into a 12-byte binary frame."""
    return struct.pack(
        INPUT_FRAME_FORMAT,
        clamp_uint16(buttons),
        clamp_int16(lx),
        clamp_int16(ly),
        clamp_int16(rx),
        clamp_int16(ry),
        clamp_uint8(lt),
        clamp_uint8(rt)
    )

def unpack_input_frame(payload: bytes) -> tuple[int, int, int, int, int, int, int]:
    """Unpacks a 12-byte binary frame into (buttons, lx, ly, rx, ry, lt, rt)."""
    if len(payload) != INPUT_FRAME_SIZE:
        raise ValueError(f"Expected {INPUT_FRAME_SIZE} bytes for input frame, got {len(payload)}")
    return struct.unpack(INPUT_FRAME_FORMAT, payload)

def pack_rumble_frame(left_motor: int, right_motor: int) -> bytes:
    """Packs a 3-byte downstream rumble frame."""
    return struct.pack(
        RUMBLE_FRAME_FORMAT,
        RUMBLE_OPCODE,
        clamp_uint8(left_motor),
        clamp_uint8(right_motor)
    )

def unpack_rumble_frame(payload: bytes) -> tuple[int, int]:
    """Unpacks a 3-byte rumble frame, returning (left_motor, right_motor)."""
    if len(payload) != RUMBLE_FRAME_SIZE:
        raise ValueError(f"Expected {RUMBLE_FRAME_SIZE} bytes for rumble frame, got {len(payload)}")
    opcode, left, right = struct.unpack(RUMBLE_FRAME_FORMAT, payload)
    if opcode != RUMBLE_OPCODE:
        raise ValueError(f"Invalid rumble opcode: {opcode}")
    return left, right
