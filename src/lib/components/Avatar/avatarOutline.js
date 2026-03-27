export const AVATAR_OUTLINE_LAYOUT = {
  showDesk: false,
  showFrame: false,
  viewBox: '50 40 128 138',
  figureClass: 'relative h-full w-full avatar-float',
};

export function getAvatarOutline() {
  return {
    headPath:
      'M62 79 L74 50 C76 45 82 45 86 50 L91 60 C96 57 104 57 109 60 L114 50 C118 45 124 45 126 50 L138 79 C142 86 144 94 144 101 C144 128 124 146 100 146 C76 146 56 128 56 101 C56 94 58 86 62 79 Z',
    bodyPath:
      'M72 111 C70 127 73 147 81 159 L121 160 C128 149 130 129 128 111 C123 98 112 92 100 92 C88 92 77 98 72 111 Z',
    tailPath:
      'M142 124 C154 106 171 108 171 127 C171 144 159 154 146 150 C153 145 158 137 158 128 C158 119 153 113 145 118 Z',
    leftPawPath:
      'M67 145 C59 154 59 166 67 172 C75 176 82 169 82 160 C82 151 77 145 67 145 Z',
    rightPawPath:
      'M133 145 C141 154 141 166 133 172 C125 176 118 169 118 160 C118 151 123 145 133 145 Z',
    leftEarInnerPath: 'M74 74 L80 57 L88 74',
    rightEarInnerPath: 'M113 74 L120 57 L126 73',
  };
}
