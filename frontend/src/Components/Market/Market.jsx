import React from 'react';
import './Market.css';
import { AppContext } from '../../ContextApi/ContextApi';
import 'primeicons/primeicons.css';

import { Messages } from 'primereact/messages';


const Market = () => {
  const { marketObservation, addSymbol, setAddSymbol, saveMarketNotes } = React.useContext(AppContext);

  const [data, setData] = React.useState([]);
  const [filterSymbol, setFilterSymbol] = React.useState('');
  const [showFilter, setShowFilter] = React.useState(false);
  const [newSymbol, setNewSymbol] = React.useState(false);
  const msgs = React.useRef(null);



  React.useEffect(() => {
    if (marketObservation) {
      setData(marketObservation);
    }
  }, [marketObservation]);

  const handleRemove = (symbol) => {
    setData(prev =>
      prev.filter(item => item.symbol !== symbol)
    );
  };

  const filteredData = data.filter(item =>
    item.symbol.toUpperCase().includes(filterSymbol.toUpperCase())
  );

  if (!marketObservation || marketObservation.length === 0) {
    return (
      <div className="market-main">
        <div className="market">
          <h2>Mercado de Criptomoedas</h2>
          <p>Carregando dados do mercado...</p>
        </div>
      </div>
    );
  }



  return (
    <div className="market-main" >
      <div className="market">
        <div style={{ position: 'relative' }}>
          <h2>
            Mercado de Criptomoedas
            <div className="search-container">
              <button
                className="filter-btn"
                onClick={() => setShowFilter(!showFilter)}
                title="Pesquisar símbolo"
              >
                <div className="search-icon-wrapper">
                  <span className="pi pi-search search-icon" />
                </div>
              </button>

              <button className='add' title="Adicionar símbolo"
                onClick={() => setNewSymbol(!newSymbol)}
              >
                <span className="pi pi-plus" />
              </button>
              {/* Filtro de símbolo popup */}
              {showFilter && (
                <div className="filter-popup">
                  <span className="close-btn" onClick={() => setShowFilter(false)}>&times;</span>
                  <input
                    type="text"
                    placeholder="Buscar símbolo..."
                    value={filterSymbol}
                    onChange={(e) => setFilterSymbol(e.target.value)}
                    autoFocus
                  />
                </div>
              )}

              {/* Adicionar símbolo popup */}
              {newSymbol && (
                <div className="filter-popup">
                  <span className="close-btn" onClick={() => setNewSymbol(false)}>&times;</span>
                  <input
                    type="text"
                    placeholder="Adicionar símbolo..."
                    value={addSymbol}
                    onChange={(e) => setAddSymbol(e.target.value.toUpperCase())}
                    autoFocus
                  />

                  <button
                    className="add-btn"
                    onClick={() => {
                      if (!addSymbol.trim()) {
                        msgs.current.clear();
                        msgs.current.show({
                          severity: 'warn',
                          summary: '',
                          detail: 'Adicione um símbolo válido para continuar.',
                          sticky: false,
                          life: 3000
                        });
                        return;
                      }

                      saveMarketNotes();
                      setAddSymbol('');
                      setNewSymbol(false);
                      msgs.current.clear();
                    }}
                  >
                    Add
                  </button>
                  <Messages ref={msgs} />
                </div>
              )}


            </div>
          </h2>
        </div>
        <table className="market-table">
          <thead>
            <tr>

              <th>Simbolo</th>
              <th>Variação %</th>
              <th>Variação pts</th>
              <th>Fechamento</th>
              <th>Máxima</th>
              <th>Mínimo</th>
              <th>Volume</th>
              <th>Ação</th>
            </tr>
          </thead>

          <tbody>
            {filteredData.map((item, index) => (
              <tr key={index}>
                <td>{item.symbol}</td>

                <td className={item.variacao < 0 ? 'negative' : 'positive'}>
                  {item.variacao_pct}%
                </td>
                <td className={item.variacao < 0 ? 'negative' : 'positive'}>
                  {item.variacao}
                </td>

                <td>{item.Fechamento}</td>

                <td>{item.Maximo}</td>
                <td>{item.Minimo}</td>

                <td>{item.Volume}</td>

                <td>
                  <button
                    className="remove-btn"
                    onClick={() => handleRemove(item.symbol)}
                  >
                    <span className="pi pi-trash" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Market;
