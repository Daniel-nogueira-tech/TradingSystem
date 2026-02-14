import React from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    TimeScale,
    Tooltip,
    Legend,
} from 'chart.js';

import {
    CandlestickController,
    CandlestickElement,
} from 'chartjs-chart-financial';

import 'chartjs-adapter-date-fns';  // ← obrigatório para time scale com date-fns
import { Chart } from 'react-chartjs-2';
import { AppContext } from '../../ContextApi/ContextApi';

// Registra tudo
ChartJS.register(
    CategoryScale,
    LinearScale,
    TimeScale,
    Tooltip,
    Legend,
    CandlestickController,
    CandlestickElement
);

const ChartMarketObservation = () => {
    const { marketObservation } = React.useContext(AppContext);

    console.log(marketObservation);

// 🔥 Simulação de 120 períodos (ex: 120 candles)
const generateValores = (periods = 120) => {
  const valores = [];
  let tendencia = 1;        // 1 = alta, -1 = baixa
  let forcaTendencia = 50;  // intensidade média
  let volatilidade = 200;   // amplitude média

  for (let i = 0; i < periods; i++) {

    // 🔁 Troca de tendência ocasional
    if (Math.random() < 0.08) {
      tendencia *= -1;
      forcaTendencia = 30 + Math.random() * 120;
    }

    // 🎲 Movimento base
    let movimento =
      tendencia * forcaTendencia +
      (Math.random() - 0.5) * volatilidade;

    // ⚡ Choque ocasional tipo notícia inesperada
    if (Math.random() < 0.8) {
      movimento += (Math.random() - 0.5) * 1500;
    }

    valores.push(Math.round(movimento));
  }

  return valores;
};

const valores = generateValores(120);



    // Dados simulados (valores de mudança)


    // Datas como objetos Date (pode ser qualquer data real ou fictícia)
    const baseDate = new Date(2025, 0, 1); // 1º de janeiro de 2025 como base

    const generateCandleData = () => {
        return valores.map((valor, index) => {
            // Cada candle avança 1 mês
            const date = new Date(baseDate);
            date.setMonth(baseDate.getMonth() + index);

            const basePrice = 2000 + index * 50;
            const change = valor;

            const open = basePrice + (Math.random() * 100 - 50);
            const close = open + change;

            const high = Math.max(open, close) + Math.abs(change) * 0.3 + Math.random() * 50;
            const low = Math.min(open, close) - Math.abs(change) * 0.3 - Math.random() * 50;

            return {
                x: date.getTime(),  // ← timestamp em milissegundos (número!)
                o: open,
                h: high,
                l: low,
                c: close,
            };
        });
    };

    const candleData = generateCandleData();

    const data = {
        datasets: [
            {
                label: 'Mercado',
                data: candleData,
                backgroundColor: candleData.map((candle) =>
                    candle.c >= candle.o
                        ? 'rgba(0, 255, 8, 0.7)'   // verde
                        : 'rgba(255, 0, 0, 0.7)'   // vermelho
                ),
                borderColor: candleData.map((candle) =>
                    candle.c >= candle.o ? '#00ff08' : '#ff0000'
                ),
                borderWidth: 1,
                type: 'candlestick',
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
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
                backgroundColor: 'rgba(20, 20, 30, 0.9)',
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
                    },
                },
            },
        },
        scales: {
            x: {
                type: 'time',                    // ← essencial!
                time: {
                    unit: 'month',                 // mostra por mês
                    displayFormats: {
                        month: 'MMM',                // Jan, Fev, Mar...
                    },
                },
                ticks: { color: '#aaa' },
                grid: { color: 'rgba(255,255,255,0.08)' },
            },
            y: {
                ticks: {
                    color: '#aaa',
                    callback: (value) => value.toFixed(0),
                },
                grid: { color: 'rgba(255,255,255,0.08)' },
            },
        },
    };

    return (
        <div
            style={{
                width: '90vw',
                height: '85vh',
                margin: '20px auto',
                padding: '15px',
                backgroundColor: 'rgba(0,0,0,0.25)',
                borderRadius: '10px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
            }}
        >
            <Chart type="candlestick" data={data} options={options} />
        </div>
    );
};

export default ChartMarketObservation;