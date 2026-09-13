# RTSP startup regression harness

Build the real native library and fixture with CMake, then run the Python suite
(Python requires `cryptography`; the native library requires OpenSSL):

```sh
cmake -S . -B /tmp/moonlight-rtsp-test -DCMAKE_BUILD_TYPE=Debug -DBUILD_RTSP_STARTUP_TEST=ON -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build /tmp/moonlight-rtsp-test -j2
python3 tests/test_rtsp_startup.py /tmp/moonlight-rtsp-test/rtsp-startup-fixture
```

The fixture target is disabled by default. This harness was validated on macOS.
The suite runs bounded, loopback-only synthetic peers; it never launches a real host
or reads device credentials. Encrypted tests use a public synthetic key. It verifies
Sunshine's five-exchange path, NVIDIA's seven-exchange path, negotiated ports, encryption,
failure propagation, and rejection of altered authentication tags.

## Fixture resource ownership

`performRtspHandshake()` starts an audio NAT-ping thread when audio SETUP completes,
even without starting media playback. Treating this as a pure control-only operation
can leak a thread and send packets to a real local service if fixture responses use
well-known media ports. The fixture must initialize/destroy the audio subsystem, and
the peer must own dynamically allocated loopback UDP sockets for every advertised port.
Keep those sockets open until the fixture exits, including failure paths. Acceptance:
native Debug cleanup asserts zero active resources, every peer thread joins, and parsed
ports match the fixture's owned sockets. Never replace these with Sunshine's fixed ports.
