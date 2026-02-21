import React from 'react';
import './Correlation.css';
import { useContext } from 'react';
import { AppContext } from '../../ContextApi/ContextApi';

const Correlation = () => {
  const { dataCorrelation } = useContext(AppContext)

  if (!dataCorrelation || !dataCorrelation.symbols || !dataCorrelation.matrix) {
    return <div>Loading...</div>;
  }

  const cryptos = dataCorrelation.symbols;
  const matrix = dataCorrelation.matrix;

  const getClass = (value) => {
    if (value >= 0.75) return 'high';
    if (value >= 0.5) return 'medium';
    if (value <= -0.75) return 'inverse-strong';
    if (value <= -0.5) return 'inverse';
    return 'low';
  };


  return (
    <div className="correlation-main">
      <h2>Tabela de Correlação</h2>

      <div className="correlation-table-wrapper">
        <table className="correlation-table">
          <thead>
            <tr>
              <th></th>
              {cryptos.map((sym) => (
                <th key={sym}>{sym.replace('USDT', '')}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {cryptos.map((sym, rowIndex) => (
              <tr key={sym}>
                <td className="crypto-label">
                  {sym.replace('USDT', '')}
                </td>

                {matrix[rowIndex]?.map((value, colIndex) => (
                  <td
                    key={colIndex}
                    className={getClass(value)}
                  >
                    {Number(value).toFixed(2)}
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