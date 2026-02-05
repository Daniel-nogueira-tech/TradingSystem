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
import zoomPlugin from 'chartjs-plugin-zoom';
import { Line } from 'react-chartjs-2';
import { AppContext } from '../../ContextApi/ContextApi';
import { useContext } from 'react';
import { useRef } from 'react';
import { useEffect } from 'react';
import { ProgressBar } from 'primereact/progressbar';
import { useState } from 'react';


// Registrar os componentes no Chart.js
ChartJS.register(
   LineElement,
   PointElement,
   LinearScale,
   CategoryScale,
   Title,
   Tooltip,
   Legend,
   Filler,
   zoomPlugin,
);








const ChartRsi = ({ selectedDateStart, selectedDateEnd }) => {
   const { rsi, rsiTime, simulationValueDataRsi, simulationLabelDataRsi, windowSize } = useContext(AppContext);
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




   const value = rsi;
   const label = rsiTime.map(time =>
       new Date(time).toLocaleString('pt-BR', {
           day: '2-digit',
           month: '2-digit',
           hour: '2-digit',
           minute: '2-digit',
       })
   );






   const activeValue = simulationValueDataRsi?.length > 0 ? simulationValueDataRsi : value;
   const activeLabel = simulationLabelDataRsi?.length > 0 ? simulationLabelDataRsi : label;
    const visibleValues = activeValue.slice(-windowSize);
    const visibleLabels = activeLabel.slice(-windowSize);
   // Simula carregamento dos dados
   const isLoading = !(visibleValues && visibleValues.length > 0);




   const data = {
       labels: visibleLabels,
       datasets: [
           {
               label: 'índice',
               data: visibleValues,
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
                   gradient.addColorStop(ratio20, 'rgba(0, 255, 8, 0.36)'); // verde leve






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
                   gradient.addColorStop(ratio80, 'rgba(255, 25, 0, 1)');


                   // Entre 20 e 80 (linha verde)
                   gradient.addColorStop(ratio20, 'rgba(38, 255, 0, 1)');


                   // Abaixo de 20 (linha verde escuro)
                   gradient.addColorStop(1, 'rgba(21, 255, 0, 1)');


                   return gradient;
               },


               pointRadius: 0,
               tension: 0.3,
               borderWidth: 2,
           },




           // 🔹 Linha fixa no RSI 20
           {
               label: 'AMRSI 20',
               data: new Array(visibleLabels.length).fill(20), // Linha reta
               borderColor: 'white',
               borderWidth: 1,
               borderDash: [5, 5], // Linha tracejada
               pointRadius: 0, // Sem pontos
           },
           // 🔹 Linha fixa no RSI 80
           {
               label: 'AMRSI 80',
               data: new Array(visibleLabels.length).fill(80),
               borderColor: 'white',
               borderWidth: 1,
               borderDash: [5, 5],
               pointRadius: 0,
           },


           // 🔹 Linha fixa no RSI 30
           {
               label: 'AMRSI 30',
               data: new Array(visibleLabels.length).fill(30),
               borderColor: 'orange',
               borderWidth: 1,
               borderDash: [5, 5],
               pointRadius: 0,
           },


           // 🔹 Linha fixa no RSI 30
           {
               label: 'AMRSI 70',
               data: new Array(visibleLabels.length).fill(70),
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
               text: 'AMRSI (arithmetic mean of relative strength index)',
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
               suggestedMin: Math.min(...visibleLabels) * 0.98,
               suggestedMax: Math.max(...visibleLabels) * 0.102,
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
    <div
        style={{
            width: '100%',
            height: '350px',
            margin: '10px auto',
            fontSize: '10px',
            padding: '15px',
            position: 'relative'
        }}
    >
        {isLoading ? (
            <div
                style={{
                    width: "300px",
                    height: "30px",
                    margin: "0 auto",
                    position: "absolute",
                    top: "50%",
                    left: "50%",
                    transform: "translate(-50%, -50%)"
                }}
            >
                <ProgressBar
                    value={progress}
                    style={{
                        height: '30px',
                        backgroundColor: '#e187ff3f',
                        color: '#a54a4a'
                    }}
                />
            </div>
        ) : (
            <>
                <button className='btn-zoom' onClick={handleZoomIn}>Zoom +</button>
                <button className='btn-zoom' onClick={handleZoomOut}>Zoom -</button>
                <button className='btn-zoom' onClick={handleResetZoom}>Reset</button>

                {selectedDateStart && <p>De : {selectedDateStart}</p>}
                {selectedDateEnd && <p>Até a : {selectedDateEnd}</p>}

                <Line
                    ref={chartRef}
                    data={data}
                    options={options}
                    plugins={[zoomPlugin]}
                />
            </>
        )}
    </div>
);
};


export default ChartRsi;



