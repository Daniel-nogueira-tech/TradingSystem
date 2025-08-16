import React, { useRef, useContext, useEffect } from 'react';
import zoomPlugin from 'chartjs-plugin-zoom';
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
import { Bar } from 'react-chartjs-2'; // 👈 agora usamos Bar aqui
import { AppContext } from '../../ContextApi/ContextApi';
import Swal from 'sweetalert2';

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

const ChartBarSecondary = () => {
    const {
        valuesSecondary,
        labelsSecondary,
        handleSearchSec,
        inputRefSec,
        symbolSec,
        simulationLabelDataSec,
        simulationValueDataSec,
        realTime,
        setRealTime,
        isPausedSec,
        setIsPausedSec,
        showDaysInputSec,
        daysSec,
        daysValueSec,
        dateSimulationStartSec,
        dateSimulationEndSec,
        setDateSimulationEndSec,
        setDateSimulationStartSec,
        setDaysValueSec,
        dateSimulationSec,
        setShowDaysInputSec
    } = useContext(AppContext)
    const chartRef = useRef();

    const handleZoomIn = () => {
        if (chartRef.current) chartRef.current.zoom(1.2);
    };

    const handleZoomOut = () => {
        if (chartRef.current) chartRef.current.zoom(0.8);
    };

    const handleResetZoom = () => {
        if (chartRef.current) chartRef.current.resetZoom();
    };

    const activeValue = simulationValueDataSec?.length > 0 ? simulationValueDataSec : valuesSecondary;
    const activeLabel = simulationLabelDataSec?.length > 0 ? simulationLabelDataSec : labelsSecondary;


    const backgroundColor = activeValue.map((valor, index) => {
        if (index === 0) return 'rgba(113, 113, 113, 0.6)';
        return valor >= activeValue[index - 1]
            ? 'rgba(0, 200, 0, 0.4)'
            : 'rgba(200, 0, 0, 0.4)';
    });

    /* pega no localStore se e simulation ou real */
    useEffect(() => {
        const modoSalve = localStorage.getItem("realTimeMode");
        if (modoSalve) {
            setRealTime(modoSalve)
        }
    })
    useEffect(() => {
        if (realTime) {
            localStorage.setItem("realTimeMode", realTime);
        }
    }, [realTime]);


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
            setDateSimulationStartSec(date);
            setDaysValueSec('')

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
            setDateSimulationEndSec(date);
            setDaysValueSec('')

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

    const data = {
        labels: activeLabel,
        datasets: [
            {
                label: 'Tendência',
                data: activeValue,
                backgroundColor: backgroundColor,
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

            const niveis = [
                { valor: 22, texto: 'Pivot', cor: 'orange' },
                { valor: 30, texto: 'Pivot', cor: 'orange' },
                { valor: 38, texto: 'Pivot', cor: 'orange' },
            ];

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
                text: symbolSec,
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
                        speed: 0.1
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
                suggestedMin: Math.min(...activeValue) * 0.98,
                suggestedMax: Math.max(...activeValue) * 1.02,
            },
        },
    };

    return (
        <div style={{ width: '600px', margin: '0 auto' }}>
            <div style={{ display: 'flex' }}>
                <input
                    ref={inputRefSec}
                    type="text"
                    style={{
                        width: '140px',
                        borderRadius: '8px 0px 0px 8px',
                        border: 'none',
                        padding: '8px'
                    }}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSearchSec();
                    }}
                    placeholder='Pesquisa de Símbolo'
                />
                <button
                    className='button-search'
                    onClick={handleSearchSec}>
                    <img src="./search.svg" alt="search" />
                </button>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '10px' }}>
                    <button className='btn-zoom' onClick={handleZoomIn}>Zoom +</button>
                    <button className='btn-zoom' onClick={handleZoomOut}>Zoom -</button>
                    <button className='btn-zoom' onClick={handleResetZoom}>Reset</button>

                    {realTime === 'simulation' && (
                        <button
                            className='btn-zoom'
                            onClick={() => setIsPausedSec(prev => !prev)}
                        >
                            {isPausedSec ? '▶️ Continuar' : '⏸️ Pausar'}
                        </button>
                    )}
                </div>
            </div>

            {realTime === "simulation" && (
                <div className='dateSimulation'>

                    {!showDaysInputSec && (
                        <>
                            <button onClick={onChangeHandlerDateSimulationStart}>
                                De : {dateSimulationStartSec}
                            </button>

                            <button onClick={onChangeHandlerDateSimulationEnd}>
                                Até : {dateSimulationEndSec}
                            </button>
                        </>
                    )}

                    {!showDaysInputSec ? (
                        <button onClick={() => setShowDaysInputSec(true)}>
                            Dias :{daysSec}
                        </button>
                    ) : (
                        <div>
                            <span>Dias : </span>
                            <input
                                type="text"
                                placeholder="Digite a quantidade de dias"
                                value={daysValueSec}
                                onChange={(e) => {
                                    setDaysValueSec(e.target.value)
                                    setDateSimulationStartSec('');
                                    setDateSimulationEndSec('');
                                }}
                            />
                            <button onClick={() => setShowDaysInputSec(false)}>
                                OK
                            </button>
                        </div>
                    )}

                    {(daysValueSec || (dateSimulationStartSec && dateSimulationEndSec)) && (
                        <button onClick={dateSimulationSec}>Atualizar Dados</button>
                    )}

                </div>
            )}

            <Bar
                ref={chartRef}
                data={data}
                options={options}
                plugins={[customLabelPlugin, zoomPlugin]}
            />
        </div>
    );
};

export default ChartBarSecondary;
