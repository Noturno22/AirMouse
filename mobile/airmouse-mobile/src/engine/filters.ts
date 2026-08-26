// One Euro Filter - Port from Python AirMouse
// Reference: https://hal.inria.fr/hal-00670496/document

class LowPass {
  private y: number | null = null;

  apply(x: number, alpha: number): number {
    this.y = this.y === null ? x : alpha * x + (1.0 - alpha) * this.y;
    return this.y;
  }

  reset(): void {
    this.y = null;
  }
}

export class OneEuroFilter {
  private minCutoff: number;
  private beta: number;
  private dCutoff: number;
  private velocity: number = 0.0;
  private xLpf = new LowPass();
  private dxLpf = new LowPass();
  private xPrev: number | null = null;
  private tPrev: number | null = null;

  constructor(minCutoff: number = 1.4, beta: number = 0.028, dCutoff: number = 1.0) {
    this.minCutoff = minCutoff;
    this.beta = beta;
    this.dCutoff = dCutoff;
  }

  reset(): void {
    this.xLpf.reset();
    this.dxLpf.reset();
    this.xPrev = null;
    this.tPrev = null;
    this.velocity = 0.0;
  }

  private static alpha(cutoff: number, dt: number): number {
    const tau = 1.0 / (2.0 * Math.PI * cutoff);
    return 1.0 / (1.0 + tau / dt);
  }

  filter(x: number, t?: number): number {
    const now = t ?? performance.now() / 1000;
    let dt: number;
    if (this.tPrev === null) {
      dt = 1.0 / 30.0;
    } else {
      dt = Math.max(now - this.tPrev, 1e-6);
    }
    this.tPrev = now;

    const dx = this.xPrev === null ? 0.0 : (x - this.xPrev) / dt;
    this.xPrev = x;
    const edx = this.dxLpf.apply(dx, OneEuroFilter.alpha(this.dCutoff, dt));
    this.velocity = edx;
    const cutoff = this.minCutoff + this.beta * Math.abs(edx);
    return this.xLpf.apply(x, OneEuroFilter.alpha(cutoff, dt));
  }

  getVelocity(): number {
    return this.velocity;
  }
}

export class FilterPair2D {
  private fx: OneEuroFilter;
  private fy: OneEuroFilter;
  vx: number = 0.0;
  vy: number = 0.0;

  constructor(minCutoff: number = 1.4, beta: number = 0.028) {
    this.fx = new OneEuroFilter(minCutoff, beta);
    this.fy = new OneEuroFilter(minCutoff, beta);
  }

  get velocity(): number {
    return Math.hypot(this.vx, this.vy);
  }

  setParams(minCutoff: number, beta: number): void {
    this.fx['minCutoff'] = minCutoff;
    this.fx['beta'] = beta;
    this.fy['minCutoff'] = minCutoff;
    this.fy['beta'] = beta;
  }

  reset(): void {
    this.fx.reset();
    this.fy.reset();
    this.vx = 0.0;
    this.vy = 0.0;
  }

  filter(x: number, y: number): [number, number] {
    const rx = this.fx.filter(x);
    const ry = this.fy.filter(y);
    this.vx = this.fx.getVelocity();
    this.vy = this.fy.getVelocity();
    return [rx, ry];
  }
}

export class AccelCurve {
  minGain: number;
  maxGain: number;
  refSpeed: number;
  expo: number;

  constructor(minGain: number = 1.2, maxGain: number = 3.0, refSpeed: number = 1400.0, expo: number = 1.7) {
    this.minGain = minGain;
    this.maxGain = maxGain;
    this.refSpeed = Math.max(refSpeed, 1e-6);
    this.expo = expo;
  }

  apply(vx: number, vy: number): number {
    const t = Math.min(Math.hypot(vx, vy) / this.refSpeed, 1.0);
    let s: number;
    if (this.expo > 0.0) {
      s = Math.pow(t, this.expo);
    } else {
      s = t * t * (3.0 - 2.0 * t);
    }
    return this.minGain + (this.maxGain - this.minGain) * s;
  }
}
