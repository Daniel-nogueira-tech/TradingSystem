import React, { useContext, useMemo, useState } from 'react'
import './Graphics.css'
import Chart from '../MyChart/Chart '
import ChartSecondary from '../MyChart/ChartSecondary'
import ChartBarKey from '../MyChart/ChartBarKey'
import { AppContext } from '../../ContextApi/ContextApi';

const Graphics = () => {
  const [value, setValue] = useState(500);
  const { dadosPrice, dadosPriceSecondary, dadosPriceKey, activeButton, handleClickTime, importantPoints, importantPointsKey, togglePivot, togglePivotKey, selectedPivotsKeys } = useContext(AppContext);
  const dadosTables = dadosPrice.reverse();
  const dadosTablesSec = dadosPriceSecondary.reverse();
  const dadosTablesKey = dadosPriceKey.reverse();
  const [currentPage, setCurrentPage] = useState(1);
  const [currentPage_2, setCurrentPage_2] = useState(1);
  const [currentPageKey, setCurrentPageKey] = useState(1);
  const [views, setViews] = useState('primario');
  const itemsPerPage = 20;
  const itemsPerPage_2 = 20;
  const itemsPerPageKey = 20;




  const movimentos = [
    "Rally secundária",
    "Rally natural",
    "Tendência Alta",
    "Tendência Baixa",
    "Reação natural",
    "Reação secundária",
  ]



  // Mapeamento caso haja pequenas diferenças de nomenclatura:
  const tipoToCol = {
    'Rally Natural (inicial)': 'Rally natural',
    'Rally Natural (fundo)': 'Rally natural',
    'Rally Natural (topo)': 'Rally natural',
    'Rally Natural (Baixa)': 'Rally natural',
    'Rally Natural (Alta)': 'Rally natural',
    'Rally Natural (retorno)': 'Rally natural',

    'Tendência Alta': 'Tendência Alta',
    'Tendência Alta (retomada)': 'Tendência Alta',
    'Tendência Alta (topo)': 'Tendência Alta',
    'Tendência Alta (reversão)': 'Tendência Alta',

    'Tendência Baixa (reversão)': 'Tendência Baixa',
    'Tendência Baixa (fundo)': 'Tendência Baixa',
    'Tendência Baixa (retomada)': 'Tendência Baixa',
    'Tendência Baixa': 'Tendência Baixa',

    'Reação Natural (topo)': 'Reação natural',
    "Reação Natural (fundo)": "Reação natural",
    'Reação Natural (de baixa)': 'Reação natural',
    'Reação Natural (Alta)': 'Reação natural',

    'Reação Natural (Baixa)': 'Reação natural',
    'Reação secundária': 'Reação secundária',
    'Reação secundária (Fundo)': 'Reação secundária',
    'Reação secundária (topo)': 'Reação secundária',
    'Reação secundária (retomada)': 'Reação secundária',

    'Rally secundária (Topo)': 'Rally secundária',
    'Rally secundária (Fundo)': 'Rally secundária',
    'Rally secundário (Alta)': 'Rally secundária',
    'Rally secundário (Baixa)': 'Rally secundária',
  };

  // Transforma os dados diretamente em linhas da tabela
  const linhas = useMemo(() => {
    return dadosTables.map(item => {
      const dataHora = new Date(item.closeTime).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });

      const movimentoFormatado = tipoToCol[item.tipo] || item.tipo;

      const linha = {
        dataHora,
        valores: movimentos.map(mov =>
          mov === movimentoFormatado ? item.closePrice : null
        )
      };

      return linha;
    });
  }, [dadosPrice]);


  // Transforma os dados diretamente em linhas da tabela secundaria
  const linhas_2 = useMemo(() => {
    return dadosTablesSec.map(item => {
      const dataHora = new Date(item.closeTime).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });

      const movimentoFormatado = tipoToCol[item.tipo] || item.tipo;

      const linha_2 = {
        dataHora,
        valores: movimentos.map(mov =>
          mov === movimentoFormatado ? item.closePrice : null
        )
      };

      return linha_2;
    });
  }, [dadosPriceSecondary]);

  // Transforma os dados diretamente em linhas da tabela Chave
  const linhasKey = useMemo(() => {
    return dadosTablesKey.map(item => {
      const dataHora = new Date(item.closeTime).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });

      const movimentoFormatado = tipoToCol[item.tipo] || item.tipo;

      const linhaKey = {
        dataHora,
        valores: movimentos.map(mov =>
          mov === movimentoFormatado ? item.closePrice : null
        )
      };

      return linhaKey;
    });
  }, [dadosPriceKey]);


  // Paginação
  const linePage = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    return linhas.slice(start, end);
  }, [linhas, currentPage])

  // Paginação segunda tabela
  const linePage_2 = useMemo(() => {
    const start = (currentPage_2 - 1) * itemsPerPage_2;
    const end = start + itemsPerPage_2;
    return linhas_2.slice(start, end);
  }, [linhas_2, currentPage_2])

  // Paginação segunda tabela
  const linePageKey = useMemo(() => {
    const start = (currentPageKey - 1) * itemsPerPageKey;
    const end = start + itemsPerPageKey;
    return linhasKey.slice(start, end);
  }, [linhasKey, currentPageKey])


  return (
    <div className='graphics-main' >
      <div className='time-frame'>

        <div className='time-container'>
          <button

            className={`button-time ${activeButton === '1h'
              ? 'active'
              : ''}`}
            onClick={() => handleClickTime('1h')}
          >1h</button>
          <button
            className={`button-time ${activeButton === '4h'
              ? 'active'
              : ''}`}

            onClick={() => handleClickTime('4h')}
          >4h</button>

          <button
            className={`button-time ${activeButton === '1d'
              ? 'active'
              : ''}`}
            onClick={() => handleClickTime('1d')}
          >1D</button>
        </div>

        <div className="slider-container">
          <label>Barras: {value}</label>
          <input
            type="range"
            min="500"
            max="5000"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="custom-slider"
          />
        </div>

      </div>

      <div className='graphics'>
        <Chart />
      </div>
      <div className='graphics'>
        <ChartSecondary />
      </div>
      <div className='graphics' id='graphics'>
        <ChartBarKey />
      </div>

      <div className='graphics' id='graphics'>

        <div>
          <h3>Dados da  operacao</h3>
          <div className='price' >
            <p> Ultimo preco: 330.524</p>
          </div>
          <div className='price' >
            <p> preco medio: 330.524</p>
          </div>
          <div className='price'>
            <p> Preco de comprar: 330.524</p>
          </div>
          <div className='price'>
            <p> Preco de stop: 330.524</p>
          </div>
          <div className='price'>
            <p> Preco de venda: 330.524</p>
          </div>
          <div className='price'>
            <p> Preco de stop: 330.524</p>
          </div>
        </div>

        <div>
          <h3>Pontos importantes</h3>
          <div>
            <div className='button-infor'>

              <button onClick={() => setViews('primario')}
                className={views === 'primario' ? 'activeButton' : ''
                }
              >Primario
              </button>

              <button onClick={() => setViews('chave')}
                className={views === 'chave' ? 'activeButton' : ''}
              >Chave</button>

            </div>
            {/* tabela de dados do primeiro ativo */}
            {views === 'primario' && (
              <div>
                <div className='price' onClick={() => togglePivot('Pivô' || 'activePivo', importantPoints?.["Tendência"]?.price)}>
                  <p>Tendência: {importantPoints?.["Tendência"]?.price.toFixed(2) ?? '---'}</p>
                </div>
                <div className='price' onClick={() => togglePivot('Pivô', importantPoints?.["Rally Natural"]?.price.toFixed(2))}>
                  <p> Rally Natural: {importantPoints?.["Rally Natural"]?.price.toFixed(2) ?? '---'}</p>
                </div>
                <div className='price' onClick={() => togglePivot('Pivô', importantPoints?.["Reação secundária"]?.price.toFixed(2))}>
                  <p>Rally secundária: {importantPoints?.["Reação secundária"]?.price.toFixed(2) ?? '---'}</p>
                </div>
                <div className='price' onClick={() => togglePivot('Pivô', importantPoints?.["Rally secundária"]?.price.toFixed(2))}>
                  <p>Reação secundária: {importantPoints?.["Rally secundária"]?.price.toFixed(2) ?? '---'}</p>
                </div>
              </div>
            )}

          </div>

          {views === 'chave' && (
            <div>
              <div className='price' onClick={() => togglePivotKey('Pivô' || 'activePivo', importantPointsKey?.["Tendência"]?.price)}>
                <p>Tendência: {importantPointsKey?.["Tendência"]?.price.toFixed(2) ?? '---'}</p>
              </div>
              <div className='price' onClick={() => togglePivotKey('Pivô', importantPointsKey?.["Rally Natural"]?.price)}>
                <p>Rally Natural: {importantPointsKey?.["Rally Natural"]?.price.toFixed(2) ?? '---'}</p>
              </div>
              <div className='price' onClick={() => togglePivotKey('Pivô', importantPointsKey?.["Reação secundária"]?.price)}>
                <p>Rally secundária: {importantPointsKey?.["Reação secundária"]?.price ?? '---'}</p>
              </div>
              <div className='price' onClick={() => togglePivotKey('Pivô', importantPointsKey?.["Rally secundária"]?.price)}>
                <p>Reação secundária: {importantPointsKey?.["Rally secundária"]?.price ?? '---'}</p>
              </div>
              
            </div>
          )}
        </div>
      </div>


      <div className='table-container'>
        <div>
          <h2 className='title-table'>Ativo Primário</h2>

          <table border="1" className='table'>
            <thead>
              <tr>
                <th>Data/Hora</th>
                {movimentos.map((mov, idx) => (
                  <th key={idx}>{mov}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {linePage.map((linha, i) => (
                <tr key={i}>
                  <td>{linha.dataHora}</td>
                  {linha.valores.map((valor, j) => (
                    <td key={j}>
                      {valor != null
                        ? Number(valor).toLocaleString('pt-EN', { style: 'currency', currency: 'USD' })
                        : ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>

          <div className="paginacao">
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
            >
              Anterior
            </button>
            <span>Página {currentPage}</span>
            <button
              onClick={() =>
                setCurrentPage(prev =>
                  prev * itemsPerPage < linhas.length ? prev + 1 : prev
                )
              }
              disabled={currentPage * itemsPerPage >= linhas.length}
            >
              Próxima
            </button>
          </div>

        </div>

        {/* Tabela secundário */}
        <div>
          <h2 className='title-table'>Ativo secundário</h2>
          <table border="1" className='table'>
            <thead>
              <tr>
                <th>Data/Hora</th>
                {movimentos.map((titulo, index) => (
                  <th key={index}>{titulo}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {linePage_2.map((linha_2, i) => (
                <tr key={i}>
                  <td>{linha_2.dataHora}</td>
                  {linha_2.valores.map((valor, j) => (
                    <td key={j}>
                      {valor != null
                        ? Number(valor).toLocaleString('pt-EN', { style: 'currency', currency: 'USD' })
                        : ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>

          <div className="paginacao">
            <button
              onClick={() => setCurrentPage_2(prev => Math.max(prev - 1, 1))}
              disabled={currentPage_2 === 1}
            >
              Anterior
            </button>
            <span>Página {currentPage_2}</span>
            <button
              onClick={() =>
                setCurrentPage_2(prev =>
                  prev * itemsPerPage_2 < linhas_2.length ? prev + 1 : prev
                )
              }
              disabled={currentPage_2 * itemsPerPage_2 >= linhas_2.length}
            >
              Próxima
            </button>
          </div>

        </div>
      </div>

      {/* Tabela de Preço chave */}

      <div className='table-container-key'>
        <h1 >Preço chave</h1>
        <table border="1">
          <thead>
            <tr>
              <th>Data/Hora</th>
              {movimentos.map((titulo, index) => (
                <th key={index}>{titulo}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {linePageKey.map((linhaKey, i) => (
              <tr key={i}>
                <td>{linhaKey.dataHora}</td>
                {linhaKey.valores.map((valor, j) => (
                  <td key={j}>
                    {valor != null
                      ? Number(valor).toLocaleString('pt-EN', { style: 'currency', currency: 'USD' })
                      : ''}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>

      </div>
      <div className="paginacao">
        <button
          onClick={() => setCurrentPageKey(prev => Math.max(prev - 1, 1))}
          disabled={currentPageKey === 1}
        >
          Anterior
        </button>
        <span>Página {currentPageKey}</span>
        <button
          onClick={() =>
            setCurrentPageKey(prev =>
              prev * itemsPerPageKey < linhasKey.length ? prev + 1 : prev
            )
          }
          disabled={currentPageKey * itemsPerPageKey >= linhasKey.length}
        >
          Próxima
        </button>
      </div>
    </div>
  )
}

export default Graphics
