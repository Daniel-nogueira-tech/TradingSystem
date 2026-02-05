import React, { useContext, useMemo, useState } from 'react'
import './Graphics.css'
import Chart from '../MyChart/Chart '
import ChartRsi from '../MyChart/ChartRsi';
import ChartVppr from '../MyChart/ChartVppr';
import { AppContext } from '../../ContextApi/ContextApi';
import 'primeicons/primeicons.css';


const Graphics = () => {
  const { 
    dadosPrice,
    activeButton,
    handleClickTime,
    importantPoints,
    togglePivot,
    setRealTime,
    simulationValueDataComplete,
    windowSize,
    setWindowSize

  } = useContext(AppContext);
  const dadosTables = dadosPrice.reverse();
  const [currentPage, setCurrentPage] = useState(1);
  const [activeStates, setActiveStates] = useState({
    tendencia: false,
    rallyNatural: false,
    reacaoSec: false,
    rallySec: false,
    reacaoNatu: false
  });



  const itemsPerPage = 20;

  const activeTable = simulationValueDataComplete?.length > 0 ? simulationValueDataComplete : dadosTables;


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
    'Rally Natural (retorno)': 'Rally Natural',

    'Tendência Alta': 'Tendência Alta',
    'Tendência Alta (compra)': 'Tendência Alta',
    'Tendência Alta (topo)': 'Tendência Alta',

    'Tendência Baixa (venda)': 'Tendência Baixa',
    'Tendência Baixa (fundo)': 'Tendência Baixa',
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
    'Reação secundária (Alta)': 'Reação secundária',

    'Rally secundário (Topo)': 'Rally secundária',
    'Rally secundário (Fundo)': 'Rally secundária',
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



  // Paginação
  const linePage = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    return linhas.slice(start, end);
  }, [linhas, currentPage])



  // Ativa as botas de pivô
  const handleClick = (key, value) => {
    setActiveStates((prev) => ({
      ...prev,
      [key]: !prev[key], // inverte só o clicado
    }));
    togglePivot("Pivô", value);
  };


  ///


  return (
    <div className='graphics-main' >
      <div className='time-frame'>
        <div className='time-container'>

          <button
            className={`button-time ${activeButton === '15m'
              ? 'active'
              : ''}`}

            onClick={() => handleClickTime('15m')}
          >Short</button>

          <button
            className={`button-time ${activeButton === '1h'
              ? 'active'
              : ''}`}
            onClick={() => handleClickTime('1h')}
          >Swing</button>

          <button
            className={`button-time ${activeButton === '1d'
              ? 'active'
              : ''}`}
            onClick={() => handleClickTime('1d')}
          >Position</button>

          <button
            className="button-time"
            onClick={() => {
              setRealTime('realTimeMode');
              window.location.reload();
            }}
          >
            <span className="pi pi-sync"></span>
          </button>

          <div className='range'>
            <div className='sliderValue'>
              <span>{windowSize}</span>
            </div>
            <div className='field'>
              <div className='value left'></div>
              <input
                type="range"
                min={100}
                max={2000}
                step={100}
                value={windowSize}
                onChange={(e) => setWindowSize(Number(e.target.value))}
              />

            </div>
          </div>


        </div>
      </div>

      <div className='graphics'>
        <Chart />
      </div>
      <div className='graphics' id='graphics'>

        <div>
          <h3>Dados das operações</h3>
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

            </div>
            {/* tabela de dados do primeiro ativo */}

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
                  handleClick("reacaoNatural", importantPoints?.["Reação Natural"]?.price?.toFixed(2))
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
          </div>
        </div>
      </div>


      <div className='graphics' id='ChartRsi'>
        <ChartVppr />
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
      </div>
    </div >
  )
}

export default Graphics
