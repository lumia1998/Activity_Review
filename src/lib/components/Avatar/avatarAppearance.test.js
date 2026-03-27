import test from 'node:test';
import assert from 'node:assert/strict';

import { getAvatarAppearance } from './avatarAppearance.js';

test('工作状态应返回蓝色系外观', () => {
  const appearance = getAvatarAppearance('working');

  assert.match(appearance.accent, /sky/);
  assert.match(appearance.desk, /sky|cyan/);
  assert.match(appearance.accent, /sky/);
});

test('未知状态应回退到 idle 外观', () => {
  const appearance = getAvatarAppearance('unknown');

  assert.match(appearance.fur, /stone|slate/);
  assert.match(appearance.accent, /slate/);
});
