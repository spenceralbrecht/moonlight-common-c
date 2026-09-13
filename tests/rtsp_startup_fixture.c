// Synthetic RTSP peer driver. No capture, media rendering, input or real host.
#include "Limelight-internal.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char** argv) {
    if (argc != 4) return 2;
    if (initializePlatform() != 0) return 3;
    LiInitializeStreamConfiguration(&StreamConfig);
    StreamConfig.width = 1280;
    StreamConfig.height = 800;
    StreamConfig.fps = 30;
    StreamConfig.bitrate = 2000;
    StreamConfig.packetSize = 640;
    StreamConfig.streamingRemotely = STREAM_CFG_REMOTE;
    StreamConfig.audioConfiguration = AUDIO_CONFIGURATION_STEREO;
    StreamConfig.supportedVideoFormats = VIDEO_FORMAT_H264;
    StreamConfig.encryptionFlags = ENCFLG_ALL;
    StreamConfig.enableAudio = true;
    memset(StreamConfig.remoteInputAesKey, 0x11, sizeof(StreamConfig.remoteInputAesKey));
    AppVersionQuad[0] = 7;
    AppVersionQuad[1] = 1;
    AppVersionQuad[2] = 431;
    AppVersionQuad[3] = atoi(argv[2]) ? -1 : 0;
    RemoteAddr.ss_family = LocalAddr.ss_family = AF_INET;
    ((struct sockaddr_in*)&RemoteAddr)->sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    ((struct sockaddr_in*)&LocalAddr)->sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    RemoteAddrString = "127.0.0.1";
    AddrLen = sizeof(struct sockaddr_in);
    RtspPortNumber = (unsigned short)atoi(argv[1]);
    char url[96];
    snprintf(url, sizeof(url), "%s://127.0.0.1:%u", atoi(argv[3]) ? "rtspenc" : "rtsp", RtspPortNumber);
    SERVER_INFORMATION server;
    LiInitializeServerInformation(&server);
    server.address = "127.0.0.1";
    server.serverInfoAppVersion = "7.1.431.0";
    server.rtspSessionUrl = url;
    if (initializeAudioStream() != 0) return 4;
    int result = performRtspHandshake(&server);
    printf("handshake_result=%d video_port=%u audio_port=%u control_port=%u encryption=%u\n",
        result, VideoPortNumber, AudioPortNumber, ControlPortNumber, EncryptionFeaturesEnabled);
    destroyAudioStream();
    cleanupPlatform();
    return result == 0 ? 0 : 1;
}
