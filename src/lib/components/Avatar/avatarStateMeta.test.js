import test from 'node:test';
import assert from 'node:assert/strict';

import {
  getAvatarModeMeta,
  getAvatarStateBubble,
} from './avatarStateMeta.js';

test('桌宠状态元信息应为不同模式提供细节变化', () => {
  const reading = getAvatarModeMeta('reading');
  const music = getAvatarModeMeta('music');
  const idle = getAvatarModeMeta('idle');

  assert.notEqual(reading.earTone, music.earTone);
  assert.notEqual(reading.cheekTone, music.cheekTone);
  assert.notEqual(reading.tailClass, music.tailClass);
  assert.equal(idle.tailClass, 'tail-idle');
});

test('桌宠状态切换气泡应返回短文案', () => {
  assert.deepEqual(getAvatarStateBubble('meeting'), {
    message: '开会中',
    tone: 'info',
    duration: 1800,
  });
  assert.deepEqual(getAvatarStateBubble('music'), {
    message: '听歌中',
    tone: 'info',
    duration: 1800,
  });
  assert.equal(getAvatarStateBubble('unknown'), null);
});
