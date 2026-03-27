import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { AVATAR_OUTLINE_LAYOUT, getAvatarOutline } from './avatarOutline.js';

test('桌宠应保持纯轮廓布局，不再包含桌面或方框结构', () => {
  assert.equal(AVATAR_OUTLINE_LAYOUT.showDesk, false);
  assert.equal(AVATAR_OUTLINE_LAYOUT.showFrame, false);
  assert.equal(AVATAR_OUTLINE_LAYOUT.viewBox, '50 40 128 138');
  assert.equal(AVATAR_OUTLINE_LAYOUT.figureClass, 'relative h-full w-full avatar-float');
});

test('桌宠应保留分段轮廓结构，只移除额外方框', () => {
  const outline = getAvatarOutline();

  assert.match(outline.headPath, /L74 50/);
  assert.match(outline.bodyPath, /L121 160/);
  assert.equal(typeof outline.bellyPath, 'undefined');
  assert.match(outline.tailPath, /Z$/);
  assert.match(outline.leftPawPath, /59 154/);
  assert.match(outline.rightPawPath, /141 154/);
  assert.equal(outline.leftEarInnerPath, 'M74 74 L80 57 L88 74');
  assert.equal(outline.rightEarInnerPath, 'M113 74 L120 57 L126 73');
});

test('桌宠路径不应复用全局 outline 类名，避免 SVG 包围框泄漏', () => {
  const source = readFileSync(new URL('./AvatarCanvas.svelte', import.meta.url), 'utf8');
  const windowSource = readFileSync(new URL('../../../routes/avatar/AvatarWindow.svelte', import.meta.url), 'utf8');
  const engineSource = readFileSync(new URL('../../../../src-tauri/src/avatar_engine.rs', import.meta.url), 'utf8');

  assert.doesNotMatch(source, /class="outline"/);
  assert.match(source, /avatar-stroke/);
  assert.match(source, /avatar-fill/);
  assert.match(source, /tail-detail/);
  assert.match(source, /ear-detail/);
  assert.match(source, /cheek-detail/);
  assert.match(source, /avatar-shell/);
  assert.match(source, /--avatar-shell-opacity/);
  assert.match(source, /class="avatar-hit avatar-fill avatar-stroke tail-detail"/);
  assert.match(source, /pointer-events:\s*visiblePainted/);
  assert.doesNotMatch(source, /state\.contextLabel/);
  assert.doesNotMatch(source, /radial-gradient\(circle/);
  assert.doesNotMatch(source, /accent-line/);
  assert.doesNotMatch(source, /thought/);
  assert.doesNotMatch(windowSource, /aria-label="打开主界面"/);
  assert.match(windowSource, /on:avatarpointerdown=\{startAvatarDrag\}/);
  assert.match(windowSource, /on:avataractivate=\{openMainWindow\}/);
  assert.match(windowSource, /getAvatarStateBubble/);
  assert.match(windowSource, /showBubble\(stateBubble\)/);
  assert.match(engineSource, /const AVATAR_SCALE_DEFAULT: f64 = 0\.9;/);
  assert.match(engineSource, /const AVATAR_WINDOW_BASE_WIDTH: f64 = 152\.0;/);
  assert.match(engineSource, /const AVATAR_WINDOW_BASE_HEIGHT: f64 = 170\.0;/);
  assert.match(engineSource, /const AVATAR_WINDOW_MARGIN: f64 = 8\.0;/);
});

test('状态气泡应悬浮在猫头上方，采用紧凑气泡而不是横条', () => {
  const source = readFileSync(new URL('./AvatarPopover.svelte', import.meta.url), 'utf8');

  assert.match(source, /Array\.from\(bubble\.message\.replace\(\/\\s\+\/g, ''\)\)/);
  assert.match(source, /style="right: 4%; top: 2%;"/);
  assert.match(source, /min-width: clamp\(22px, 14vw, 30px\)/);
  assert.match(source, /font-size: clamp\(10px, 7vw, 13px\)/);
  assert.match(source, /flex flex-col items-center/);
  assert.match(source, /rotate-45 border-b border-r/);
  assert.doesNotMatch(source, /-translate-x-1\/2/);
});
