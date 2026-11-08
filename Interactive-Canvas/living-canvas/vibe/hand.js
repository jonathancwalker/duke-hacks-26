// Hand tracking: camera + MediaPipe HandLandmarker -> fingertip positions in canvas pixels.
import { S, video, lin, say } from './state.js';
import { pickHand, boxOf } from './pick.js';

let hands = null, lastT = -1, lock = null;

export async function startCamera() {
  if (hands) return;
  say('Waking the camera…');
  video.srcObject = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
  await video.play();
  const { FilesetResolver, HandLandmarker } = await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14');
  const vision = await FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm');
  hands = await HandLandmarker.createFromOptions(vision, { runningMode: 'VIDEO', numHands: 4,   // 4: a bystander's two hands can't crowd out the visitor's
    baseOptions: { modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task', delegate: 'GPU' } });
}

// The camera's middle 80% maps to the whole canvas, so reaching the edges is easy. Mirrored, like a mirror.
const toCanvas = lm => ({ x: lin(1 - lm.x, .1, .9) * S.W, y: lin(lm.y, .1, .9) * S.H });

// Call at the start of each trace (where the 3, 2, 1 countdown ends): the next frame locks onto the largest hand.
export function resetTips() { lastT = -1; lock = null; }

// Closed fist: the index fingertip (8) is curled in nearer the wrist (0) than its middle knuckle (6). Pointing keeps it out.
const fromWrist = (lm, j) => Math.hypot(lm[j].x - lm[0].x, lm[j].y - lm[0].y, lm[j].z - lm[0].z);
const isFist = lm => fromWrist(lm, 8) < fromWrist(lm, 6);

// [{ key, x, y, fist }]: the locked visitor's index fingertip, or [] while their hand is out of sight; other people's
// hands never draw (#22, pick.js). null when there is no new camera frame (keep strokes open).
// fist: true lifts the pen (the cursor still moves, nothing is recorded).
export function readTips() {
  if (!(hands && video.readyState >= 2 && video.currentTime !== lastT)) return null;
  lastT = video.currentTime;
  const now = performance.now(), r = hands.detectForVideo(video, now);
  const pick = pickHand(r.landmarks.map(lm => ({ ...boxOf(lm, 0), lm })), lock, now / 1000);   // 0: wrist
  lock = pick.lock;
  return pick.hand ? [{ key: 'visitor', ...toCanvas(pick.hand.lm[8]), fist: isFist(pick.hand.lm) }] : [];
}
