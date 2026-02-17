// ChartMarketObservation.jsx
import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  TimeScale,
  Tooltip,
  Legend,
} from 'chart.js';
import zoomPlugin from 'chartjs-plugin-zoom';
import {
  CandlestickController,
  CandlestickElement,
} from 'chartjs-chart-financial';

import 'chartjs-adapter-date-fns';
import { Chart } from 'react-chartjs-2';
import { AppContext } from '../../ContextApi/ContextApi';


// Registrar Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  TimeScale,
  Tooltip,
  Legend,
  CandlestickController,
  CandlestickElement,
  zoomPlugin
);

const TOOL = {
  NONE: 'none',
  PENCIL: 'pencil',
  LINE: 'line',
  TRIANGLE: 'triangle',
  RECTANGLE: 'rectangle',
};

const ChartMarketObservation = ({ symbol }) => {
  const { marketObservationComplete } = React.useContext(AppContext);
  const chartRef = React.useRef(null);
  const containerRef = React.useRef(null);
  const overlayRef = React.useRef(null);

  const [shapes, setShapes] = React.useState([]);
  const [tool, setTool] = React.useState(TOOL.NONE);
  const [color, setColor] = React.useState('#00ff88');
  const [lineWidth, setLineWidth] = React.useState(2);
  const [isDrawing, setIsDrawing] = React.useState(false);
  const [currentPath, setCurrentPath] = React.useState([]);
  const [tempShape, setTempShape] = React.useState(null);
  const [triangleClicks, setTriangleClicks] = React.useState([]);

  // ---- dados vindos do backend (marketObservationComplete) ----
  // normaliza, garante timestamp (number) e ordena por tempo asc
  const candleData = React.useMemo(() => {
    if (!marketObservationComplete) return [];
    const raw = Array.isArray(marketObservationComplete) ? marketObservationComplete : [marketObservationComplete];

    const parsed = raw.map((item) => {
      const o = item.Abertura ?? item.open ?? item.o ?? item.Open;
      const h = item.Maximo ?? item.high ?? item.h ?? item.High;
      const l = item.Minimo ?? item.low ?? item.l ?? item.Low;
      const c = item.Fechamento ?? item.close ?? item.c ?? item.Close;
      const t = item.Tempo ?? item.time ?? item.date ?? item.x;
      const v = item.Volume ?? item.volume ?? item.vol ?? 0;

      const date = t ? new Date(String(t)) : null;
      const ts = date && !isNaN(date.getTime()) ? date.getTime() : null;

      return {
        x: ts,
        o: Number(o),
        h: Number(h),
        l: Number(l),
        c: Number(c),
        v: Number(v) || 0,
      };
    }).filter(d => d.x !== null && !Number.isNaN(d.o) && !Number.isNaN(d.h) && !Number.isNaN(d.l) && !Number.isNaN(d.c));

    // ordenar por timestamp ascendente
    parsed.sort((a, b) => a.x - b.x);
    return parsed;
  }, [marketObservationComplete]);



  const data = React.useMemo(() => {
    const bg = candleData.map(d => d.c >= d.o ? 'rgba(0,255,8,0.7)' : 'rgba(255,0,0,0.7)');
    const bc = candleData.map(d => d.c >= d.o ? '#00ff08' : '#ff0000');

    return {
      datasets: [
        {
          label: symbol || 'Mercado',
          data: candleData,
          backgroundColor: bg,
          borderColor: bc,
          borderWidth: 1,
          type: 'candlestick',
        },
      ],
    };
  }, [candleData, symbol]);

  const options = React.useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      zoom: {
        pan: {
          enabled: true,
          mode: 'x',
        },
        zoom: {
          mode: 'x',
          drag: {
            enabled: true,
            modifierKey: 'shift', 
            borderColor: 'rgba(225,225,225,0.3)',
            borderWidth: 1,
            backgroundColor: 'rgba(225,225,225,0.1)',
          },
          wheel: {
            enabled: true, // ativa zoom com scroll
            speed: 0.2,
          },
          pinch: {
            enabled: true, // permite pinch
          }
        },
        // impede que o pan/zoom extrapolem os limites originais dos dados
        limits: {
          x: { min: 'original', max: 'original' },
          y: { min: 'original', max: 'original' },
        }
      },
      legend: {
        position: 'top',
        labels: { color: '#ddd' },
      },
      title: {
        display: true,
        text: 'Gráfico Candlestick de Mercado',
        color: '#eee',
        font: { size: 16 },
      },
      tooltip: {
        backgroundColor: 'rgba(20,20,30,0.95)',
        titleColor: '#fff',
        bodyColor: '#ddd',
        borderColor: '#444',
        borderWidth: 1,
        callbacks: {
          label: (context) => {
            const candle = context.raw;
            return [
              `Open:  ${candle.o.toFixed(2)}`,
              `High:  ${candle.h.toFixed(2)}`,
              `Low:   ${candle.l.toFixed(2)}`,
              `Close: ${candle.c.toFixed(2)}`,
            ];
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'month',
          displayFormats: { month: 'MMM' },
        },
        ticks: { color: '#aaa' },
        grid: { color: 'rgba(255,255,255,0.06)' },
      },
      y: {
        ticks: { color: '#aaa', callback: (v) => Number(v).toFixed(0) },
        grid: { color: 'rgba(255,255,255,0.06)' },
      }
    }
  }), []);

  // ---- helpers coordenadas ----
  const getOverlayRect = () => overlayRef.current?.getBoundingClientRect();
  const posClientToCanvas = (clientX, clientY) => {
    const rect = getOverlayRect();
    if (!rect || !overlayRef.current) return null;
    return {
      x: (clientX - rect.left) * (overlayRef.current.width / rect.width),
      y: (clientY - rect.top) * (overlayRef.current.height / rect.height),
    };
  };

  // ---- redimensiona overlay ----
  React.useEffect(() => {
    const resize = () => {
      const container = containerRef.current;
      const overlay = overlayRef.current;
      if (!container || !overlay) return;
      const rect = container.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      overlay.style.width = `${rect.width}px`;
      overlay.style.height = `${rect.height}px`;
      overlay.width = Math.round(rect.width * dpr);
      overlay.height = Math.round(rect.height * dpr);
      const ctx = overlay.getContext('2d');
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      redrawAll();
    };
    resize();
    const ro = new ResizeObserver(resize);
    if (containerRef.current) ro.observe(containerRef.current);
    window.addEventListener('resize', resize);
    return () => {
      ro.disconnect();
      window.removeEventListener('resize', resize);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shapes, tempShape]);

  // quando sem ferramenta, overlay não intercepta eventos (permite zoom/pan)
  React.useEffect(() => {
    const overlay = overlayRef.current;
    if (!overlay) return;
    overlay.style.pointerEvents = tool === TOOL.NONE ? 'none' : 'auto';
    const wheelHandler = (e) => {
      if (tool !== TOOL.NONE) e.preventDefault();
    };
    overlay.addEventListener('wheel', wheelHandler, { passive: false });
    return () => overlay.removeEventListener('wheel', wheelHandler);
  }, [tool, isDrawing]);

  // Shift+click: zoom centered at clicked time (keeps within data bounds)
  React.useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    const canvas = chart.canvas;

    const onClick = (ev) => {
      if (!ev.shiftKey) return; // apenas quando Shift estiver pressionado
      if (!candleData || candleData.length === 0) return;

      const rect = canvas.getBoundingClientRect();
      const pixelX = ev.clientX - rect.left;
      const xScale = chart.scales.x;
      const clickedVal = xScale.getValueForPixel(pixelX);

      const dataMin = candleData[0].x;
      const dataMax = candleData[candleData.length - 1].x;

      const currentMin = typeof xScale.min === 'number' ? xScale.min : dataMin;
      const currentMax = typeof xScale.max === 'number' ? xScale.max : dataMax;
      const currentRange = currentMax - currentMin;

      // reduz o range atual (zoom in) e centra no ponto clicado
      const zoomRatio = 0.25; // novo range = 25% do atual
      const halfNew = (currentRange * zoomRatio) / 2;
      let newMin = clickedVal - halfNew;
      let newMax = clickedVal + halfNew;

      // clamp aos limites dos dados
      if (dataMin != null) newMin = Math.max(newMin, dataMin);
      if (dataMax != null) newMax = Math.min(newMax, dataMax);

      chart.options.scales = chart.options.scales || {};
      chart.options.scales.x = chart.options.scales.x || {};
      chart.options.scales.x.min = newMin;
      chart.options.scales.x.max = newMax;
      chart.update();
    };

    canvas.addEventListener('click', onClick);
    return () => canvas.removeEventListener('click', onClick);
  }, [chartRef, candleData]);

  // ---- desenho ----
  const redrawAll = () => {
    const overlay = overlayRef.current;
    if (!overlay) return;
    const ctx = overlay.getContext('2d');
    ctx.clearRect(0, 0, overlay.width, overlay.height);

    shapes.forEach((s) => drawShape(ctx, s, false));
    if (tempShape) drawShape(ctx, tempShape, true);
  };

  const drawShape = (ctx, s, isPreview = false) => {
    if (!ctx || !s) return;
    ctx.save();
    ctx.lineWidth = s.lineWidth || 2;
    ctx.strokeStyle = s.color || '#00ff88';
    ctx.fillStyle = s.color || '#00ff88';
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    if (s.type === TOOL.PENCIL) {
      ctx.beginPath();
      s.points.forEach((p, i) => {
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      });
      ctx.stroke();
    } else if (s.type === TOOL.LINE) {
      const [p1, p2] = s.points;
      if (!p1 || !p2) { ctx.restore(); return; }
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    } else if (s.type === TOOL.TRIANGLE) {
      const pts = s.points;
      if (pts.length < 3) { ctx.restore(); return; }
      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      ctx.lineTo(pts[1].x, pts[1].y);
      ctx.lineTo(pts[2].x, pts[2].y);
      ctx.closePath();
      ctx.stroke();
      if (!isPreview) {
        ctx.globalAlpha = 0.06;
        ctx.fill();
        ctx.globalAlpha = 1;
      }
    } else if (s.type === TOOL.RECTANGLE) {
      const [p1, p2] = s.points;
      if (!p1 || !p2) { ctx.restore(); return; }
      const x = Math.min(p1.x, p2.x);
      const y = Math.min(p1.y, p2.y);
      const w = Math.abs(p2.x - p1.x);
      const h = Math.abs(p2.y - p1.y);
      ctx.beginPath();
      ctx.rect(x, y, w, h);
      ctx.stroke();
      if (!isPreview) {
        ctx.globalAlpha = 0.06;
        ctx.fillRect(x, y, w, h);
        ctx.globalAlpha = 1;
      }
    }

    ctx.restore();
  };

  // ---- eventos ponteiro ----
  React.useEffect(() => {
    const overlay = overlayRef.current;
    if (!overlay) return;

    const onPointerDown = (ev) => {
      if (tool === TOOL.NONE) return;
      overlay.setPointerCapture(ev.pointerId);
      const pos = posClientToCanvas(ev.clientX, ev.clientY);
      if (!pos) return;

      setIsDrawing(true);

      if (tool === TOOL.PENCIL) {
        setCurrentPath([pos]);
        setTempShape({ type: TOOL.PENCIL, points: [pos], color, lineWidth });
      } else if (tool === TOOL.LINE) {
        setTempShape({ type: TOOL.LINE, points: [pos, pos], color, lineWidth });
      } else if (tool === TOOL.RECTANGLE) {
        setTempShape({ type: TOOL.RECTANGLE, points: [pos, pos], color, lineWidth });
      } else if (tool === TOOL.TRIANGLE) {
        setTriangleClicks((prev) => {
          const nxt = [...prev, pos];
          if (nxt.length === 3) {
            const shape = { type: TOOL.TRIANGLE, points: nxt, color, lineWidth };
            setShapes((s) => [...s, shape]);
            setTempShape(null);
            setTriangleClicks([]);
          } else {
            setTempShape({ type: TOOL.TRIANGLE, points: nxt, color, lineWidth });
          }
          return nxt.length === 3 ? [] : nxt;
        });
        setIsDrawing(false);
      }
      redrawAll();
    };

    const onPointerMove = (ev) => {
      if (!isDrawing) return;
      const pos = posClientToCanvas(ev.clientX, ev.clientY);
      if (!pos) return;

      if (tool === TOOL.PENCIL) {
        setCurrentPath((prev) => {
          const next = [...prev, pos];
          setTempShape({ type: TOOL.PENCIL, points: next, color, lineWidth });
          redrawAll();
          return next;
        });
      } else if (tool === TOOL.LINE) {
        setTempShape((prev) => {
          if (!prev) return prev;
          const next = { ...prev, points: [prev.points[0], pos] };
          redrawAll();
          return next;
        });
      } else if (tool === TOOL.RECTANGLE) {
        setTempShape((prev) => {
          if (!prev) return prev;
          const next = { ...prev, points: [prev.points[0], pos] };
          redrawAll();
          return next;
        });
      }
    };

    const onPointerUp = (ev) => {
      overlay.releasePointerCapture?.(ev.pointerId);
      if (!isDrawing) return;
      setIsDrawing(false);
      const pos = posClientToCanvas(ev.clientX, ev.clientY);
      if (!pos) {
        setTempShape(null);
        return;
      }

      if (tool === TOOL.PENCIL) {
        setShapes((s) => [...s, { type: TOOL.PENCIL, points: currentPath.concat([pos]), color, lineWidth }]);
        setCurrentPath([]);
        setTempShape(null);
      } else if (tool === TOOL.LINE) {
        setShapes((s) => [...s, { type: TOOL.LINE, points: [tempShape.points[0], pos], color, lineWidth }]);
        setTempShape(null);
      } else if (tool === TOOL.RECTANGLE) {
        setShapes((s) => [...s, { type: TOOL.RECTANGLE, points: [tempShape.points[0], pos], color, lineWidth }]);
        setTempShape(null);
      }
      redrawAll();
    };

    overlay.addEventListener('pointerdown', onPointerDown);
    overlay.addEventListener('pointermove', onPointerMove);
    overlay.addEventListener('pointerup', onPointerUp);
    overlay.addEventListener('pointercancel', onPointerUp);

    return () => {
      overlay.removeEventListener('pointerdown', onPointerDown);
      overlay.removeEventListener('pointermove', onPointerMove);
      overlay.removeEventListener('pointerup', onPointerUp);
      overlay.removeEventListener('pointercancel', onPointerUp);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tool, isDrawing, currentPath, tempShape, color, lineWidth, triangleClicks]);

  React.useEffect(() => {
    redrawAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shapes, tempShape]);

  // ---- utilitários UI ----
  const undo = () => setShapes((s) => s.slice(0, -1));
  const clearAll = () => {
    setShapes([]);
    setTempShape(null);
    setTriangleClicks([]);
  };



  return (
    <div className="chart-wrapper" ref={containerRef} style={{ position: 'relative', width: '90vw', height: '85vh', margin: '20px auto' }}>
      <div className="draw-toolbar" style={{ position: 'absolute', top: 10, left: 12, zIndex: 20, display: 'flex', gap: 8, alignItems: 'center' }}>
        <button onClick={() => setTool(TOOL.PENCIL)} className={tool === TOOL.PENCIL ? 'active' : ''}>✏️ Pincel</button>
        <button onClick={() => setTool(TOOL.LINE)} className={tool === TOOL.LINE ? 'active' : ''}>📏 Linha</button>
        <button onClick={() => setTool(TOOL.RECTANGLE)} className={tool === TOOL.RECTANGLE ? 'active' : ''}>▭ Retângulo</button>
        <button onClick={() => setTool(TOOL.TRIANGLE)} className={tool === TOOL.TRIANGLE ? 'active' : ''}>🔺 Triângulo</button>
        <button onClick={() => setTool(TOOL.NONE)} className={tool === TOOL.NONE ? 'active' : ''}>✖ Sem desenho</button>

        <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          Cor:
          <input type="color" value={color} onChange={(e) => setColor(e.target.value)} />
        </label>

        <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          Espessura:
          <input type="range" min="1" max="8" value={lineWidth} onChange={(e) => setLineWidth(Number(e.target.value))} />
        </label>

        <button className='active-toolbar' onClick={undo}><span className='pi pi-refresh'></span> Desfazer</button>
        <button className='active-toolbar' onClick={clearAll}><span className='pi pi-trash'></span> Limpar</button>
        <button className='active-toolbar' onClick={() => {
          const overlay = overlayRef.current;
          const chart = chartRef.current;
          if (!overlay || !chart) return;
          try {
            const tmp = document.createElement('canvas');
            tmp.width = overlay.width;
            tmp.height = overlay.height;
            const ctx = tmp.getContext('2d');
            const chartCanvas = chart.canvas || (chart.chart && chart.chart.canvas);
            if (chartCanvas instanceof HTMLCanvasElement) {
              ctx.drawImage(chartCanvas, 0, 0, tmp.width, tmp.height);
              ctx.drawImage(overlay, 0, 0, tmp.width, tmp.height);
              const url = tmp.toDataURL('image/png');
              const a = document.createElement('a');
              a.href = url;
              a.download = `${symbol || 'chart'}-with-annotations.png`;
              a.click();
            } else {
              const img = new Image();
              img.src = chart.toBase64Image?.() || chartCanvas?.toDataURL?.();
              img.onload = () => {
                ctx.drawImage(img, 0, 0, tmp.width, tmp.height);
                ctx.drawImage(overlay, 0, 0, tmp.width, tmp.height);
                const url = tmp.toDataURL('image/png');
                const a = document.createElement('a');
                a.href = url;
                a.download = `${symbol || 'chart'}-with-annotations.png`;
                a.click();
              };
            }
          } catch (err) {
            console.error('Export failed', err);
          }
        }}>💾 Salvar</button>
      </div>

      <button
        className='btn-zoom'
        style={{ position: 'absolute', top: 10, right: 12, zIndex: 20 }}
        onClick={() => {
          const chart = chartRef.current;
          if (!chart) return;

          // 1) reset plugin-managed zoom/pan
          if (chart.resetZoom) chart.resetZoom();

          // 2) clear any manual min/max set on scales (ex: Shift+click handler)
          if (chart.options && chart.options.scales && chart.options.scales.x) {
            delete chart.options.scales.x.min;
            delete chart.options.scales.x.max;
          }
          if (chart.options && chart.options.scales && chart.options.scales.y) {
            delete chart.options.scales.y.min;
            delete chart.options.scales.y.max;
          }

          // apply changes
          try { chart.update(); } catch (e) { /* ignore */ }
        }}
      >
        Reset Zoom
      </button>

      <div style={{width: '100%', height: '100%', position: 'relative' }}>
        <Chart ref={chartRef} type="candlestick" data={data} options={options} />
        <canvas
          ref={overlayRef}
          className="chart-overlay-canvas"
          style={{ position: 'absolute', left: 0, top: 0, zIndex: 15, touchAction: 'none' }}
        />
      </div>
    </div>
  );
};

export default ChartMarketObservation;
