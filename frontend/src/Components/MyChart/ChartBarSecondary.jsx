import React, { useRef, useEffect, useContext } from 'react';
import zoomPlugin from 'chartjs-plugin-zoom';
import {
    Chart as ChartJS,
    BarElement,
    CategoryScale,
    LinearScale,
    Title,
    Tooltip,
    Legend,
    LogarithmicScale
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
    zoomPlugin
);

const ChartBarSecondary = () => {
    const { valuesSecondary, labelsSecondary } = useContext(AppContext)

    // Gerar cores com base na comparação com o valor anterior
    const backgroundColor = valuesSecondary.map((valor, index) => {
        if (index === 0) return 'rgba(113, 113, 113, 0.6)'; // primeiro valor (neutro)
        return valor >= valuesSecondary[index - 1]
            ? 'rgba(0, 200, 0, 0.4)'   // verde se maior ou igual
            : 'rgba(200, 0, 0, 0.4)'; // vermelho se menor
    });

    const data = {
        labels: labelsSecondary,
        datasets: [
            {
                label: 'Tendência',
                data: valuesSecondary,
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
                { valor: 22, texto: 'Pivot', cor: 'orange' },
                { valor: 30, texto: 'Pivot', cor: 'orange' },
                { valor: 38, texto: 'Pivot', cor: 'orange' },
            ];

            niveis.forEach(nivel => {
                // Procura a primeira barra que tem exatamente o valor
                const index = dataset.data.findIndex(v => v === nivel.valor);

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
                text: 'Gráfico ETHUSD',
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
                suggestedMin: Math.min(...valuesSecondary) * 0.98,
                suggestedMax: Math.max(...valuesSecondary) * 1.02,
            },
        },
    };

    const inputRef = useRef(null);
    useEffect(() => {
        inputRef.current.focus();
    }, []);

    return (
        <div style={{ width: '600px', margin: '0 auto' }}>
            <form style={{ display: 'flex' }}>
                <input
                    ref={inputRef}
                    type="text"
                    style={{
                        width: '140px',
                        borderRadius: '8px 0px 0px 8px',
                        border: 'none',
                        padding: '8px'
                    }}
                    placeholder='Pesquisa de Símbolo'
                />
                <button
                    className='button-search'
                    onClick={() => inputRef.current.focus(null)} >
                    <img src="./search.svg" alt="search" />
                </button>
            </form>
            <Bar data={data} options={options} plugins={[customLabelPlugin]} />
        </div>
    );
};

export default ChartBarSecondary;
