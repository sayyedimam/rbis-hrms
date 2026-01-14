import { Component, ElementRef, HostListener, OnInit, ViewChild, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';

interface Particle {
  x: number;
  y: number;
  size: number;
  baseX: number;
  baseY: number;
  density: number;
  color: string;
  text: string;
}

@Component({
  selector: 'app-particle-bg',
  standalone: true,
  imports: [CommonModule],
  template: `
    <canvas #canvas class="particle-canvas"></canvas>
  `,
  styles: `
    .particle-canvas {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: -1;
      background: #fdfdff;
    }
  `
})
export class ParticleBgComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('canvas') canvasRef!: ElementRef<HTMLCanvasElement>;
  private ctx!: CanvasRenderingContext2D;
  private particles: Particle[] = [];
  private mouse = {
    x: undefined as number | undefined,
    y: undefined as number | undefined,
    radius: 150
  };
  private animationId!: number;

  private techStack = ['Angular', '.NET', 'RBIS','Python', 'AI', 'ML', 'SQL', 'Cloud', 'ERP'];
  private colors = [
    'rgba(86, 77, 253, 0.21)',   // Soft Indigo
    'rgba(59, 131, 246, 0.35)',   // Soft Blue
    'rgba(16, 185, 129, 0.15)',   // Soft Emerald
    'rgba(139, 92, 246, 0.12)',   // Soft Purple
    'rgba(148, 163, 184, 0.2)'    // Soft Slate
  ];

  ngOnInit(): void {}

  ngAfterViewInit(): void {
    const canvas = this.canvasRef.nativeElement;
    this.ctx = canvas.getContext('2d')!;
    this.resizeCanvas();
    this.initParticles();
    this.animate();
  }

  ngOnDestroy(): void {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
  }

  @HostListener('window:resize')
  onResize(): void {
    this.resizeCanvas();
    this.initParticles();
  }

  @HostListener('window:mousemove', ['$event'])
  onMouseMove(event: MouseEvent): void {
    this.mouse.x = event.x;
    this.mouse.y = event.y;
  }

  private resizeCanvas(): void {
    const canvas = this.canvasRef.nativeElement;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  private initParticles(): void {
    this.particles = [];
    // Much fewer particles for a truly minimalist, professional feel
    const numberOfParticles = Math.floor((window.innerWidth * window.innerHeight) / 45000);
    
    // Shuffle tech stack to get diverse initial labels
    const shuffledTech = [...this.techStack].sort(() => Math.random() - 0.5);

    for (let i = 0; i < numberOfParticles; i++) {
      let x = Math.random() * window.innerWidth;
      let y = Math.random() * window.innerHeight;
      const size = Math.random() * 40 + 40; // 40 to 80px
      
      // Simple check to avoid initial overlapping
      let overlapping = false;
      for (let j = 0; j < this.particles.length; j++) {
        const dx = x - this.particles[j].x;
        const dy = y - this.particles[j].y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        if (distance < size + this.particles[j].size + 50) {
          overlapping = true;
          break;
        }
      }
      
      if (overlapping && i > 0) {
          // If overlaps, try again once or just scatter far
          x = Math.random() * window.innerWidth;
          y = Math.random() * window.innerHeight;
      }

      this.particles.push({
        x: x,
        y: y,
        size: size,
        baseX: x,
        baseY: y,
        density: (Math.random() * 1.5) + 0.5,
        color: this.colors[Math.floor(Math.random() * this.colors.length)],
        text: shuffledTech[i % shuffledTech.length]
      });
    }
  }

  private animate(): void {
    this.animationId = requestAnimationFrame(this.animate.bind(this));
    this.ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    
    // Smooth background gradient - extra light for minimalism
    const gradient = this.ctx.createLinearGradient(0, 0, window.innerWidth, window.innerHeight);
    gradient.addColorStop(0, '#ffffff');
    gradient.addColorStop(1, '#ffffff'); // Pure white for maximum brightness
    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(0, 0, window.innerWidth, window.innerHeight);

    // Update and draw
    for (let i = 0; i < this.particles.length; i++) {
        this.updateParticle(this.particles[i], i);
        this.drawParticle(this.particles[i]);
    }
  }

  private updateParticle(p: Particle, index: number): void {
    // Very gentle floating movement
    p.baseX += Math.sin(Date.now() / 4000 + p.density) * 0.1;
    p.baseY += Math.cos(Date.now() / 4000 + p.density) * 0.1;
    
    // Bubble-to-Bubble soft repulsion to prevent overlapping
    for (let j = 0; j < this.particles.length; j++) {
        if (index === j) continue;
        const other = this.particles[j];
        const dx = p.x - other.x;
        const dy = p.y - other.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const minDistance = p.size + other.size + 40;
        
        if (distance < minDistance) {
            const force = (minDistance - distance) / minDistance;
            p.x += (dx / distance) * force * 2;
            p.y += (dy / distance) * force * 2;
        }
    }

    if (this.mouse.x !== undefined && this.mouse.y !== undefined) {
      const dx = this.mouse.x - p.x;
      const dy = this.mouse.y - p.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance < 250) {
        const force = (250 - distance) / 250;
        const directionX = (dx / distance) * force * 15;
        const directionY = (dy / distance) * force * 15;
        p.x -= directionX * 0.04;
        p.y -= directionY * 0.04;
      }
    }
    
    // Smoothly return to base position
    p.x += (p.baseX - p.x) * 0.01;
    p.y += (p.baseY - p.y) * 0.01;
  }

  private drawParticle(p: Particle): void {
    this.ctx.save();
    
    // Draw bubble
    this.ctx.beginPath();
    this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    this.ctx.shadowBlur = 30;
    this.ctx.shadowColor = p.color;
    this.ctx.fillStyle = p.color;
    this.ctx.fill();

    // Draw tech stack label
    this.ctx.shadowBlur = 0; // Disable shadow for text
    this.ctx.font = `600 ${p.size * 0.3}px 'Inter', sans-serif`;
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    // Darker version of bubble color for text but still very soft
    this.ctx.fillStyle = p.color.replace('0.15', '0.5').replace('0.12', '0.5').replace('0.2', '0.5');
    this.ctx.fillText(p.text, p.x, p.y);
    
    this.ctx.restore();
  }

  private connectParticles(): void {
    // Not used for this professional aesthetic
  }
}
