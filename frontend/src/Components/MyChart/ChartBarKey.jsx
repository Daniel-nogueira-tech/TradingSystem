import React, { useContext } from 'react';
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

const ChartBarKey = () => {
    const { labelsKey, valuesKey, symbol, symbolSec, importantPointsKey, selectedPivotsKey } = useContext(AppContext);

    if (!importantPointsKey || !importantPointsKey["Tendência"]) {
        return <div>Carregando gráfico...</div>;
    }

    // Gerar cores com base na comparação com o valor anterior
    const backgroundColor = valuesKey.map((valor, index) => {
        if (index === 0) return 'rgba(113, 113, 113, 0.6)'; // primeiro valor (neutro)
        return valor >= valuesKey[index - 1]
            ? 'rgba(168, 186, 10, 0.84)'   // verde se maior ou igual
            : 'rgba(163, 163, 163, 0.63)'; // vermelho se menor
    });

    const data = {
        labels: labelsKey,
        datasets: [
            {
                label: 'Chave',
                data: valuesKey,
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
            const niveis = selectedPivotsKey;


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
                text: `Σ - ${symbol} + ${symbolSec}`,
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
                suggestedMin: Math.min(...valuesKey) * 0.98,
                suggestedMax: Math.max(...valuesKey) * 1.02,
            },
        },
    };

    return (
        <div style={{ width: '600px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <Bar key={JSON.stringify(selectedPivotsKey)} data={data} options={options} plugins={[customLabelPlugin]} />
        </div>

    );
};

export default ChartBarKey;
