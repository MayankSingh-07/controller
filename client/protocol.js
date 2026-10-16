// client/protocol.js - Ultra-low latency binary protocol encoder/decoder
(function (global) {
  'use strict';

  const INPUT_FRAME_SIZE = 12;
  const RUMBLE_FRAME_SIZE = 3;
  const RUMBLE_OPCODE = 0x01;

  function clamp(val, min, max) {
    return Math.max(min, Math.min(max, Math.round(val)));
  }

  // Pre-allocated ArrayBuffer to avoid GC pressure in high-frequency touch loops
  const buffer = new ArrayBuffer(INPUT_FRAME_SIZE);
  const view = new DataView(buffer);

  /**
   * Packs gamepad state into an ArrayBuffer of 12 bytes:
   * [0..1]  : uint16 (buttons bitmask, little-endian)
   * [2..3]  : int16  (left stick x, -32768..32767)
   * [4..5]  : int16  (left stick y, -32768..32767)
   * [6..7]  : int16  (right stick x, -32768..32767)
   * [8..9]  : int16  (right stick y, -32768..32767)
   * [10]    : uint8  (left trigger, 0..255)
   * [11]    : uint8  (right trigger, 0..255)
   */
  function packInputFrame(buttons, lx, ly, rx, ry, lt, rt) {
    view.setUint16(0, clamp(buttons, 0, 65535), true);
    view.setInt16(2, clamp(lx, -32768, 32767), true);
    view.setInt16(4, clamp(ly, -32768, 32767), true);
    view.setInt16(6, clamp(rx, -32768, 32767), true);
    view.setInt16(8, clamp(ry, -32768, 32767), true);
    view.setUint8(10, clamp(lt, 0, 255));
    view.setUint8(11, clamp(rt, 0, 255));
    return buffer;
  }

  /**
   * Unpacks a 3-byte downstream rumble frame from the server.
   * [0] : opcode (0x01)
   * [1] : leftMotor (0..255)
   * [2] : rightMotor (0..255)
   */
  function unpackRumbleFrame(arrayBuffer) {
    if (!arrayBuffer || arrayBuffer.byteLength !== RUMBLE_FRAME_SIZE) {
      return null;
    }
    const rView = new DataView(arrayBuffer);
    const opcode = rView.getUint8(0);
    if (opcode !== RUMBLE_OPCODE) {
      return null;
    }
    return {
      leftMotor: rView.getUint8(1),
      rightMotor: rView.getUint8(2)
    };
  }

  const Protocol = {
    INPUT_FRAME_SIZE,
    RUMBLE_FRAME_SIZE,
    RUMBLE_OPCODE,
    packInputFrame,
    unpackRumbleFrame
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = Protocol;
  } else {
    global.Protocol = Protocol;
  }
})(typeof window !== 'undefined' ? window : globalThis);
