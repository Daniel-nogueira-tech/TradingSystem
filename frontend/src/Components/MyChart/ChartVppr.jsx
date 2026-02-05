import React, { useContext } from "react";
import zoomPlugin from 'chartjs-plugin-zoom';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    LineElement,
    PointElement,
    Tooltip,
    Legend,
} from "chart.js";
import { Chart } from "react-chartjs-2";
import { AppContext } from "../../ContextApi/ContextApi";
import { useRef } from "react";
import { ProgressBar } from "primereact/progressbar";
import { useState } from "react";
import { useEffect } from "react";
import { useMemo } from "react";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    LineElement,
    PointElement,
    Tooltip,
    Legend,
    zoomPlugin,
);



const ChartVppr = () => {
    const { vppr, vpprTime, vpprEma, simulationLabelDataVppr, simulationValueDataVppr, simulationValueDataVpprEma,windowSize } = useContext(AppContext);
    const chartRef = useRef();
    const [progress, setProgress] = useState(0);

    /* Função para zoom*/
    const handleZoomIn = () => {
        if (chartRef.current) chartRef.current.zoom(1.2);
    };
    const handleZoomOut = () => {
        if (chartRef.current) chartRef.current.zoom(0.8);
    };
    const handleResetZoom = () => {
        if (chartRef.current) chartRef.current.resetZoom();
    };

    const labels = vpprTime.map(time =>
        new Date(time).toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        })
    );

    const activeValueVppr = useMemo(() => {
        return simulationValueDataVppr?.length > 0
            ? simulationValueDataVppr
            : vppr;
    }, [simulationValueDataVppr, vppr]);

    const activeLabelVppr = useMemo(() => {
        return simulationLabelDataVppr?.length > 0
            ? simulationLabelDataVppr
            : labels;
    }, [simulationLabelDataVppr, labels]);
    
    
    const activeValueVpprEma = useMemo(() => {
        return simulationValueDataVpprEma?.length > 0
            ? simulationValueDataVpprEma
            : vpprEma;
    }, [simulationValueDataVpprEma, vpprEma]);

    const visibleValuesVppr = activeValueVppr.slice(-windowSize);
    const visibleLabelsVppr = activeLabelVppr.slice(-windowSize);
    const visibleValuesVpprEma = activeValueVpprEma.slice(-windowSize);

    // Simula carregamento dos dados
    const isLoading = !(visibleValuesVppr  && visibleValuesVppr.length > 0);


    const data = useMemo(() => {
        return {
            labels: visibleLabelsVppr,
            datasets: [
                {
                    type: "line",
                    label: "VPPR EMA (week)",
                    data: visibleValuesVpprEma,
                    borderColor: "rgba(0, 148, 253, 1)",
                    backgroundColor: "rgba(0, 150, 255, 0.3)",
                    tension: 0.3,
                    pointRadius: 0,
                    borderWidth: 2,
                },
                {
                    label: 'VPPR',
                    type: "line",
                    data: visibleValuesVppr,
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 0,

                    // ⚠️ essas funções continuam dinâmicas, mas o objeto em si não recria sempre
                    backgroundColor: (context) => {
                        const { chart } = context;
                        const { ctx, chartArea, scales } = chart;
                        if (!chartArea) return null;

                        const zeroY = scales.y.getPixelForValue(0);
                        const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);

                        let zeroRatio = (zeroY - chartArea.top) / (chartArea.bottom - chartArea.top);
                        zeroRatio = Math.max(0, Math.min(1, zeroRatio));

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

                        const zeroY = scales.y.getPixelForValue(0);
                        const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);

                        let zeroRatio = (zeroY - chartArea.top) / (chartArea.bottom - chartArea.top);
                        zeroRatio = Math.max(0, Math.min(1, zeroRatio));

                        gradient.addColorStop(0, 'rgba(0, 255, 8, 1)');
                        gradient.addColorStop(zeroRatio, 'rgba(0, 255, 8, 0.24)');
                        gradient.addColorStop(zeroRatio, 'rgba(208, 0, 0, 0.24)');
                        gradient.addColorStop(1, 'rgb(208, 0, 0)');

                        return gradient;
                    },

                    pointBackgroundColor: visibleValuesVppr.map(v =>
                        v >= 0 ? 'rgba(0, 255, 8, 1)' : 'rgba(208, 0, 0, 1)'
                    ),
                },
            ],
        };
    }, [visibleLabelsVppr, visibleValuesVppr, visibleValuesVpprEma]);


    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'VPPR (Volume Price Pressure Ratio)',
            },
            zoom: {
                pan: {
                    enabled: true,
                    mode: 'xy',
                    modifierKey: 'ctrl',
                },
                zoom: {
                    wheel: {
                        enabled: true,
                        modifierKey: 'shift',
                        speed: 0.1,
                    },
                    drag: {
                        enabled: true,
                        borderColor: 'rgba(225,225,225,0.3)',
                        borderWidth: 1,
                        backgroundColor: 'rgba(225,225,225,0.1)',
                    },
                    pinch: {
                        enabled: true,
                    },
                    mode: 'xy',
                },
                limits: {
                    x: { min: 'original', max: 'original' },
                    y: { min: 'original', max: 'original' },
                },
            },
        },


        scales: {
            y: {
                beginAtZero: true,
                type: 'linear',
                suggestedMin: Math.min(...visibleLabelsVppr) * 0.98,
                suggestedMax: Math.max(...visibleLabelsVppr) * 0.102,
            },
        },
    };


    //Efeito para animar o progresso
    useEffect(() => {
        if (!isLoading) {
            setProgress(100);
            return;
        }

        setProgress(0);

        const interval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 99) return prev;
                return prev + 5;
            });
        }, 200);

        return () => clearInterval(interval);
    }, [isLoading]);


    return (
        isLoading ? (
            <div
                style={{
                    width: "300px",
                    height: "270px",
                    margin: "20px auto",
                    textAlign: "center"
                }}
            >
                <ProgressBar value={progress}
                    style={{
                        height: '30px',
                        top: "110px",
                        color: '#a54a4a',
                        backgroundColor: '#e187ff3f'
                    }} />
            </div>
        ) : (
            <>
                <div
                    style={{
                        width: "100%",
                        height: "350px",
                        margin: "10px auto",
                        fontSize: "10px",
                        padding: "15px"
                    }}
                >
                    <div
                        style={{
                            display: "flex",
                            justifyContent: "center",
                            gap: "10px",
                            marginBottom: "10px"
                        }}
                    >
                        <button className="btn-zoom" onClick={handleZoomIn}>
                            Zoom +
                        </button>
                        <button className="btn-zoom" onClick={handleZoomOut}>
                            Zoom -
                        </button>
                        <button className="btn-zoom" onClick={handleResetZoom}>
                            Reset
                        </button>
                    </div>

                    <Chart
                        ref={chartRef}
                        type="bar"
                        data={data}
                        options={options}
                        plugins={[zoomPlugin]}
                    />
                </div>
            </>
        )
    );
};

export default ChartVppr;
