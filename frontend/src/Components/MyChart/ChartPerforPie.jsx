import React from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Pie } from 'react-chartjs-2';

// Registrar os elementos específicos do gráfico de pizza
ChartJS.register(ArcElement, Tooltip, Legend);

const ChartPerforPie = () => {
  const data = {
    labels: ['Ganhos', 'Perdas'],
    datasets: [
      {
        label: 'Performance Financeira',
        data: [6500, 3500], // Exemplo: 6500 de ganho e 3500 de perda
        backgroundColor: ['rgba(0, 255, 8, 0.47)', 'rgba(255, 0, 0, 0.32)'], // Verde para ganhos, vermelho para perdas
        borderColor: ['#fff', '#fff'],
        borderWidth: 2,
      },
    ],
  };


  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
  };

  return (
    <div style={{ width: '300px', margin: 'auto' }}> 
      <h3 style={{ textAlign: 'center' }}>Ganhos vs Perdas</h3>
      <Pie data={data} options={options} />
    </div>
  );
};

export default ChartPerforPie;
