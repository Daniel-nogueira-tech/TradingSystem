import React from 'react';
import './Correlation.css';

const Correlation = () => {
  const cryptos = ['BTC', 'ETH', 'SOL', 'BNB', 'TDS'];
  // Sample correlation matrix (values between -1 and 1)
  const matrix = [
    [1, 0.85, 0.65, 0.72, 0.2],
    [0.85, 1, 0.70, 0.68, 0.8],
    [0.65, 0.70, 1, 0.60, 0.1],
    [0.72, 0.68, 0.60, 1, 0.4],
    [0.72, 0.68, 0.60, 1, 0.7],

  ];

  return (
    <div className="correlation-main">
      <h2>Tabela de Correlação de Criptomoedas</h2>
      <div className="correlation-table-wrapper">
        <table className="correlation-table">
          <thead>
            <tr>
              <th></th>
              {cryptos.map((sym) => (
                <th key={sym}>{sym}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {cryptos.map((sym, rowIndex) => (
              <tr key={sym}>
                <td className="crypto-label">{sym}</td>
                {matrix[rowIndex].map((value, colIndex) => (
                  <td key={colIndex} className={
                    value > 0.8 ? 'high' : value > 0.5 ? 'medium' : 'low'
                  }>
                    {value.toFixed(2)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Correlation;