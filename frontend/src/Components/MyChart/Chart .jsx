import React, { useRef, useContext, useMemo } from 'react';
import zoomPlugin from 'chartjs-plugin-zoom';
import './MyChart.css';
import { ProgressBar } from 'primereact/progressbar';
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
import { useEffect } from 'react';
import Swal from 'sweetalert2';
import { useState } from 'react';
import 'primeicons/primeicons.css';

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
    const {
        values,
        labels,
        atr,
        handleSearch,
        inputRefMain,
        symbol,
        selectedPivots,
        simulationLabelData,
        simulationValueData,
        realTime,
        isPaused,
        setIsPaused,
        dateSimulationStart,
        dateSimulationEnd,
        setDateSimulationEnd,
        setDateSimulationStart,
        dateSimulation,
        daysValue,
        showDaysInput,
        setDaysValue,
        setShowDaysInput,
        days,
        windowSize,
     
    } = useContext(AppContext);
    const chartRef = useRef();
    const [progress, setProgress] = useState(0);


    const handleZoomIn = () => {
        if (chartRef.current) chartRef.current.zoom(1.2);
    };

    const handleZoomOut = () => {
        if (chartRef.current) chartRef.current.zoom(0.8);
    };

    const handleResetZoom = () => {
        if (chartRef.current) chartRef.current.resetZoom();
    };




    const activeValue = simulationValueData?.length > 0 ? simulationValueData : values;
    const activeLabel = simulationLabelData?.length > 0 ? simulationLabelData : labels;
    const visibleValues = activeValue.slice(-windowSize);
    const visibleLabels = activeLabel.slice(-windowSize);

    

    // Simula carregamento dos dados
    const isLoading = !(activeValue && activeValue.length > 0);



