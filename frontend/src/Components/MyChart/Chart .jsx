import React, { useRef, useContext, useMemo } from 'react';
import zoomPlugin from 'chartjs-plugin-zoom';
import './MyChart.css';
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
        loadingSimulation,
        downloadedData,
        dadosPrice,

    } = useContext(AppContext);
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



    const value = new Float64Array(dadosPrice.length);
    const label = new Array(dadosPrice.length);

    for (let i = 0; i < dadosPrice.length; i++) {
        value[i] = dadosPrice[i].closePrice;
        label[i] = dadosPrice[i].closeTime;
    }
        const labels = label.map(time =>
        new Date(time).toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        })
    );


    // Dados ativos para gráfico (prioriza simulação se disponível)
    const activeValueRaw = simulationValueData?.length > 0 ? simulationValueData : value;
    const activeLabelRaw = simulationLabelData?.length > 0 ? simulationLabelData : labels ;

    // remove valores 0 do início
    const firstValidIndex = activeValueRaw.findIndex(v => v > 0);

    const activeValue = firstValidIndex !== -1 ? activeValueRaw.slice(firstValidIndex) : [];
    const activeLabel = firstValidIndex !== -1 ? activeLabelRaw.slice(firstValidIndex) : [];
    const visibleValues = activeValue.slice(-windowSize);
    const visibleLabels =  activeLabel.slice(-windowSize);

    // Simula carregamento dos dados
    const isLoading = !(activeValue && activeValue.length > 0);



    const backgroundColor = useMemo(() => {
        const len = activeValue.length;
        const result = new Array(len);
        let trendState = null;

        if (len === 0) return result;

        result[0] = 'rgba(113, 113, 113, 0.6)';

        // Calcula threshold baseado na volatilidade dos dados visíveis
        const visibleData = activeValue.slice(-windowSize);
        let threshold = atr > 0 ? atr / 2 : 0.01;

        // Se ATR for muito pequeno ou dados tiverem baixa volatilidade, usa threshold dinâmico
        if (visibleData.length > 1) {
            const diffs = visibleData.slice(1).map((val, i) => Math.abs(val - visibleData[i]));
            const avgDiff = diffs.reduce((a, b) => a + b, 0) / diffs.length;
            const dynamicThreshold = avgDiff * 0.1; // 10% da mudança média

            // Usa o maior entre ATR e threshold dinâmico
            threshold = Math.max(threshold, dynamicThreshold, 0.001);
        }

        for (let i = 1; i < len; i++) {
            const diff = activeValue[i] - activeValue[i - 1];

            if (diff >= threshold) trendState = 'up';
            else if (diff <= -threshold) trendState = 'down';

            if (trendState === 'up') result[i] = 'rgba(0, 255, 0, 0.6)';
            else if (trendState === 'down') result[i] = 'rgba(255, 0, 0, 0.6)';
            else result[i] = 'rgba(113, 113, 113, 0.6)';
        }

        return result;
    }, [activeValue, atr, windowSize]);


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






    const data = {
        labels: visibleLabels,
        datasets: [
            {
                label: '',
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
        maintainAspectRatio: false,
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
                beginAtZero: true,
                type: 'linear',
                min: visibleValues.length > 0 ? Math.min(...visibleValues) * 0.995 : undefined,
                max: visibleValues.length > 0 ? Math.max(...visibleValues) * 1.005 : undefined,
                grid: {
                    color: 'rgba(200, 200, 200, 0.1)',
                },
            },
        },
    };

    return (
        <div className='container-charts-pri'>
            <div className='search-container'>
                <input
                    ref={inputRefMain}
                    type="text"
                    style={{
                        width: '100px',
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
                    className='button-search pi pi-search'
                    onClick={handleSearch}
                >
                </button>
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '10px' }}>
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
                        <button
                            onClick={dateSimulation}
                            disabled={loadingSimulation}
                            style={{
                                minWidth: '160px',
                                padding: '8px 12px',
                                fontWeight: '500',
                                border: loadingSimulation
                                    ? '2px solid #666'                           // durante loading → cinza
                                    : downloadedData
                                        ? '2px solid #4caf50'                      // sucesso → verde
                                        : '2px solid #f44336',                     // pendente → vermelho
                                borderRadius: '6px',
                                backgroundColor: loadingSimulation
                                    ? '#424242'
                                    : downloadedData
                                        ? '#2e7d32'
                                        : '#c62828',
                                color: '#fff',
                                cursor: loadingSimulation ? 'not-allowed' : 'pointer',
                                opacity: loadingSimulation ? 0.7 : 1,
                                transition: 'all 0.25s ease',
                            }}
                        >
                            {loadingSimulation ? (
                                <>
                                    <i className="pi pi-spin pi-spinner" style={{ marginRight: '8px' }} />
                                    Baixando...
                                </>
                            ) : downloadedData ? (
                                <>
                                    <i className="pi pi-check" style={{ marginRight: '8px' }} />
                                    Dados baixados
                                </>
                            ) : (
                                'Baixar dados'
                            )}
                        </button>
                    )}

                </div>
            )}
            {isLoading ? (
                <div style={{ width: "100%", height: "400px", margin: "20px auto" }} />
            ) : (
                <div style={{ position: 'relative', height: '400px', width: '100%', margin: '20px auto' }}>
                    <Bar
                        key={JSON.stringify(selectedPivots)}
                        ref={chartRef}
                        data={data}
                        options={options}
                        plugins={[customLabelPlugin, zoomPlugin]}
                    />
                </div>
            )}
        </div>

    );
};

export default ChartBar;
