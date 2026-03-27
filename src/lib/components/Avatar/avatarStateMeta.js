const MODE_META = {
  idle: {
    eyePath: 'M78 90 Q84 86 90 90 M110 90 Q116 86 122 90',
    mouthPath: 'M96 111 Q100 116 104 111',
    leftPawClass: 'paw-rest',
    rightPawClass: 'paw-rest',
    shellClass: 'mode-idle',
    tailClass: 'tail-idle',
    earTone: 'rgba(248, 218, 214, 0.92)',
    cheekTone: 'rgba(251, 214, 218, 0.52)',
    cheekOpacity: 0.42,
  },
  working: {
    eyePath: 'M78 89 Q84 95 90 89 M110 89 Q116 95 122 89',
    mouthPath: 'M95 110 Q100 118 105 110',
    leftPawClass: 'paw-work-left',
    rightPawClass: 'paw-work-right',
    shellClass: 'mode-working',
    tailClass: 'tail-working',
    earTone: 'rgba(202, 228, 255, 0.92)',
    cheekTone: 'rgba(191, 219, 254, 0.52)',
    cheekOpacity: 0.44,
  },
  reading: {
    eyePath: 'M79 92 Q85 87 91 92 M109 92 Q115 87 121 92',
    mouthPath: 'M94 111 Q100 118 106 111',
    leftPawClass: 'paw-rest',
    rightPawClass: 'paw-rest',
    shellClass: 'mode-reading',
    tailClass: 'tail-reading',
    earTone: 'rgba(224, 226, 236, 0.9)',
    cheekTone: 'rgba(214, 220, 235, 0.26)',
    cheekOpacity: 0.16,
  },
  meeting: {
    eyePath: 'M79 90 Q84 93 89 90 M111 90 Q116 93 121 90',
    mouthPath: 'M97 111 Q100 113 103 111',
    leftPawClass: 'paw-rest',
    rightPawClass: 'paw-rest',
    shellClass: 'mode-meeting',
    tailClass: 'tail-meeting',
    earTone: 'rgba(209, 218, 242, 0.92)',
    cheekTone: 'rgba(196, 208, 255, 0.34)',
    cheekOpacity: 0.28,
  },
  music: {
    eyePath: 'M78 89 Q84 96 90 89 M110 89 Q116 96 122 89',
    mouthPath: 'M94 110 Q100 121 106 110',
    leftPawClass: 'paw-music-left',
    rightPawClass: 'paw-music-right',
    shellClass: 'mode-music',
    tailClass: 'tail-music',
    earTone: 'rgba(244, 200, 226, 0.94)',
    cheekTone: 'rgba(249, 168, 212, 0.54)',
    cheekOpacity: 0.52,
  },
  video: {
    eyePath: 'M80 88 Q85 96 90 88 M110 88 Q115 96 120 88',
    mouthPath: 'M98 111 Q100 114 102 111',
    leftPawClass: 'paw-rest',
    rightPawClass: 'paw-rest',
    shellClass: 'mode-video',
    tailClass: 'tail-video',
    earTone: 'rgba(211, 234, 250, 0.94)',
    cheekTone: 'rgba(186, 230, 253, 0.38)',
    cheekOpacity: 0.26,
  },
  generating: {
    eyePath: 'M79 89 Q84 95 90 89 M110 89 Q116 95 121 89',
    mouthPath: 'M96 110 Q100 117 104 110',
    leftPawClass: 'paw-think-left',
    rightPawClass: 'paw-think-right',
    shellClass: 'mode-generating',
    tailClass: 'tail-generating',
    earTone: 'rgba(207, 244, 227, 0.94)',
    cheekTone: 'rgba(167, 243, 208, 0.44)',
    cheekOpacity: 0.34,
  },
  slacking: {
    eyePath: 'M79 90 Q84 95 90 90 M110 89 Q115 94 121 89',
    mouthPath: 'M94 109 Q100 119 106 109',
    leftPawClass: 'paw-rest',
    rightPawClass: 'paw-rest',
    shellClass: 'mode-slacking',
    tailClass: 'tail-slacking',
    earTone: 'rgba(255, 222, 200, 0.94)',
    cheekTone: 'rgba(253, 186, 116, 0.48)',
    cheekOpacity: 0.46,
  },
};

const STATE_BUBBLES = {
  idle: { message: '待机中', tone: 'info', duration: 1600 },
  working: { message: '办公中', tone: 'info', duration: 1800 },
  reading: { message: '阅读中', tone: 'info', duration: 1800 },
  meeting: { message: '开会中', tone: 'info', duration: 1800 },
  music: { message: '听歌中', tone: 'info', duration: 1800 },
  video: { message: '视频中', tone: 'info', duration: 1800 },
  slacking: { message: '摸鱼中', tone: 'info', duration: 1800 },
};

export function getAvatarModeMeta(mode) {
  return MODE_META[mode] || MODE_META.idle;
}

export function getAvatarStateBubble(mode) {
  return STATE_BUBBLES[mode] || null;
}
