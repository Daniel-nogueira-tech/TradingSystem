import React from 'react';
import './Market.css';

const Market = () => {
  const cryptos = [
    { name: 'Bitcoin', price: '$65,200', change: '+2.5%', close: '$64,500', volume: '$32B' },
    { name: 'Ethereum', price: '$3,200', change: '-1.2%', close: '$3,240', volume: '$15B' },
    { name: 'Solana', price: '$150', change: '+0.8%', close: '$149', volume: '$3.2B' },
    { name: 'BNB', price: '$580', change: '-0.6%', close: '$584', volume: '$1.1B' },
  ];

  return (
    <div className='market-main'>
      <div className='market'>
        <h2>Mercado de Criptomoedas</h2>
        <table className='market-table'>
          <thead>
            <tr>
              <th>Nome</th>
              <th>Preço</th>
              <th>Variação</th>
              <th>Fechamento</th>
              <th>Volume</th>
            </tr>
          </thead>
          <tbody>
            {cryptos.map((crypto, index) => (
              <tr key={index}>
                <td>{crypto.name}</td>
                <td>{crypto.price}</td>
                <td className={crypto.change.includes('-') ? 'negative' : 'positive'}>
                  {crypto.change}
                </td>
                <td>{crypto.close}</td>
                <td>{crypto.volume}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Market;
