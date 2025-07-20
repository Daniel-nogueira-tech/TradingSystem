import React, { useRef, useEffect, useContext } from 'react';
import zoomPlugin from 'chartjs-plugin-zoom';
import './MyChart.css'
import {
    Chart as ChartJS,
    BarElement,
    CategoryScale,
    LinearScale,
    Title,
    Tooltip,
    Legend,
    LogarithmicScale,

} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { AppContext } from '../../ContextApi/ContextApi';


ChartJS.register(
    BarElement,
    CategoryScale,
    LinearScale,
    Title,
    Tooltip,
    Legend,
    LogarithmicScale,
    zoomPlugin,
);



const ChartBar = () => {
    const { values, labels, handleSearch, inputRefMain } = useContext(AppContext);




    // Gerar cores com base na comparação com o valor anterior
    const backgroundColor = values.map((valor, index) => {
        if (index === 0) return 'rgba(113, 113, 113, 0.6)'; // primeiro valor (neutro)
        return valor >= values[index - 1]
            ? 'rgba(0, 200, 0, 0.4)'   // verde se maior ou igual
            : 'rgba(200, 0, 0, 0.4)'; // vermelho se menor
    });

    const data = {
        labels: labels,
        datasets: [
            {
                label: 'Tendência',
                data: values,
                backgroundColor: backgroundColor,
                borderRadius: 6,
            },
        ],
    };

    // Plugin que desenha texto em cima das barras
    const customLabelPlugin = {
        id: 'customLabelPlugin',
        afterDatasetsDraw(chart) {
            const { ctx, chartArea, scales } = chart;
            const dataset = chart.data.datasets[0];
            const meta = chart.getDatasetMeta(0);

            // Seus níveis de referência
            const niveis = [
                { valor: 110255.63, texto: 'Pivot', cor: 'orange' },
                { valor: 107950, texto: 'Pivot', cor: 'orange' },
                { valor: 108400, texto: 'Pivot', cor: 'orange' },
            ];

            niveis.forEach(nivel => {
                // Procura a primeira barra que tem exatamente o valor
                const index = dataset.data.findIndex(v => Math.abs(v - nivel.valor) < 0.01);


                if (index !== -1) {
                    const bar = meta.data[index];
                    const y = scales.y.getPixelForValue(nivel.valor);

                    ctx.save();
                    ctx.beginPath();
                    ctx.moveTo(bar.x, y); // começa na barra que atingiu o valor
                    ctx.lineTo(chartArea.right, y); // vai até o fim do gráfico
                    ctx.strokeStyle = nivel.cor;
                    ctx.setLineDash([4, 4]);
                    ctx.lineWidth = 1.2;
                    ctx.stroke();

                    // Escreve o nome ao lado da barra
                    ctx.fillStyle = nivel.cor;
                    ctx.font = '12px sans-serif';
                    ctx.textAlign = 'left';
                    ctx.fillText(`${nivel.texto}: ${nivel.valor}`, bar.x + 5, y - 6);

                    ctx.restore();
                }
            });
        },
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'Gráfico BTC',
            },
            customLabelPlugin,
            zoom: {
                pan: {
                    enabled: true,
                    mode: 'x', // ou 'xy' se quiser arrastar vertical também
                },
                zoom: {
                    wheel: {
                        enabled: true, // zoom com scroll do mouse
                    },
                    pinch: {
                        enabled: true // zoom com gesto de pinça em touch
                    },
                    mode: 'x', // zoom horizontal
                }

            },
        },
        scales: {
            y: {
                beginAtZero: false,
                type: 'linear',
                suggestedMin: Math.min(...values) * 0.98,
                suggestedMax: Math.max(...values) * 1.02,
            },
        },

    };





    return (
        <div style={{ width: '600px', margin: '0 auto' }} >
            <div style={{ display: 'flex' }}>
                <input
                     ref={inputRefMain}
                    type="text"
                    style={{
                        width: '140px',
                        borderRadius: '8px 0px 0px 8px',
                        border: 'none',
                        padding: '8px'
                    }}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                            handleSearch();
                        }
                    }}
                    placeholder='Pesquisa de Símbolo'
                />
                <button
                    type='submit'
                    className='button-search'
                    onClick={handleSearch}
                >
                    <img src="./search.svg" alt="search" />

                </button>
            </div>
            <Bar data={data} options={options} plugins={[customLabelPlugin, zoomPlugin]} />
        </div>

    );
};

export default ChartBar;



