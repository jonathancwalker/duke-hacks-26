// Charcoal silk: the slow satin surface behind Momento cards (station, setup start screen). Look only.
// startSilk(canvas) -> stop(). Draws at ~30 fps and lowest resolution so the GPU stays free for the painting.
const FS = `precision highp float; varying vec2 vUv; uniform vec2 uRes; uniform float uTime; uniform vec2 uMouse;
float hash(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p){ vec2 i=floor(p),f=fract(p); vec2 u=f*f*(3.0-2.0*f); return mix(mix(hash(i),hash(i+vec2(1.0,0.0)),u.x),mix(hash(i+vec2(0.0,1.0)),hash(i+vec2(1.0,1.0)),u.x),u.y); }
float fbm(vec2 p){ float v=0.0,a=0.5; for(int i=0;i<5;i++){ v+=a*noise(p); p=p*2.02+vec2(3.1,7.7); a*=0.5; } return v; }
float H(vec2 p){ float t=uTime*0.15; vec2 m=uMouse*vec2(uRes.x/uRes.y,1.0); float d=length(p-m);
  float h=sin(p.x*4.2+sin(p.y*2.3+t)*2.0+t)*0.5+sin(p.y*6.51+p.x*1.6-t*1.2)*0.2+fbm(p*1.5+t*0.2)*0.15; return h+0.12*exp(-d*d*6.0)*sin(d*10.0-uTime*1.2); }
void main(){ vec2 asp=vec2(uRes.x/uRes.y,1.0), p=vUv*asp; float e=1.5/uRes.y;
  float h=H(p),hx=H(p+vec2(e,0.0)),hy=H(p+vec2(0.0,e)); vec3 n=normalize(vec3((h-hx)/e*0.7,(h-hy)/e*0.7,1.0));
  float key=max(dot(n,normalize(vec3(-0.6,0.5,0.6))),0.0); vec2 lm=uMouse*asp-p; vec3 L=normalize(vec3(lm,0.5)); float fall=1.0/(1.0+dot(lm,lm)*4.0);
  float spec=pow(max(dot(reflect(-L,n),vec3(0.0,0.0,1.0)),0.0),10.0)*fall;
  vec3 c=vec3(0.07,0.066,0.062)+vec3(0.13,0.125,0.118)*key+vec3(0.30,0.28,0.26)*spec; gl_FragColor=vec4(c,1.0); }`;

export function startSilk(cv) {
  const gl = cv && cv.getContext('webgl', { antialias: false });
  if (!gl) return () => {};
  const sh = (t, s) => { const o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); return o; };
  const pr = gl.createProgram();
  gl.attachShader(pr, sh(gl.VERTEX_SHADER, 'attribute vec2 a; varying vec2 vUv; void main(){ vUv=a*0.5+0.5; gl_Position=vec4(a,0.0,1.0); }'));
  gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr); gl.useProgram(pr);
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const a = gl.getAttribLocation(pr, 'a'); gl.enableVertexAttribArray(a); gl.vertexAttribPointer(a, 2, gl.FLOAT, false, 0, 0);
  const uR = gl.getUniformLocation(pr, 'uRes'), uT = gl.getUniformLocation(pr, 'uTime'), uM = gl.getUniformLocation(pr, 'uMouse');
  const size = () => { const d = Math.min(devicePixelRatio || 1, 1); cv.width = Math.round(innerWidth * d); cv.height = Math.round(innerHeight * d); gl.viewport(0, 0, cv.width, cv.height); };
  addEventListener('resize', size); size();
  let mx = -1, my = -1, on = true, last = 0;
  const M = { x: .5, y: .55 };
  const onMove = e => { mx = e.clientX / innerWidth; my = 1 - e.clientY / innerHeight; };
  addEventListener('pointermove', onMove);
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  (function loop(now) {
    if (!on) return;
    requestAnimationFrame(loop);
    if (now - last < 33) return; last = now;
    const t = reduce ? 10 : now / 1000, tx = mx < 0 ? .5 + Math.sin(t * .25) * .25 : mx, ty = my < 0 ? .55 + Math.cos(t * .2) * .12 : my;
    M.x += (tx - M.x) * .12; M.y += (ty - M.y) * .12;
    gl.uniform2f(uR, cv.width, cv.height); gl.uniform1f(uT, t); gl.uniform2f(uM, M.x, M.y); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  })(0);
  return () => { on = false; removeEventListener('resize', size); removeEventListener('pointermove', onMove); };
}
