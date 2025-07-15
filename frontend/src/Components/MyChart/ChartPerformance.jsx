import React from 'react';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Registrar os componentes no Chart.js
ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend,
  Filler // esse é essencial para o fill funcionar
);

const ChartPerformance = ({ selectedDateStart,selectedDateEnd }) => {
  const valores = [300, 200, -280, 600, -1000, 2000, 1000, 2000, 2200, 2000, 1000, 1050];

  const data = {
    labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
    datasets: [
      {
        label: 'Desempenho',
        data: valores,
        fill: true, // Ativa o preenchimento abaixo da linha
        backgroundColor: (context) => {
          const { chart } = context;
          const { ctx, chartArea, scales } = chart;
          if (!chartArea) return null;

          const { y } = scales; // Escala Y
          const zeroY = y.getPixelForValue(0); // Posição do Y = 0 no canvas
          const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);

          // Normaliza a posição do zero em relação à área do gráfico
          let zeroRatio = (zeroY - chartArea.top) / (chartArea.bottom - chartArea.top);
          // Garante que zeroRatio fique no intervalo [0, 1]
          zeroRatio = Math.max(0, Math.min(1, zeroRatio));


          // Define o gradiente com base na posição do zero
          gradient.addColorStop(0, 'rgba(0, 255, 8, 0.45)');
          gradient.addColorStop(zeroRatio, 'rgba(0, 255, 8, 0.11)');
          gradient.addColorStop(zeroRatio, 'rgba(255, 0, 0, 0.11)');
          gradient.addColorStop(1, 'rgba(255, 0, 0, 0.45)');

          return gradient;
        },
        borderColor: (context) => {
          const { chart } = context;
          const { ctx, chartArea, scales } = chart;
          if (!chartArea) return null;

          const { y } = scales;
          const zeroY = y.getPixelForValue(0);
          const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);

          // Corrigir aqui também:
          let zeroRatio = (zeroY - chartArea.top) / (chartArea.bottom - chartArea.top);
          zeroRatio = Math.max(0, Math.min(1, zeroRatio));

          gradient.addColorStop(0, 'rgba(0, 255, 8, 1)');
          gradient.addColorStop(zeroRatio, 'rgba(0, 255, 8, 0.24)');
          gradient.addColorStop(zeroRatio, 'rgba(208, 0, 0, 0.24)');
          gradient.addColorStop(1, 'rgb(208, 0, 0)');

          return gradient;
        },

        pointBackgroundColor: valores.map((value) =>
          value >= 0 ? 'rgba(0, 255, 8, 1)' : 'rgba(208, 0, 0, 1)'
        ),
        tension: 0.3,
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Gráfico de Desempenho',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };
  return (
    <div style={{ width: '700px', height:'400px', margin: '10 auto', fontSize:'10px', padding:'15px'}}>
      {selectedDateStart && <p>De : {selectedDateStart} </p>}
      {selectedDateEnd && <p>Até a : {selectedDateEnd}</p>}
      <Line data={data} options={options} />
    </div>
  );
};

export default ChartPerformance;
