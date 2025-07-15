import React from 'react';
import {
    Chart as ChartJS,
    BarElement,
    CategoryScale,
    LinearScale,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
    BarElement,
    CategoryScale,
    LinearScale,
    Title,
    Tooltip,
    Legend
);

const ChartBarKey = () => {
    const valores = [20, 25, 30, 25, 24, 22, 25, 30, 34, 38, 30, 45, 50, 52, 58, 80,];

    // Gerar cores com base na comparação com o valor anterior
    const backgroundColor = valores.map((valor, index) => {
        if (index === 0) return 'rgba(113, 113, 113, 0.6)'; // primeiro valor (neutro)
        return valor >= valores[index - 1]
            ? 'rgba(255, 251, 0, 0.59)'   // verde se maior ou igual
            : 'rgba(163, 163, 163, 0.63)'; // vermelho se menor
    });

    const data = {
        labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'agos', 'set', 'otu', 'nov', 'dez', 'Jan', 'Fev', 'Mar', 'Abr',],
        datasets: [
            {
                label: 'Chave',
                data: valores,
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
                { valor: 22, texto: 'Pivot', cor: 'white' },
                { valor: 30, texto: 'Pivot', cor: 'white' },
                { valor: 38, texto: 'Pivot', cor: 'white' },
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
        },
        scales: {
            y: {
                beginAtZero: true,
            },
        },
    };
    return (
        <div style={{ width: '600px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <Bar data={data} options={options} plugins={[customLabelPlugin]} />
        </div>

    );
};

export default ChartBarKey;
