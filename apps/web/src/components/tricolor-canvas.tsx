"use client";

import { useEffect, useRef } from "react";

const vertexSource = `
  attribute vec2 position;
  void main() {
    gl_Position = vec4(position, 0.0, 1.0);
  }
`;

const fragmentSource = `
  precision highp float;
  uniform vec2 u_resolution;
  uniform float u_time;

  void main() {
    vec2 p = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / min(u_resolution.x, u_resolution.y);
    float t = u_time * 0.3;
    float angle = t * 0.45 + 0.3 * sin(t * 0.7);
    mat2 rotation = mat2(cos(angle), -sin(angle), sin(angle), cos(angle));
    vec2 q = rotation * p;
    float wave = q.x * 1.1
      + 0.45 * sin(q.y * 1.8 + t)
      + 0.22 * sin(q.y * 3.5 - t * 0.6)
      + 0.18 * cos(q.x * 2.3 + q.y * 1.4 + t);
    wave += 0.35 * sin(t * 0.55);
    float blend = smoothstep(-0.9, 0.9, wave);
    vec3 orange = vec3(1.0, 0.6, 0.2);
    vec3 white = vec3(1.0, 1.0, 1.0);
    vec3 green = vec3(0.075, 0.533, 0.031);
    vec3 color;
    if (blend < 0.5) {
      color = mix(orange, white, smoothstep(0.0, 0.5, blend));
    } else {
      color = mix(white, green, smoothstep(0.5, 1.0, blend));
    }
    float lighting = 0.96 + 0.04 * sin(q.x * 2.0 + q.y * 1.8 + t);
    color = mix(color, vec3(1.0), 1.0 - lighting);
    gl_FragColor = vec4(color, 1.0);
  }
`;

function createShader(
  gl: WebGLRenderingContext,
  type: number,
  source: string,
): WebGLShader {
  const shader = gl.createShader(type);
  if (!shader) throw new Error("Unable to create shader");
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS))
    throw new Error(gl.getShaderInfoLog(shader) ?? "Shader compile failed");
  return shader;
}

/**
 * Decorative tricolor gradient; CSS gradient fallback covers no-WebGL and
 * prefers-reduced-motion, since this is purely ambient and non-interactive.
 */
export function TricolorCanvas({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const gl = canvas.getContext("webgl");
    if (!gl) return;

    const program = gl.createProgram();
    if (!program) return;
    gl.attachShader(program, createShader(gl, gl.VERTEX_SHADER, vertexSource));
    gl.attachShader(
      program,
      createShader(gl, gl.FRAGMENT_SHADER, fragmentSource),
    );
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return;
    gl.useProgram(program);

    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
      gl.STATIC_DRAW,
    );
    const position = gl.getAttribLocation(program, "position");
    gl.enableVertexAttribArray(position);
    gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);

    const resolution = gl.getUniformLocation(program, "u_resolution");
    const time = gl.getUniformLocation(program, "u_time");

    let frame = 0;
    function resize() {
      if (!canvas) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(canvas.clientWidth * dpr);
      canvas.height = Math.round(canvas.clientHeight * dpr);
      gl?.viewport(0, 0, canvas.width, canvas.height);
    }
    window.addEventListener("resize", resize);
    resize();

    const start = performance.now();
    function animate() {
      const elapsed = (performance.now() - start) / 1000;
      gl?.uniform2f(resolution, canvas?.width ?? 1, canvas?.height ?? 1);
      gl?.uniform1f(time, elapsed);
      gl?.drawArrays(gl.TRIANGLES, 0, 6);
      frame = requestAnimationFrame(animate);
    }
    animate();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={`tricolor-canvas ${className ?? ""}`}
    />
  );
}
