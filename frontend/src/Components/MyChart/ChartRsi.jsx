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
import { AppContext } from '../../ContextApi/ContextApi';
import { useContext } from 'react';

// Registrar os componentes no Chart.js
ChartJS.register(
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
    Title,
    Tooltip,
    Legend,
    Filler
);




const ChartRsi = ({ selectedDateStart, selectedDateEnd }) => {
    const { rsi, rsiTime } = useContext(AppContext);


    const value = rsi;

    const getPointColor = (v) => {
        if (v <= 20) return 'rgba(255, 0, 0, 1)';
        if (v >= 80) return 'rgba(255, 0, 0, 1)';
        return 'rgba(0, 255, 8, 1)';
    };


    const data = {
        labels: rsiTime,
        datasets: [
            {
                label: 'índice',
                data: value,
                fill: true,
                backgroundColor: (context) => {
                    const { chart } = context;
                    const { ctx, chartArea, scales } = chart;
                    if (!chartArea) return null;

                    const { y } = scales;

                    // Posição dos níveis no gráfico
                    const y20 = y.getPixelForValue(20);
                    const y80 = y.getPixelForValue(80);

                    // Normaliza posição em relação ao chartArea
                    let ratio20 = (y20 - chartArea.top) / (chartArea.bottom - chartArea.top);
                    let ratio80 = (y80 - chartArea.top) / (chartArea.bottom - chartArea.top);

                    ratio20 = Math.max(0, Math.min(1, ratio20));
                    ratio80 = Math.max(0, Math.min(1, ratio80));

                    // Cria gradiente
                    const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);

                    // Acima de 80 (sobrecompra)
                    gradient.addColorStop(0, 'rgba(255, 0, 0, 1)');   // vermelho forte
                    gradient.addColorStop(ratio80, 'rgba(255, 0, 0, 0.51)'); // laranja mais leve

                    // Entre 20 e 80 (neutro)
                    gradient.addColorStop(ratio20, 'rgba(0, 255, 8, 0.22)'); // verde leve



                    return gradient;
                },
                borderColor: (context) => {
                    const { chart } = context;
                    const { ctx, chartArea, scales } = chart;
                    if (!chartArea) return null;

                    const { y } = scales;
                    const y20 = y.getPixelForValue(20);
                    const y80 = y.getPixelForValue(80);

                    let ratio20 = (y20 - chartArea.top) / (chartArea.bottom - chartArea.top);
                    let ratio80 = (y80 - chartArea.top) / (chartArea.bottom - chartArea.top);

                    ratio20 = Math.max(0, Math.min(1, ratio20));
                    ratio80 = Math.max(0, Math.min(1, ratio80));

                    const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);

                    // Acima de 80 (linha vermelha)
                    gradient.addColorStop(0, 'rgba(255, 0, 0, 1)');
                    gradient.addColorStop(ratio80, 'rgba(255, 102, 0, 0.8)');

                    // Entre 20 e 80 (linha verde)
                    gradient.addColorStop(ratio20, 'rgba(42, 255, 4, 1)');

                    // Abaixo de 20 (linha verde escuro)
                    gradient.addColorStop(1, 'rgba(0, 150, 0, 0.9)');

                    return gradient;
                },

                pointRadius: 0,
                tension: 0.3,
                borderWidth: 2,
            },


            // 🔹 Linha fixa no RSI 20
            {
                label: 'AMRSI 20',
                data: new Array(rsiTime.length).fill(20), // Linha reta
                borderColor: 'white',
                borderWidth: 1,
                borderDash: [5, 5], // Linha tracejada
                pointRadius: 0, // Sem pontos
            },
            // 🔹 Linha fixa no RSI 80
            {
                label: 'AMRSI 80',
                data: new Array(rsiTime.length).fill(80),
                borderColor: 'white',
                borderWidth: 1,
                borderDash: [5, 5],
                pointRadius: 0,
            },

            // 🔹 Linha fixa no RSI 30
            {
                label: 'AMRSI 30',
                data: new Array(rsiTime.length).fill(30),
                borderColor: 'orange',
                borderWidth: 1,
                borderDash: [5, 5],
                pointRadius: 0,
            },

            // 🔹 Linha fixa no RSI 30
            {
                label: 'AMRSI 60',
                data: new Array(rsiTime.length).fill(70),
                borderColor: 'orange',
                borderWidth: 1,
                borderDash: [5, 5],
                pointRadius: 0,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Media aritmética de índice de força relativa.',
            },
        },
        scales: {
            y: {
                beginAtZero: true,
            },
        },
    };
    return (
        <div style={{ width: '100%', height: '350px', margin: '10 auto', fontSize: '10px', padding: '15px' }}>
            {selectedDateStart && <p>De : {selectedDateStart} </p>}
            {selectedDateEnd && <p>Até a : {selectedDateEnd}</p>}
            <Line data={data} options={options} />
        </div>
    );
};

export default ChartRsi;
