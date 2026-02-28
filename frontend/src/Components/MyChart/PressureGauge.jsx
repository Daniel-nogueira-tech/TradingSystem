import React, { useContext, useState, useEffect } from 'react';
import './MyChart.css';
import { OrderList } from 'primereact/orderlist';
import { AppContext } from '../../ContextApi/ContextApi';



const PressureGauge = () => {
  const { assetCorrelationData } = useContext(AppContext)
  // Altere este valor para testar (range sugerido: -100 a +100)
  const [pressure, setPressure] = useState(0);
  const [selectedSymbols, setSelectedSymbols] = useState([]);
  const [list, setList] = useState(assetCorrelationData || []);

  useEffect(() => {
    setList(assetCorrelationData || []);
  }, [assetCorrelationData]);

  

  // 🔹 Calcula % de ativos subindo vs caindo
  useEffect(() => {
      if (!assetCorrelationData || assetCorrelationData.length === 0) {
        setPressure(0);
        return;
      }

      const validItems = assetCorrelationData.filter(
        item => typeof item.variacao_pct === 'number'
      );

      const total = validItems.length;
      if (total === 0) {
        setPressure(0);
        return;
      }

      const positivos = validItems.filter(item => item.variacao_pct > 0).length;
      const negativos = validItems.filter(item => item.variacao_pct < 0).length;

      let percentual = 0;
      if (positivos > negativos) {
        percentual = (positivos / total) * 100;
      } else if (negativos > positivos) {
        percentual = -((negativos / total) * 100);
      } else {
        percentual = 0;
      }
      setPressure(Number(percentual.toFixed(2)));

      // Armazena para exibir nas porcentagens
      PressureGauge.positivos = positivos;
      PressureGauge.negativos = negativos;
      PressureGauge.total = total;
    }, [assetCorrelationData]);


  // Template customizado para exibir symbol e variação
  const itemTemplate = (item) => {
    return (
      <div className='picklist-item'>
        <div>{item.correlated_asset}</div>
        <span className={item.correlation >= 0 ? 'positive' : 'negative'}>
          {item.correlation > 0 ? '+' : ''}{item.correlation.toFixed(2)}
        </span>
      </div>
    );
  };


  // Normaliza o valor para ângulo (-90° = esquerda / +90° = direita)
  const getAngle = (value) => {
    // -100 → -90°, 0 → 0°, +100 → +90°
    return (value / 100) * 90;
  };

  const angle = getAngle(pressure);
  const isNegative = pressure < 0;
  const isPositive = pressure > 0;

  return (
    <div className='gauge-container-main'>
      <div className="gauge-container">
        <div className="gauge">
          {/* Arco de fundo com zonas de cor */}
          <div className="gauge-arc">
            <div className="zone negative"></div>
            <div className="zone neutral"></div>
            <div className="zone positive"></div>
          </div>

          {/* Ponteiro */}
          <div
            className="needle"
            style={{
              transform: `rotate(${angle}deg)`,
            }}
          >
            <div className="needle-body"></div>
            <div className="needle-tip"></div>
          </div>

          {/* Centro */}
          <div className="gauge-center"></div>

          {/* Valor numérico */}
          <div className="value-display">
            <span className={isNegative ? 'negative' : isPositive ? 'positive' : 'neutral'}>
              {pressure > 0 ? '+' : ''}{pressure}
            </span>
            <small>%</small>
          </div>
        </div>

        {/* Controles*/}
        <div className="controls">

          <div className='range-thermometer'>
            <input className='thermometer-slider'
              type="range"
              min="-100"
              max="100"
              value={pressure}
              onChange={e => setPressure(Number(e.target.value))}
            />
          </div>
        </div>
        {/* Porcentagens dos ativos */}
        <div className="gauge-percentages" style={{marginTop: '8px', display: 'flex', gap: '16px'}}>
           <span className="negative">
            {PressureGauge.negativos || 0} ativos caindo ({PressureGauge.total ? ((PressureGauge.negativos/PressureGauge.total)*100).toFixed(1) : 0}%)
          </span>
          <span className="positive">
            {PressureGauge.positivos || 0} ativos subindo ({PressureGauge.total ? ((PressureGauge.positivos/PressureGauge.total)*100).toFixed(1) : 0}%)
          </span>
         
        </div>

      </div>
      <div className='list-cript'>

        <OrderList
          value={list}
          header="Correlação"
          itemTemplate={itemTemplate}
          listStyle={{ height: '220px', width: '100%' }}
          onChange={(e) => {
            setList(e.value);
            setSelectedSymbols(e.value);
          }}
          dragdrop
          filter
          filterBy="correlated_asset,correlation"
          filterPlaceholder="Search"
        />

      </div>
    </div>
  );
};

export default PressureGauge;

