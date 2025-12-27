import React, { useContext, useMemo, useState } from 'react'
import './Graphics.css'
import Chart from '../MyChart/Chart '
import ChartSecondary from '../MyChart/ChartSecondary'
import ChartBarKey from '../MyChart/ChartBarKey'
import ChartRsi from '../MyChart/ChartRsi'
import { AppContext } from '../../ContextApi/ContextApi';


const Graphics = () => {
  const { dadosPrice,
    dadosPriceSecondary,
    dadosPriceKey,
    activeButton,
    handleClickTime,
    importantPoints,
    importantPointsKey,
    togglePivot,
    togglePivotKey,
    setRealTime,
    simulationValueDataComplete,
    simulationValueDataCompleteSec,
    simulationValueDataCompleteKey,

  } = useContext(AppContext);
  const dadosTables = dadosPrice.reverse();
  const dadosTablesSec = dadosPriceSecondary.reverse();
  const dadosTablesKey = dadosPriceKey.reverse();
  const [currentPage, setCurrentPage] = useState(1);
  const [currentPage_2, setCurrentPage_2] = useState(1);
  const [currentPageKey, setCurrentPageKey] = useState(1);
  const [views, setViews] = useState('primario');
  const [activeStates, setActiveStates] = useState({
    tendencia: false,
    rallyNatural: false,
    reacaoSec: false,
    rallySec: false,
    reacaoNatu: false
  });
  const [activeStatesKey, setActiveStatesKey] = useState({
    tendencia: false,
    rallyNatural: false,
    reacaoSec: false,
    rallySec: false,
    reacaoNatu: false
  });

  const itemsPerPage = 20;
  const itemsPerPage_2 = 20;
  const itemsPerPageKey = 20;


  const activeTable = simulationValueDataComplete?.length > 0 ? simulationValueDataComplete : dadosTables;
  const activeTableSec = simulationValueDataCompleteSec?.length > 0 ? simulationValueDataCompleteSec : dadosTablesSec;
  const activeTableKey = simulationValueDataCompleteKey?.length > 0 ? simulationValueDataCompleteKey : dadosTablesKey;



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
    return activeTable.map(item => {
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
  }, [activeTable]);


  // Transforma os dados diretamente em linhas da tabela secundaria
  const linhas_2 = useMemo(() => {
    return activeTableSec.map(item => {
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
  }, [activeTableSec]);

  // Transforma os dados diretamente em linhas da tabela Chave
  const linhasKey = useMemo(() => {
    return activeTableKey.map(item => {
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
  }, [activeTableKey]);



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


  // Ativa as botas de pivô
  const handleClick = (key, value) => {
    setActiveStates((prev) => ({
      ...prev,
      [key]: !prev[key], // inverte só o clicado
    }));
    togglePivot("Pivô", value);
  };

  const handleClickKey = (key, value) => {
    setActiveStatesKey((prev) => ({
      ...prev,
      [key]: !prev[key], // inverte só o clicado
    }));
    togglePivotKey("Pivô", value);
  };


  return (
    <div className='graphics-main' >
      <div className='time-frame'>
        <div className='time-container'>

          <button
            className={`button-time ${activeButton === '15m'
              ? 'active'
              : ''}`}

            onClick={() => handleClickTime('15m')}
          >15M</button>

          <button
            className={`button-time ${activeButton === '1h'
              ? 'active'
              : ''}`}
            onClick={() => handleClickTime('1h')}
          >1H</button>

          <button
            className={`button-time ${activeButton === '1d'
              ? 'active'
              : ''}`}
            onClick={() => handleClickTime('1d')}
          >1D</button>

          <button
            className="button-time"
            onClick={() => {
              setRealTime('real');
              window.location.reload();
            }}
          >
            🔄 Atualizar
          </button>

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
          <h3>Dados das operações</h3>
          <div className='price' >
            <p>Ultimo preço: 330.524</p>
          </div>
          <div className='price' >
            <p>Preço médio: 330.524</p>
          </div>
          <div className='price'>
            <p>Preço de comprar: 330.524</p>
          </div>
          <div className='price'>
            <p>Preço de stop: 330.524</p>
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
                <div
                  className={`price ${activeStates.tendencia ? "active" : ""}`}
                  onClick={() => handleClick("tendencia", importantPoints?.["Tendência"]?.price)}
                >
                  <p>
                    Tendência: {importantPoints?.["Tendência"]?.price?.toFixed(2) ?? "---"}
                  </p>
                </div>

                <div
                  className={`price ${activeStates.rallyNatural ? "active" : ""}`}
                  onClick={() =>
                    handleClick("rallyNatural", importantPoints?.["Rally Natural"]?.price?.toFixed(2))
                  }
                >
                  <p>
                    Reação Natural: {importantPoints?.["Rally Natural"]?.price?.toFixed(2) ?? "---"}
                  </p>
                </div>

                <div
                  className={`price ${activeStates.reacaoNatu ? "active" : ""}`}
                  onClick={() =>
                    handleClick("reacaoNatu", importantPoints?.["Reação Natural"]?.price?.toFixed(2))
                  }
                >
                  <p>
                    Rally Natural: {importantPoints?.["Reação Natural"]?.price?.toFixed(2) ?? "---"}
                  </p>
                </div>

                <div
                  className={`price ${activeStates.reacaoSec ? "active" : ""}`}
                  onClick={() =>
                    handleClick("reacaoSec", importantPoints?.["Reação secundária"]?.price?.toFixed(2))
                  }
                >
                  <p>
                    Reação secundária: {importantPoints?.["Reação secundária"]?.price?.toFixed(2) ?? "---"}
                  </p>
                </div>

                <div
                  className={`price ${activeStates.rallySec ? "active" : ""}`}
                  onClick={() =>
                    handleClick("rallySec", importantPoints?.["Rally secundária"]?.price?.toFixed(2))
                  }
                >
                  <p>
                    Rally secundária: {importantPoints?.["Rally secundária"]?.price?.toFixed(2) ?? "---"}
                  </p>
                </div>
              </div>
            )}

          </div>


          {views === 'chave' && (
            <div>
              <div
                className={`price ${activeStatesKey.tendencia ? "active" : ""}`}
                onClick={() => handleClickKey("tendencia", importantPointsKey?.["Tendência"]?.price)}
              >
                <p>
                  Tendência: {importantPointsKey?.["Tendência"]?.price?.toFixed(2) ?? "---"}
                </p>
              </div>

              <div
                className={`price ${activeStatesKey.rallyNatural ? "active" : ""}`}
                onClick={() =>
                  handleClickKey("rallyNatural", importantPointsKey?.["Rally Natural"]?.price?.toFixed(2))
                }
              >
                <p>
                  Reação Natural: {importantPointsKey?.["Rally Natural"]?.price?.toFixed(2) ?? "---"}
                </p>
              </div>

              <div
                className={`price ${activeStatesKey.reacaoNatu ? "active" : ""}`}
                onClick={() =>
                  handleClickKey("reacaoNatu", importantPointsKey?.["Reação Natural"]?.price?.toFixed(2))
                }
              >
                <p>
                  Rally Natural: {importantPointsKey?.["Reação Natural"]?.price?.toFixed(2) ?? "---"}
                </p>
              </div>

              <div
                className={`price ${activeStatesKey.reacaoSec ? "active" : ""}`}
                onClick={() =>
                  handleClickKey("reacaoSec", importantPointsKey?.["Reação secundária"]?.price?.toFixed(2))
                }
              >
                <p>
                  Reação secundária: {importantPointsKey?.["Reação secundária"]?.price?.toFixed(2) ?? "---"}
                </p>
              </div>

              <div
                className={`price ${activeStatesKey.rallySec ? "active" : ""}`}
                onClick={() =>
                  handleClickKey("rallySec", importantPointsKey?.["Rally secundária"]?.price?.toFixed(2))
                }
              >
                <p>
                  Rally secundária: {importantPointsKey?.["Rally secundária"]?.price?.toFixed(2) ?? "---"}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className='graphics' id='ChartRsi'>
        <ChartRsi />
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
    </div >
  )
}

export default Graphics
