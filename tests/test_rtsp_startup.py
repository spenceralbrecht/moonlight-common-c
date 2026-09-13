#!/usr/bin/env python3
"""Exercise the real native handshake against a bounded loopback-only synthetic peer.

All keys and responses are synthetic. No Sunshine, device, Keychain or credentials
are accessed. Every peer closes when its single fixture subprocess exits.
"""
import socket
import struct
import subprocess
import sys
import threading
import unittest
from contextlib import ExitStack
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

FIXTURE = sys.argv.pop(1)
KEY = bytes([0x11]) * 16


def read_exact(conn, size):
    data = b''
    while len(data) < size:
        part = conn.recv(size - len(data))
        if not part:
            raise EOFError('Synthetic peer received a truncated message')
        data += part
    return data


def iv(sequence, direction):
    return struct.pack('<I', sequence) + bytes(6) + direction


class StartupTest(unittest.TestCase):
    def run_handshake(self, sunshine=True, encrypted=True, fail=None, corrupt=False):
        commands, sequences, failures, announces = [], [], [], []
        stop = threading.Event()
        with socket.socket() as server, ExitStack() as sockets:
            # The native handshake starts audio NAT pings. Own every advertised
            # media port so those packets cannot reach another local service.
            ports = {}
            for stream in ['audio', 'video', 'control']:
                udp = sockets.enter_context(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
                udp.bind(('127.0.0.1', 0))
                ports[stream] = udp.getsockname()[1]
            server.bind(('127.0.0.1', 0))
            server.listen(1)
            server.settimeout(0.1)

            def serve():
                try:
                    while not stop.is_set():
                        try:
                            conn, _ = server.accept()
                        except socket.timeout:
                            continue
                        with conn:
                            conn.settimeout(2)
                            if encrypted:
                                header = read_exact(conn, 24)
                                length, enc_seq = struct.unpack('!II', header[:8])
                                assert length & 0x80000000
                                wire = read_exact(conn, length & 0x7fffffff)
                                data = AESGCM(KEY).decrypt(iv(enc_seq, b'CR'), wire + header[8:], None)
                            else:
                                data = b''
                                while b'\r\n\r\n' not in data:
                                    data += read_exact(conn, 1)
                                headers = data.decode().split('\r\n')
                                length = next((int(h.split(':',1)[1]) for h in headers
                                               if h.lower().startswith('content-length:')), 0)
                                data += read_exact(conn, length)
                            lines = data.decode().split('\r\n')
                            command = lines[0].split()[0]
                            sequence = int(next(h.split(':',1)[1] for h in lines if h.startswith('CSeq:')))
                            commands.append(command)
                            sequences.append(sequence)
                            body = b''
                            extra = ''
                            if command == 'DESCRIBE':
                                body = (b'v=0\r\na=rtpmap:96 H264/90000\r\n'
                                        b'a=x-ss-general.featureFlags:0\r\n'
                                        b'a=x-ss-general.encryptionSupported:7\r\n'
                                        b'a=x-ss-general.encryptionRequested:7\r\n')
                            elif command == 'SETUP':
                                port = ports['audio' if 'audio' in lines[0] else 'video' if 'video' in lines[0] else 'control']
                                extra = ('Session: DEADBEEFCAFE;timeout=90\r\n'
                                         f'Transport: server_port={port}\r\n')
                            elif command == 'ANNOUNCE':
                                announces.append(data.decode())
                            status = 403 if command == fail else 200
                            response = (f'RTSP/1.0 {status} Test\r\nCSeq: {sequence}\r\n{extra}'
                                        f'Content-length: {len(body)}\r\n\r\n').encode() + body
                            if encrypted:
                                sealed = AESGCM(KEY).encrypt(iv(enc_seq, b'HR'), response, None)
                                tag = sealed[-16:]
                                if corrupt:
                                    tag = bytes([tag[0] ^ 1]) + tag[1:]
                                response = struct.pack('!II', len(sealed)-16 | 0x80000000, enc_seq) + tag + sealed[:-16]
                            conn.sendall(response)
                except Exception as error:
                    failures.append(type(error).__name__)

            thread = threading.Thread(target=serve)
            thread.start()
            try:
                result = subprocess.run([FIXTURE, str(server.getsockname()[1]),
                                         str(int(sunshine)), str(int(encrypted))],
                                        capture_output=True, text=True, timeout=6)
            finally:
                stop.set()
                thread.join(3)
            self.assertFalse(thread.is_alive())
            if result.returncode == 0:
                self.assertIn(f"video_port={ports['video']} audio_port={ports['audio']} control_port={ports['control']}", result.stdout)
        self.assertEqual([], failures)
        self.assertEqual(list(range(1, len(sequences)+1)), sequences)
        return result, commands, announces

    def check_success(self, sunshine, encrypted):
        result, commands, announces = self.run_handshake(sunshine, encrypted)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        expected = ['DESCRIBE', 'SETUP', 'SETUP', 'SETUP', 'ANNOUNCE']
        self.assertEqual(expected if sunshine else ['OPTIONS'] + expected + ['PLAY'], commands)
        self.assertIn('encryption=7' if sunshine else 'encryption=0', result.stdout)
        if sunshine:
            self.assertIn('x-ss-general.encryptionEnabled:7', announces[0])

    def test_sunshine_encrypted_five_exchanges(self): self.check_success(True, True)
    def test_sunshine_plaintext_five_exchanges(self): self.check_success(True, False)
    def test_nvidia_retains_seven_exchanges(self): self.check_success(False, False)

    def test_describe_failure_cannot_reach_setup(self):
        result, commands, _ = self.run_handshake(fail='DESCRIBE')
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(['DESCRIBE'], commands)
        self.assertIn('handshake_result=403', result.stdout)

    def test_announce_failure_cannot_report_success(self):
        result, commands, _ = self.run_handshake(fail='ANNOUNCE')
        self.assertNotEqual(0, result.returncode)
        self.assertEqual('ANNOUNCE', commands[-1])
        self.assertIn('handshake_result=403', result.stdout)

    def test_tampered_ciphertext_fails_before_session_setup(self):
        result, commands, _ = self.run_handshake(corrupt=True)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(['DESCRIBE'], commands)


if __name__ == '__main__':
    unittest.main()
