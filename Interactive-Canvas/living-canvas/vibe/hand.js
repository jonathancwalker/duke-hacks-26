// Hand tracking: camera + MediaPipe HandLandmarker -> fingertip positions in canvas pixels.
import { S, video, lin, say } from './state.js';

let hands = null, lastT = -1;

export async function startCamera() {
  if (hands) return;
  say('Waking the camera…');
  video.srcObject = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
  await video.play();
  const { FilesetResolver, HandLandmarker } = await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14');
  const vision = await FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm');
  hands = await HandLandmarker.createFromOptions(vision, { runningMode: 'VIDEO', numHands: 2,
    baseOptions: { modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task', delegate: 'GPU' } });
}

// The camera's middle 80% maps to the whole canvas, so reaching the edges is easy. Mirrored, like a mirror.
const toCanvas = lm => ({ x: lin(1 - lm.x, .1, .9) * S.W, y: lin(lm.y, .1, .9) * S.H });

// Call at the start of each trace.
export function resetTips() { lastT = -1; }

// Closed fist: the index fingertip (8) is curled in nearer the wrist (0) than its middle knuckle (6). Pointing keeps it out.
const fromWrist = (lm, j) => Math.hypot(lm[j].x - lm[0].x, lm[j].y - lm[0].y, lm[j].z - lm[0].z);
const isFist = lm => fromWrist(lm, 8) < fromWrist(lm, 6);

// [{ key, x, y, fist }] index fingertips, one per visible hand; null when there is no new camera frame (keep strokes open).
// fist: true lifts the pen (the cursor still moves, nothing is recorded).
export function readTips() {
  if (!(hands && video.readyState >= 2 && video.currentTime !== lastT)) return null;
  lastT = video.currentTime;
  const r = hands.detectForVideo(video, performance.now());
  return r.landmarks.map((lm, i) => ({ key: r.handednesses?.[i]?.[0]?.categoryName || 'h' + i, ...toCanvas(lm[8]), fist: isFist(lm) }));
}