const backgroundColor = useMemo(() => {
    const len = activeValue.length;
    const result = new Array(len); // Pré-aloca o tamanho do array
    let trendState = null;

    result[0] = 'rgba(113, 113, 113, 0.6)';

    for (let i = 1; i < len; i++) {
        const diff = activeValue[i] - activeValue[i - 1];
        const threshold = atr / 2;

        if (diff >= threshold) trendState = 'up';
        else if (diff <= -threshold) trendState = 'down';

        if (trendState === 'up') result[i] = 'rgba(0, 255, 0, 0.44)';
        else if (trendState === 'down') result[i] = 'rgba(255, 0, 0, 0.44)';
        else result[i] = 'rgba(113, 113, 113, 0.6)';
    }

    return result;
}, [activeValue, atr]);


    /* simular trade  (pega a data do back teste)*/
    const onChangeHandlerDateSimulationStart = async () => {
        const { value: date } = await Swal.fire({
            title: "Selecione a data",
            input: "date",
            inputLabel: "Escolha uma data",
            inputPlaceholder: "Data",
            inputAttributes: {
                required: true,
            },
            customClass: {
                popup: 'fundo-preto',
                title: 'titulo-branco',
                inputLabel: 'label-branca',
                confirmButton: 'botao-verde',
                validationMessage: 'erro-custom'
            },
            didOpen: () => {
                const today = new Date().toISOString().split("T")[0];
                Swal.getInput().max = today;
            },
            preConfirm: (date) => {
                if (!date) {
                    Swal.showValidationMessage("Você precisa escolher uma data!");
                }
            }
        });
        if (date) {
            setDateSimulationStart(date);
            setDaysValue('')

            Swal.fire({
                title: 'Data selecionada:',
                text: date,
                customClass: {
                    popup: 'fundo-preto',
                    title: 'titulo-branco',
                    content: 'texto-branco',
                    confirmButton: 'botao-verde',
                }
            });
            // Aqui você pode disparar um fetch ou filtro com a data selecionada
            // Exemplo: fetchDataByDate(date);

        }
    };
    /*simular trade (pega a data do back teste)*/
    const onChangeHandlerDateSimulationEnd = async () => {
        const { value: date } = await Swal.fire({
            title: "Selecione a data",
            input: "date",
            inputLabel: "Escolha uma data",
            inputPlaceholder: "Data",
            inputAttributes: {
                required: true,
            },
            customClass: {
                popup: 'fundo-preto',
                title: 'titulo-branco',
                inputLabel: 'label-branca',
                confirmButton: 'botao-verde',
                validationMessage: 'erro-custom'
            },
            didOpen: () => {
                const today = new Date().toISOString().split("T")[0];
                Swal.getInput().max = today;
            },
            preConfirm: (date) => {
                if (!date) {
                    Swal.showValidationMessage("Você precisa escolher uma data!");
                }
            }
        });
        if (date) {
            setDateSimulationEnd(date);
            setDaysValue('')

            Swal.fire({
                title: 'Data selecionada:',
                text: date,
                customClass: {
                    popup: 'fundo-preto',
                    title: 'titulo-branco',
                    content: 'texto-branco',
                    confirmButton: 'botao-verde',
                }
            });

            // Aqui você pode disparar um fetch ou filtro com a data selecionada
            // Exemplo: fetchDataByDate(date);

        }
    };

    /* pega no localStore se e simulation ou real */
    // 1. Inicialização direta (Roda apenas UMA vez no carregamento)

    // 2. Efeito de Persistência (Único para o modo)
    useEffect(() => {
        localStorage.setItem("realTimeMode", realTime);
    }, [realTime]);

    // 3. Efeito de Progresso (Melhorado para evitar memory leaks)
    useEffect(() => {
        if (!isLoading) {
            setProgress(100);
            return;
        }

        setProgress(0);
        const interval = setInterval(() => {
            setProgress(prev => (prev >= 95 ? prev : prev + 5));
        }, 200);

        return () => clearInterval(interval);
    }, [isLoading]);




    const data = {
        labels: visibleLabels,
        datasets: [
            {
                label: 'Tendência',
                data: visibleValues,
                backgroundColor: backgroundColor.slice(-windowSize),
                borderRadius: 6,
            },
        ],
    };

    const customLabelPlugin = {
        id: 'customLabelPlugin',
        afterDatasetsDraw(chart) {
            const { ctx, chartArea, scales } = chart;
            const dataset = chart.data.datasets[0];
            const meta = chart.getDatasetMeta(0);
            const niveis = selectedPivots;

            niveis.forEach(nivel => {
                const index = dataset.data.findIndex(v => Math.abs(v - nivel.valor) < 0.01);
                if (index !== -1) {
                    const bar = meta.data[index];
                    const y = scales.y.getPixelForValue(nivel.valor);

                    ctx.save();
                    ctx.beginPath();
                    ctx.moveTo(bar.x, y);
                    ctx.lineTo(chartArea.right, y);
                    ctx.strokeStyle = nivel.cor;
                    ctx.setLineDash([4, 4]);
                    ctx.lineWidth = 1.2;
                    ctx.stroke();

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
                text: symbol,
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
                beginAtZero: false,
                type: 'linear',
                suggestedMin: Math.min(...visibleValues) * 0.98,
                suggestedMax: Math.max(...visibleValues) * 0.102,
            },
        },
    };

    return (
        <div style={{ width: '600px', margin: '0 auto' }}>
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
                        if (e.key === 'Enter') handleSearch();
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
                <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '10px' }}>
                    <button className='btn-zoom' onClick={handleZoomIn}>Zoom +</button>
                    <button className='btn-zoom' onClick={handleZoomOut}>Zoom -</button>
                    <button className='btn-zoom' onClick={handleResetZoom}>Reset</button>

                    {realTime === 'simulation' && (
                        <button
                            className='btn-zoom'
                            onClick={() => setIsPaused(prev => !prev)}
                        >
                            {isPaused ? <span className='pi pi-play' ></span> : <span className='pi pi-pause' ></span>}
                        </button>
                    )}

                </div>
            </div>

            {realTime === "simulation" && (
                <div className='dateSimulation'>

                    {!showDaysInput && (
                        <>
                            <button onClick={onChangeHandlerDateSimulationStart}>
                                De : {dateSimulationStart}
                            </button>

                            <button onClick={onChangeHandlerDateSimulationEnd}>
                                Até : {dateSimulationEnd}
                            </button>
                        </>
                    )}

                    {!showDaysInput ? (
                        <button onClick={() => setShowDaysInput(true)}>
                            Dias :{days}
                        </button>
                    ) : (
                        <div>
                            <span>Dias : </span>
                            <input
                                type="text"
                                placeholder="Digite a quantidade de dias"
                                value={daysValue}
                                onChange={(e) => {
                                    setDaysValue(e.target.value)
                                    setDateSimulationStart('');
                                    setDateSimulationEnd('');
                                }}
                            />
                            <button onClick={() => setShowDaysInput(false)}>
                                OK
                            </button>
                        </div>
                    )}

                    {(daysValue || (dateSimulationStart && dateSimulationEnd)) && (
                        <button onClick={dateSimulation}>Atualizar Dados</button>
                    )}

                </div>
            )}
            {isLoading ? (
                <div style={{ width: "300px", height: "270px", margin: "20px auto", textAlign: "center" }}>
                    <ProgressBar value={progress}
                        style={{
                            height: '30px',
                            top: "110px",
                            color: '#a54a4a',
                            backgroundColor: '#e187ff3f'
                        }} />
                </div>
            ) : (
                < >
                    <div>
                        <Bar
                            key={JSON.stringify(selectedPivots)}
                            ref={chartRef}
                            data={data}
                            options={options}
                            plugins={[customLabelPlugin, zoomPlugin]}
                        />
                    </div>

                </>
            )}
        </div>

    );
};

export default ChartBar;
