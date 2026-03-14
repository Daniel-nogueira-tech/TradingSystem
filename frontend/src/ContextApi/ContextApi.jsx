import React, { createContext, use, useEffect, useRef, useState } from 'react';
import Swal from 'sweetalert2';
import axios from 'axios';
import { Toast } from 'primereact/toast';
import { BsRobot } from "react-icons/bs";
import { ProgressSpinner } from 'primereact/progressspinner';
import 'primereact/resources/themes/lara-dark-indigo/theme.css';
import 'primereact/resources/primereact.min.css';
import { useMemo } from 'react';




export const AppContext = createContext();


const ContextApi = (props) => {
  const url = "http://localhost:5000";
  const [theme, setTheme] = useState(() => { return localStorage.getItem('theme') || 'dark'; });
  const [windowSize, setWindowSize] = useState(1000);
  const [atr, setAtr] = useState([]);// usado na regra de cores no Chart.jsx
  const [dadosPrice, setDadosPrice] = useState([]); // DADOS completos do ativo primária (open, close, high, low, volume, etc)
  const [vpprComplete, setVpprComplete] = useState([]); // Dados completos do VPPR (valor, ema, etc) para análise detalhada
  const [rsiComplete, setRsiComplete] = useState([]); // Dados completos do RSI (valor, amrsi, rsi_ma) para análise detalhada
  const [candlesComplete, setCandlesComplete] = useState([]) // Dados completos com candles
  const inputRefMain = useRef(null);
  const [symbol, setSymbol] = useState(() => {
    return localStorage.getItem('symbol') || "";
  });
  useEffect(() => {
    if (symbol) {
      localStorage.setItem('symbol', symbol);
    }
  }, [symbol]);
  const toast = useRef(null);
  const [activeButton, setActiveButton] = useState('1h');
  const [importantPoints, setImportantPoints] = useState([]);
  const [selectedPivots, setSelectedPivots] = useState([]);
  const [realTime, setRealTime] = useState(() => {
    return localStorage.getItem("realTimeMode") || "simulation";
  });
  const [timeCurrent, setTimeCurrent] = useState(() => {
    return localStorage.getItem('timeCurrent') || "";
  });
  // whenever timeCurrent is updated, persist locally
  useEffect(() => {
    if (timeCurrent) {
      localStorage.setItem('timeCurrent', timeCurrent);
    }
  }, [timeCurrent]);
  const modo = realTime;
  const [rsi, setRsi] = useState([]);
  const [rsiTime, setRsiTime] = useState([]);
  const [vppr, setVppr] = useState([]);
  const [vpprTime, setVpprTime] = useState([]);
  const [vpprEma, setVpprEma] = useState([]);
  const [addSymbol, setAddSymbol] = React.useState('');
  const [removeSymbol, setRemoveSymbol] = React.useState('')
  const [data, setData] = React.useState([]);
  const [loadingSimulation, setLoadingSimulation] = useState(false);
  const [downloadedData, setDownloadedData] = useState(false);
  const [dataCorrelation, setDataCorrelation] = useState([])
  const [assetCorrelationData, setAssetCorrelationData] = useState([]);

  const timeoutRef = useRef(null);

  // Variáveis para controle incremental dos dados (Gráficos)
  const fullDataRef = useRef([]);
  const indexRef = useRef(0);
  const intervalRef = useRef(null);

  // Variáveis para controle incremental dos dados do VPPR (Indicador)
  const fullDataVpprRef = useRef([]);
  const indexVpprRef = useRef(0);
  const intervalVpprRef = useRef(null);

  // Variáveis para controle incremental dos dados do RSI (Indicador)
  const fullDataRsiRef = useRef([]);
  const indexRsiRef = useRef(0);
  const intervalRsiRef = useRef(null);
  const timeoutRsiRef = useRef(null); // usada no novo motor recursivo

  // Variáveis para controle incremental dos dados do VPPR (Indicador)
  const fullDataCandlesRef = useRef([]);
  const indexCandlesRef = useRef(0);
  const intervalCandlesRef = useRef(null);



  // Delta-tracking refs para evitar reprocessar dados históricos em modo real-time
  const lastProcessedTimestampRef = useRef(null); // para price
  const lastProcessedTimestampRsiRef = useRef(null); // para RSI
  const lastProcessedTimestampVpprRef = useRef(null); // para VPPR
  const lastProcessedTimestampCandlesRef = useRef(null); // para candles

  // Global loading (reference-counted) — use para mostrar um único loading enquanto múltiplos fetches ocorrem
  const [globalLoadingCount, setGlobalLoadingCount] = useState(0);
  const isGlobalLoading = globalLoadingCount > 0;
  const startGlobalLoading = () => setGlobalLoadingCount(c => c + 1);
  const stopGlobalLoading = () => setGlobalLoadingCount(c => Math.max(0, c - 1));
  const runWithGlobalLoading = async (fn) => {
    startGlobalLoading();
    try {
      return await fn();
    } finally {
      stopGlobalLoading();
    }
  };

  const [dateSimulationStart, setDateSimulationStart] = useState("")
  const [dateSimulationEnd, setDateSimulationEnd] = useState("")
  const [days, setDays] = useState('')
  const [showDaysInput, setShowDaysInput] = useState(false);
  const [daysValue, setDaysValue] = useState('');

  /*-------------------------------------------------------------------------------------
                      Variáveis para atualizar graficos
  ---------------------------------------------------------------------------------------*/
  const [simulationLabelData, setSimulationLabelData] = useState([]);
  const [simulationValueData, setSimulationValueData] = useState([]);

  const [simulationLabelDataRsi, setSimulationLabelDataRsi] = useState([]);
  const [simulationValueDataRsi, setSimulationValueDataRsi] = useState([]);

  const [simulationLabelDataVppr, setSimulationLabelDataVppr] = useState([]);
  const [simulationValueDataVppr, setSimulationValueDataVppr] = useState([]);
  const [simulationValueDataVpprEma, setSimulationValueDataVpprEma] = useState([]);

  const [simulationValueDataComplete, setSimulationValueDataComplete] = useState([]);
  const [simulationValueDataCompleteRsi, setSimulationValueDataCompleteRsi] = useState([]);
  const [simulationValueDataCompleteVppr, setSimulationValueDataCompleteVppr] = useState([]);

  // Estados para armazenar confirmações de compra e venda
  const [simulationCandleComplete, setSimulationCandleComplete] = useState([]);
  const [simulationCandleValue, setSimulationCandleValue] = useState([]);
  const [simulationCandleLabel, setSimulationCandleLabel] = useState([]);

  /**----------------------------------------//--------------------------------------------------- 
   * //////////////////////////////////////////////////////////////////////////////////////////
   * ----------------------------------------//---------------------------------------------------*/


  /**--------------------------------------------------
   *        Variáveis para pausar a simulação 
   * --------------------------------------------------*/
  const simulationTimeoutRef = useRef(null);
  const [isPaused, setIsPaused] = useState(true);
  const isPausedRef = useRef(isPaused);

  const simulationTimeoutSyncRef = useRef(null);
  const simulationRsiTimeoutRef = useRef(null);
  const [isPausedRsi, setIsPausedRsi] = useState(false);
  const isPausedRsiRef = useRef(isPausedRsi);

  const simulationVpprTimeoutRef = useRef(null);
  const [isPausedVppr, setIsPausedVppr] = useState(false);
  const isPausedVpprRef = useRef(isPausedVppr);

  const simulationCandleTimeoutRef = useRef(null);
  const [isPausedCandle, setIspausedCandle] = useState(false);
  const isPausedCandleRef = useRef(isPausedCandle);
  /**-----------------------//-------------------------
   * /////////////////////////////////////////////////
   *------------------------//-------------------------*/

  // Variáveis de controle para simulação
  const simulationControllerRef = useRef(null);
  // OffSet para controlar simulação
  const offsetRefPrimary = useRef(0);
  const offsetRefRsi = useRef(0);
  const offsetRefVppr = useRef(0);
  const offsetRefCandle = useRef(0);
  const period = 14; /* periodo do AMRSI */

  // Variável de referência para usar no toast
  const toastShownRef = useRef(false);

  const checkEndOfIncrement = useRef(false);



  /*-------------------------------------------------------------------
    Função para atualizar na alternância entre simulação e real time 
  ---------------------------------------------------------------------*/
  const LoadGraphicDataOne = async (savedSymbol) => {
    if (!savedSymbol) return;
    if (realTime === "realTimeMode") {
      await graphicDataOne(savedSymbol);
      await getRsi(savedSymbol);
      await getVppr(savedSymbol);
      await graphicCandles();

      if (!toastShownRef.current) {
        toast.current.show({
          severity: "success",
          summary: "Modo",
          detail: "Welcome, Next Atom Loaded!",
          life: 1500
        });
        toastShownRef.current = true;
      }
    }
    else if (realTime === "simulation") {
      await getRsi();
      await getVppr();
      await graphicCandles();
      await simulateStepSync(savedSymbol);
      toast.current.show({
        severity: "success",
        summary: "Modo",
        detail: "Simulação",
        life: 1500
      });
    }
    else {
      console.warn("Modo inválido:", realTime);
    }
  };

  // --------------------------------////------------------------------------------//

  // --------------------------------////------------------------------------------//

  // --------------------------------////------------------------------------------///
  /*#####################################################################
                         1️⃣📈INICIO ATIVO PRIMÁRIA CANDLE📈1️⃣
  ########################################################################*/

  // Função principal modificada
  const processingCandlesRef = useRef();
  const binanceWsRef = useRef(null);

  // Função principal modificada
  const graphicCandles = async () => {
    if (modo === "simulation") return;

    // Cancela processamento anterior
    if (processingCandlesRef.current) {
      cancelAnimationFrame(processingCandlesRef.current);
      processingCandlesRef.current = null;
    }

    // Fecha WebSocket existente se houver
    if (binanceWsRef.current) {
      binanceWsRef.current.close();
      binanceWsRef.current = null;
    }

    try {
      // 1. CARREGA DADOS HISTÓRICOS DA API
      const response = await axios.get(`${url}/api/complete_data_candle`);
      const historicalData = response.data;

      if (!Array.isArray(historicalData)) return;

      // Processa e ordena os dados históricos
      const sortedHistoricalData = processHistoricalData(historicalData);

      // Armazena no ref e atualiza o estado
      fullDataCandlesRef.current = sortedHistoricalData;

      if (modo === "realTimeMode") {
        setCandlesComplete(sortedHistoricalData);
      } else {
        setCandlesComplete([]);
        resetBuffer();
        return;
      }

      // 2. INICIA CONEXÃO WEBSOCKET COM BINANCE
      setupBinanceWebSocket(sortedHistoricalData);

    } catch (error) {
      console.error("❌ Erro ao buscar dados:", error);
    }
  };

  // Função para processar dados históricos
  const processHistoricalData = (data) => {
    const len = data.length;
    const timestamps = new Uint32Array(len);

    // Processa em chunks
    const CHUNK_SIZE = 5000;
    for (let i = 0; i < len; i += CHUNK_SIZE) {
      const end = Math.min(i + CHUNK_SIZE, len);
      setTimeout(() => { }, 0);

      for (let j = i; j < end; j++) {
        const candle = data[j];
        // Verifica se já está no formato correto
        timestamps[j] = new Date(candle.tempo.replace(' ', 'T')).getTime() / 1000;
      }
    }

    // Ordenação
    const indices = new Uint32Array(len);
    for (let i = 0; i < len; i++) indices[i] = i;
    indices.sort((a, b) => timestamps[a] - timestamps[b]);

    // Reconstrói array ordenado (já deve estar com open, high, low, close)
    const sorted = new Array(len);
    for (let i = 0; i < len; i++) {
      sorted[i] = data[indices[i]];
    }

    return sorted;
  };


  // Configuração do WebSocket da Binance
  const setupBinanceWebSocket = (historicalData) => {
    // Parâmetros do WebSocket 
    if (!symbol || !timeCurrent) {
      console.error("❌ symbol ou timeCurrent não definidos");
      return;
    }

    // Binance exige símbolo em minúsculas
    const tradingSymbol = symbol.toLowerCase();
    const interval = timeCurrent;


    const wsUrl = `wss://stream.binance.com:9443/ws/${tradingSymbol}@kline_${interval}`;

    binanceWsRef.current = new WebSocket(wsUrl);

    binanceWsRef.current.onopen = () => {
      console.log('✅ WebSocket Binance conectado para', tradingSymbol, interval);
    };

    binanceWsRef.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        // Processa o candle recebido para o SEU formato
        const newCandle = processBinanceCandle(message);

        // Atualiza os dados com o novo candle
        updateCandlesWithRealTimeData(newCandle);

      } catch (error) {
        console.error('❌ Erro ao processar mensagem WebSocket:', error);
      }
    };

    binanceWsRef.current.onerror = (error) => {
      console.error('❌ Erro no WebSocket:', error);
    };

    binanceWsRef.current.onclose = () => {
      console.log('🔌 WebSocket desconectado');

      // Tenta reconectar após 5 segundos
      setTimeout(() => {
        if (modo === "realTimeMode" && fullDataCandlesRef.current) {
          console.log('🔄 Tentando reconectar WebSocket...');
          setupBinanceWebSocket(fullDataCandlesRef.current);
        }
      }, 5000);
    };
  };

  // Processa o candle da Binance para o SEU formato - CORRIGIDO
  const processBinanceCandle = (message) => {
    const k = message.k;

    // Formata a data
    const date = new Date(k.t);
    const formattedTime = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:00`;

    // Retorna com os nomes CORRETOS (open, high, low, close)
    return {
      tempo: formattedTime,
      open: parseFloat(k.o) || 0,
      high: parseFloat(k.h) || 0,
      low: parseFloat(k.l) || 0,
      close: parseFloat(k.c) || 0,
      volume: parseFloat(k.v) || 0
    };
  };

  // Atualiza os candles com dados em tempo real - CORRIGIDO
  const updateCandlesWithRealTimeData = (newCandle) => {
    if (!fullDataCandlesRef.current || fullDataCandlesRef.current.length === 0) {
      console.log('⚠️ Nenhum dado histórico disponível');
      return;
    }

    // Pega o último candle do array histórico
    const currentData = fullDataCandlesRef.current;
    const lastHistoricalCandle = currentData[currentData.length - 1];


    // Se for o mesmo minuto, ATUALIZA o último candle
    if (newCandle.tempo === lastHistoricalCandle.tempo) {

      // IMPORTANTE: Preserva a abertura (open) original do histórico!
      const openOriginal = lastHistoricalCandle.open;

      // Garante que estamos trabalhando com números
      const currentHigh = Number(lastHistoricalCandle.high) || 0;
      const currentLow = Number(lastHistoricalCandle.low) || 0;
      const newHigh = Number(newCandle.high) || 0;
      const newLow = Number(newCandle.low) || 0;
      const newClose = Number(newCandle.close) || 0;
      const newVolume = Number(newCandle.volume) || 0;

      // Calcula nova máxima e mínima
      const highAtualizada = Math.max(currentHigh, newHigh, newClose);
      const lowAtualizada = Math.min(currentLow, newLow, newClose);

      // Cria um novo array com o último candle atualizado
      const updatedData = [...currentData];
      updatedData[updatedData.length - 1] = {
        tempo: lastHistoricalCandle.tempo,
        open: openOriginal,           // ← MANTÉM o nome 'open'
        high: highAtualizada,          // ← MANTÉM o nome 'high'
        low: lowAtualizada,            // ← MANTÉM o nome 'low'
        close: newClose,               // ← MANTÉM o nome 'close'
        volume: newVolume               // ← MANTÉM o nome 'volume'
      };

      // Atualiza o ref e o estado
      fullDataCandlesRef.current = updatedData;
      setCandlesComplete(updatedData);
    }
    // Se for um minuto novo, ADICIONA ao final
    else if (newCandle.tempo > lastHistoricalCandle.tempo) {

      // Garante que o novo candle use os nomes corretos (open, high, low, close)
      const novoCandleFormatado = {
        tempo: newCandle.tempo,
        open: Number(newCandle.open) || 0,
        high: Number(newCandle.high) || 0,
        low: Number(newCandle.low) || 0,
        close: Number(newCandle.close) || 0,
        volume: Number(newCandle.volume) || 0
      };

      const updatedData = [...currentData, novoCandleFormatado];
      fullDataCandlesRef.current = updatedData;
      setCandlesComplete(updatedData);
    }
    else {
      console.log('⏭️ Ignorando candle antigo:', newCandle.tempo);
    }
  };
  // Limpeza na saída do componente
  useEffect(() => {
    return () => {
      if (binanceWsRef.current) {
        binanceWsRef.current.close();
      }
    };
  }, []);

  // --------------------------------////------------------------------------------//

  // --------------------------------////------------------------------------------//

  // --------------------------------////------------------------------------------///

  /*#### #################################################################
                                ///////////
  ########################################################################*/
  // --------------------------------////------------------------------------------//

  // --------------------------------////------------------------------------------//

  // --------------------------------////------------------------------------------///

  /*#####################################################################
                         1️⃣📈INICIO ATIVO PRIMÁRIA📈1️⃣
  ########################################################################*/
  /*------------------------------------------------------------------
              1️⃣ Função para buscar dados do ativo Primária
   -------------------------------------------------------------------*/
  // Use uma estrutura de buffer circular em vez de array dinâmico
  const MAX_CANDLES_ONE = 2000;
  const BufferOneRef = useRef(new Array(MAX_CANDLES_ONE));
  const bufferStartOneRef = useRef(0);
  const bufferLengthOneRef = useRef(0);
  const processingRef = useRef(false);

  // Função para adicionar candle ao buffer
  const addToBufferOne = (candle) => {
    const buffer = BufferOneRef.current;
    const pos = (bufferStartOneRef.current + bufferLengthOneRef.current) % MAX_CANDLES_ONE;
    buffer[pos] = candle;

    if (bufferLengthOneRef.current === MAX_CANDLES_ONE) {
      bufferStartOneRef.current = (bufferStartOneRef.current + 1) % MAX_CANDLES_ONE;
    } else {
      bufferLengthOneRef.current++;
    }
  };

  // Função para adicionar múltiplos candles ao buffer
  const addBatchToBufferOne = (candles) => {
    candles.forEach(candle => addToBufferOne(candle));
  };

  // Função para obter array atual
  const getCurrentOne = () => {
    const result = [];
    const buffer = BufferOneRef.current;
    for (let i = 0; i < bufferLengthOneRef.current; i++) {
      result.push(buffer[(bufferStartOneRef.current + i) % MAX_CANDLES_ONE]);
    }
    return result;
  };

  const graphicDataOne = async (symbol) => {
    if (!symbol || modo === "simulation") return;

    clearTimeout(simulationTimeoutRef.current);

    try {
      const response = await axios.get(`${url}/api/filter_price_atr?symbol=${symbol}`);
      const data = response.data;


      if (!Array.isArray(data) || data.length === 0) return;

      const len = data.length;
      const CHUNK_SIZE = 5000;

      // Pré-alocação
      const timestamps = new Uint32Array(len);

      // Processamento em chunks
      for (let i = 0; i < len; i += CHUNK_SIZE) {
        const end = Math.min(i + CHUNK_SIZE, len);

        // Permite que a UI atualize entre chunks
        await new Promise(resolve => setTimeout(resolve, 0));

        // Processa apenas o chunk atual
        for (let j = i; j < end; j++) {
          const candle = data[j];
          timestamps[j] = new Date(candle.closeTime.replace(' ', 'T')).getTime();
        }
      }

      const atrLast = Number(data[len - 1].limite);

      // Atualiza estados
      setAtr(atrLast);

      // Guarda dados ordenados
      fullDataRef.current = data;

      // Reseta o buffer
      bufferStartOneRef.current = 0;
      bufferLengthOneRef.current = 0;
      indexRef.current = 0;

      if (modo !== "realTimeMode") {
        setDadosPrice([]);
      } else {
        setDadosPrice(getCurrentOne())
      }

    } catch (error) {
      console.error("❌ Erro ao buscar dados:", error);
    } finally {
      startIncrementalFeed(10);
    }
  };

  // Motor incremental otimizado
  const startIncrementalFeed = (speed = 1) => {
    if (modo === 'simulation' || processingRef.current) return;

    try {
      // Limpa intervalo anterior se existir
      if (intervalRef.current?.clear) {
        intervalRef.current.clear();
      }

      processingRef.current = true;

      // Delta-tracking otimizado com busca binária
      if (modo === "realTimeMode" && lastProcessedTimestampRef.current) {
        const lastTs = new Date(lastProcessedTimestampRef.current).getTime();
        const data = fullDataRef.current;

        // ✅ Busca binária (mais rápida que findIndex)
        let left = 0;
        let right = data.length - 1;

        while (left <= right) {
          const mid = Math.floor((left + right) / 2);
          const midTs = new Date(data[mid].closeTime).getTime();

          if (midTs <= lastTs) {
            left = mid + 1;
          } else {
            right = mid - 1;
          }
        }

        indexRef.current = left;

        if (indexRef.current >= data.length) {
          console.log("✅ Nenhum dado novo para processar");
          processingRef.current = false;
          return;
        }

        console.log(`🚀 Delta-tracking: pulando para índice ${indexRef.current}`);
      } else {
        indexRef.current = 0;
      }

      // Processa em batches
      const BATCH_SIZE = Math.max(1, Math.floor(speed)); // Garante que seja pelo menos 1
      let frameId;

      const processBatch = () => {
        if (indexRef.current >= fullDataRef.current.length) {
          // Final do processamento
          if (fullDataRef.current.length > 0) {
            lastProcessedTimestampRef.current =
              fullDataRef.current[fullDataRef.current.length - 1].closeTime;
            console.log("💾 Último timestamp processado:", lastProcessedTimestampRef.current);
          }
          console.log("✅ Fim da análise incremental");
          processingRef.current = false;
          return;
        }

        // Processa um lote
        const endIdx = Math.min(
          indexRef.current + BATCH_SIZE,
          fullDataRef.current.length
        );

        // ✅ CORRIGIDO: Adiciona lote ao buffer
        for (let i = indexRef.current; i < endIdx; i++) {
          addToBufferOne(fullDataRef.current[i]);
        }

        // ✅ CORRIGIDO: Atualiza estado com função e parênteses
        setDadosPrice(getCurrentOne());

        // ✅ CORRIGIDO: Atualiza índice corretamente
        indexRef.current = endIdx;

        // Agenda próximo lote
        if (indexRef.current < fullDataRef.current.length) {
          frameId = requestAnimationFrame(processBatch);
        } else {
          processingRef.current = false;
        }
      };

      // Inicia processamento
      frameId = requestAnimationFrame(processBatch);

      // Cleanup
      intervalRef.current = {
        current: frameId,
        clear: () => {
          if (frameId) {
            cancelAnimationFrame(frameId);
          }
          processingRef.current = false;
        }
      };

    } catch (error) {
      console.error("Erro no feed incremental:", error);
      processingRef.current = false;
    }
  };

  // Worker (opcional, se precisar)
  const workerOneRef = useRef(null);

  useEffect(() => {
    // Só cria worker se suportado e se ainda não existe
    if (window.Worker && !workerOneRef.current) {
      try {
        workerOneRef.current = new Worker('/candleWorkerOne.js');
        workerOneRef.current.onmessage = (e) => {
          const { type, data, lastTimestamp } = e.data;

          if (type === 'newData' && data?.length > 0) {
            requestAnimationFrame(() => {
              addBatchToBufferOne(data);
              setDadosPrice(getCurrentOne());
              if (lastTimestamp) {
                lastProcessedTimestampRef.current = lastTimestamp;
              }
            });
          }
        };
      } catch (error) {
        console.error("Erro ao criar worker:", error);
      }
    }

    return () => {
      if (workerOneRef.current) {
        workerOneRef.current.terminate();
        workerOneRef.current = null;
      }
    };
  }, []);

  // --------------------------------////------------------------------------------//

  // --------------------------------////------------------------------------------//

  // --------------------------------////------------------------------------------///

  /*--------------------------------------------------------------------
    🔍1️⃣ Faz pequisa do simbolo envia para backend (do ativo primária)
    --------------------------------------------------------------------*/
  const handleSearch = async (event) => {
    event?.preventDefault();
    inputRefMain.current.focus();

    const searchedSymbol = inputRefMain.current.value.toUpperCase();
    if (!searchedSymbol) return;
    try {
      const response = await axios.get(`${url}/api/filter_price_atr?symbol=${searchedSymbol}`);
      const data = response.data;

      // 🔥 ORDENA os dados também em handleSearch
      const sortedData = [...data].sort((a, b) => {
        const timeA = new Date(a.closeTime.replace(" ", "T")).getTime();
        const timeB = new Date(b.closeTime.replace(" ", "T")).getTime();
        return timeA - timeB;
      });

      const prices = sortedData.map(p => parseFloat(p.closePrice));
      const time = sortedData.map(p => p.closeTime);

      setDadosPrice(sortedData);
      setSymbol(searchedSymbol);
      timeframeToMs()

      // ✅ Toast de sucesso
      toast.current.show({
        severity: "success",
        summary: 'Busca realizada',
        detail: `Símbolo ${searchedSymbol} carregado com sucesso!`,
        life: 5000
      });
    } catch (error) {
      // ❌ Toast de erro
      toast.current.show({
        severity: 'error',
        summary: 'Erro na busca',
        detail: `Não foi possível buscar o símbolo: ${searchedSymbol}`,
        life: 5000
      });

      console.error('Erro ao buscar dados:', error);
    }
    inputRefMain.current.value = "";
  };
  /*------------------------------------//----------------------------------------
   * //////////////////////////////////////////////////////////////////////////
   -------------------------------------//---------------------------------------*/
  /*-------------------------------------------------------------------
                    🔍1️⃣ Busca o simbolo Primária
   --------------------------------------------------------------------*/
  const getSymbol = async () => {
    // Try backend first
    try {
      const response = await axios.get(url + "/api/last_symbol");
      const data = response.data;
      if (data && data.symbol) {
        setSymbol(data.symbol);
        return data.symbol;
      }
    } catch (error) {
      console.error("Erro na API para recuperar símbolos:", error);
    }
    // fallback to localStorage if available
    const stored = localStorage.getItem('symbol');
    if (stored) {
      setSymbol(stored);
      return stored;
    }
    return null;
  };
  /**-------------------------------//---------------------------------
   * ////////////////////////////////////////////////////////////////
   ---------------------------------//---------------------------------*/
  /*#####################################################################
                               ###########
  ########################################################################*/




  /*#####################################################################
                           1️⃣💰INICIA SIMULAÇÃO💰1️⃣
  ######################################################################### */
  /*--------------------------------------------------------------
         1️⃣ Busca as datas da simulação do ativo Primária
   ---------------------------------------------------------------*/
  const getDateSimulation = async () => {
    try {
      const response = await axios.get(`${url}/api/get_date/simulation`);
      const data = response.data;
      setDays(data.days || '');
      setDateSimulationStart(data.days_start || '')
      setDateSimulationEnd(data.days_end || '')

    } catch (error) {
      console.error("Erro na API para recuperar datas:", error);
    }
  }
  /**-----------------------------//---------------------------------
   * //////////////////////////////////////////////////////////////
   -------------------------------//---------------------------------*/
  /*----------------------------------------------------
      Função para simulação pega os dados fatiados
   -----------------------------------------------------*/
  const simulateStepSync = async (symbolPrimary) => {
    if (!symbolPrimary) return;
    // se não estiver em modo simulation, cancela
    if (realTime !== 'simulation') {
      console.log("🛑 Simulação cancelada: modo não é 'simulation'");
      return;
    }
    // cancela timeout anterior
    clearTimeout(simulationTimeoutSyncRef.current);

    try {
      // Cria novo AbortController para esta iteração
      if (simulationControllerRef.current) {
        simulationControllerRef.current.abort();
      }
      simulationControllerRef.current = new AbortController();
      const signal = simulationControllerRef.current.signal;
      const fetchOne = async (endpoint, offset) => {
        const resp = await axios.get(`${endpoint}?offset=${offset}&limit=100`, { signal });
        return (resp.data && resp.data.length) ? resp.data[0] : null;
      };

      // endpoints mantidos
      const epPrimary = `${url}/api/simulate_price_atr`;
      const epRsi = `${url}/api/simulate_amrsi`;
      const epVppr = `${url}/api/simulate_vppr`;
      const epDadosCandles = `${url}/api/simulate_full`;


      // pausa global do primary
      if (isPausedRef.current) {
        simulationTimeoutSyncRef.current = setTimeout(
          () => simulateStepSync(symbolPrimary),
          300
        );
        return;
      }

      // 🔹 PRIMARY (driver do tempo)
      let candleP = await fetchOne(epPrimary, offsetRefPrimary.current);
      if (!candleP) {
        console.log("✅ Simulação finalizada (primary terminou)");
        return;
      }

      const dateP = candleP.closeTime;
      const tp = new Date(dateP).getTime();

      setSimulationValueData(prev => {
        const next = [...prev, parseFloat(candleP.closePrice)];
        return next.length > 2000 ? next.slice(- 2000) : next;
      });
      setSimulationLabelData(prev => {
        const next = [...prev, candleP.closeTime];
        return next.length > 2000 ? next.slice(- 2000) : next;
      });
      setSimulationValueDataComplete(prev => {
        const next = [...prev, candleP];
        return next.length > 2000 ? next.slice(- 2000) : next;
      });

      offsetRefPrimary.current += 1;

      // 🔹 Confirmações sincronizadas ao primary (processa até tp)
      // durante o processamento das confirmações iremos atualizar os estados imediatamente,
      // não acumularemos arrays locais. Isso garante que simulationCandleComplete cresça de
      while (true) {
        if (isPausedCandleRef.current) {
          console.log("⏸️ Pausado durante processamento das confirmações. Retomando depois...");
          // re-agenda a simulação e sai; não mexemos nos dados adicionais
          simulationTimeoutSyncRef.current = setTimeout(
            () => simulateStepSync(symbolPrimary),
            300
          );
          return;
        }

        // busca próxima confirmação pelo offset atual
        let candles = await fetchOne(epDadosCandles, offsetRefCandle.current);

        if (!candles) {
          break; // não há mais confirmações para esta iteração
        }

        // o valor de tempo vem no campo 'tempo' (texto ou timestamp);
        // comparar usando essa data para saber se devemos processar
        const dateConf = candles.tempo;
        const tConf = new Date(dateConf).getTime();
        if (tConf > tp) {
          break; // confirmação adiantada, interrompe o loop
        }

        // atualiza os três estados de uma vez como nos outros dados
        setSimulationCandleValue(prev => {
          const next = [...prev, parseFloat(candles.close)];
          return next.length > 2000 ? next.slice(-2000) : next;
        });
        setSimulationCandleLabel(prev => {
          const next = [...prev, candles.tempo];
          return next.length > 2000 ? next.slice(-2000) : next;
        });
        setSimulationCandleComplete(prev => {
          const next = [...prev, candles];
          return next.length > 2000 ? next.slice(-2000) : next;
        });

        offsetRefCandle.current += 1;
      }
      // Não é necessário aplicar um batch final – já inserimos cada candle dentro do loop.


      // 🔹 RSI sincronizado ao primary (fetch em batch, processa até tp)
      const rsiBatchValues = [];
      const rsiBatchLabels = [];
      const rsiBatchComplete = [];

      while (true) {
        if (isPausedRsiRef.current) {
          console.log("⏸️ Pausado durante processamento do RSI. Retomando depois...");
          // Aplica batch antes de pausar
          if (rsiBatchValues.length) {
            setSimulationValueDataRsi(prev => {
              const next = [...prev, ...rsiBatchValues];
              return next.length > 2000 ? next.slice(-2000) : next;
            });
            setSimulationLabelDataRsi(prev => {
              const next = [...prev, ...rsiBatchLabels];
              return next.length > 2000 ? next.slice(-2000) : next;
            });
            setSimulationValueDataCompleteRsi(prev => {
              const next = [...prev, ...rsiBatchComplete];
              return next.length > 2000 ? next.slice(-2000) : next;
            });
          }
          simulationTimeoutSyncRef.current = setTimeout(
            () => simulateStepSync(symbolPrimary),
            300
          );
          return;
        }

        let candleRsi = await fetchOne(epRsi, offsetRefRsi.current);

        if (!candleRsi) {
          break;
        }

        // próximo é depois, para sem avançar
        const dateRsi = candleRsi.time;
        const tRsi = new Date(dateRsi).getTime();

        if (tRsi > tp) {
          break;
        }
        const value =
          candleRsi.amrsi ??
          candleRsi.rsi_ma ??
          candleRsi.rsi;

        rsiBatchValues.push(parseFloat(value));
        rsiBatchLabels.push(candleRsi.time);
        rsiBatchComplete.push(candleRsi);

        // avança para o próximo (offset alinhado com limit=100)
        offsetRefRsi.current += 1;
      }

      // Aplica batch RSI ao final do loop
      if (rsiBatchValues.length) {
        setSimulationValueDataRsi(prev => {
          const next = [...prev, ...rsiBatchValues];
          return next.length > 2000 ? next.slice(-2000) : next;
        });
        setSimulationLabelDataRsi(prev => {
          const next = [...prev, ...rsiBatchLabels];
          return next.length > 2000 ? next.slice(-2000) : next;
        });
        setSimulationValueDataCompleteRsi(prev => {
          const next = [...prev, ...rsiBatchComplete];
          return next.length > 2000 ? next.slice(-2000) : next;
        });
      }

      // 🔹 VPPR sincronizado ao primary (fetch em batch, processa até tp)
      const vpprBatchValues = [];
      const vpprBatchLabels = [];
      const vpprBatchComplete = [];
      const vpprBatchEma = [];

      while (true) {
        if (isPausedVpprRef.current) {
          console.log("⏸️ Pausado durante processamento do Vppr. Retomando depois...");
          // Aplica batch antes de pausar
          if (vpprBatchValues.length) {
            setSimulationValueDataVppr(prev => {
              const next = [...prev, ...vpprBatchValues];
              return next.length > 2000 ? next.slice(-2000) : next;
            });
            setSimulationLabelDataVppr(prev => {
              const next = [...prev, ...vpprBatchLabels];
              return next.length > 2000 ? next.slice(-2000) : next;
            });
            setSimulationValueDataCompleteVppr(prev => {
              const next = [...prev, ...vpprBatchComplete];
              return next.length > 2000 ? next.slice(-2000) : next;
            });
            setSimulationValueDataVpprEma(prev => {
              const next = [...prev, ...vpprBatchEma];
              return next.length > 2000 ? next.slice(-2000) : next;
            });
          }
          simulationTimeoutSyncRef.current = setTimeout(
            () => simulateStepSync(symbolPrimary), 300
          );
          return;
        }
        // pega o próximo candle (driver)
        let candleVppr = await fetchOne(epVppr, offsetRefVppr.current);

        if (!candleVppr) {
          console.log("✅ Simulação finalizada (Vppr terminou)");
          // Aplica batch final antes de terminar
          if (vpprBatchValues.length) {
            setSimulationValueDataVppr(prev => {
              const next = [...prev, ...vpprBatchValues];
              return next.length > 2000 ? next.slice(-2000) : next;
            });
            setSimulationLabelDataVppr(prev => {
              const next = [...prev, ...vpprBatchLabels];
              return next.length > 2000 ? next.slice(-2000) : next;
            });
            setSimulationValueDataCompleteVppr(prev => {
              const next = [...prev, ...vpprBatchComplete];
              return next.length > 2000 ? next.slice(-2000) : next;
            });
            setSimulationValueDataVpprEma(prev => {
              const next = [...prev, ...vpprBatchEma];
              return next.length > 2000 ? next.slice(-2000) : next;
            });
          }
          return;
        }

        // data (somente parte data "YYYY-MM-DD" para sincronização por data)
        let dateVppr = candleVppr.time;
        const tVppr = new Date(dateVppr).getTime();

        if (tVppr > tp) {
          break;
        }

        // Acumula no batch local
        vpprBatchValues.push(parseFloat(candleVppr.vppr));
        vpprBatchLabels.push(candleVppr.time);
        vpprBatchComplete.push(candleVppr);
        vpprBatchEma.push(candleVppr.vppr_ema);

        // avança para o próximo (offset alinhado com limit=100)
        offsetRefVppr.current += 1;
      }

      // Aplica batch VPPR ao final do loop
      if (vpprBatchValues.length) {
        setSimulationValueDataVppr(prev => {
          const next = [...prev, ...vpprBatchValues];
          return next.length > 2000 ? next.slice(-2000) : next;
        });
        setSimulationLabelDataVppr(prev => {
          const next = [...prev, ...vpprBatchLabels];
          return next.length > 2000 ? next.slice(-2000) : next;
        });
        setSimulationValueDataCompleteVppr(prev => {
          const next = [...prev, ...vpprBatchComplete];
          return next.length > 2000 ? next.slice(-2000) : next;
        });
        setSimulationValueDataVpprEma(prev => {
          const next = [...prev, ...vpprBatchEma];
          return next.length > 2000 ? next.slice(-2000) : next;
        });
      }

      // agenda próxima iteração
      simulationTimeoutSyncRef.current = setTimeout(() => {
        simulateStepSync(symbolPrimary);
      }, 300);

    } catch (error) {
      if (error.name !== 'CanceledError') {
        console.error("❌ Erro na simulateStepSync:", error);
      }
      clearTimeout(simulationTimeoutSyncRef.current);
      if (simulationControllerRef.current) {
        simulationControllerRef.current.abort();
      }
    }
  };



  /**-------------------------------//-----------------------------------------
   * ////////////////////////////////////////////////////////////////////////
   ---------------------------------//-----------------------------------------*/
  /*-----------------------------------------------------------------------
    1️⃣ Função para (BAIXAR) dados simulação (envia as datas para o backend)
   -------------------------------------------------------------------------*/
  const dateSimulation = async () => {
    if (loadingSimulation) return;
    setLoadingSimulation(true);
    setDownloadedData(false);
    try {
      const response = await axios.post(`${url}/api/update_klines`, {},
        {
          params: {
            date_start: dateSimulationStart,
            date_end: dateSimulationEnd,
            days: daysValue,
            symbol: symbol
          }
        }
      );
      const res = await axios.post(`${url}/api/update_klines_correlation`, {},
        {
          params: {
            date_start: dateSimulationStart,
            date_end: dateSimulationEnd,
            days: daysValue,
            symbol: symbol
          }
        }
      );

      // 🔹Chamada da API para enviar o modo para simular a classificação
      await axios.post(`${url}/api/filter_price_atr?symbol=${symbol}&modo=${modo}`);
      await axios.get(`${url}/api/rsi?period=${period}&symbol=${symbol}&modo=${modo}`);
      await axios.get(`${url}/api/vppr?symbol=${symbol}&modo=${modo}`);

      getDateSimulation();

      if (response.data?.mensagem || res.data?.mensagem) {
        // ✅ Toast de sucesso
        toast.current.show({
          severity: "success",
          summary: 'Sucesso!',
          detail: `Os dados para simular foram baixados!`,
          life: 5000
        });
      }
      setDownloadedData(true);
    } catch (error) {
      // ❌ Toast de erro
      toast.current.show({
        severity: 'error',
        summary: 'Erro',
        detail: `Não é possível baixar dados para simular`,
        life: 5000
      });
      console.error("Erro na API de atualização de datas:", error.response?.data || error.message);
    } finally {
      setLoadingSimulation(false);
    }
  }
  /**-------------------------------------------//----------------------------------------------------
   * ///////////////////////////////////////////////////////////////////////////////////////////////
   ---------------------------------------------//----------------------------------------------------*/
  /*###################################################################################################
                                       1️⃣💰FIM DA SIMULAÇÃO💰1️⃣
  ######################################################################################################*/


  /**######################################################################################################
   *                                       TIME FRAME
   ########################################################################################################*/
  /*--------------------------------------------------------------------------------------------
     🗓 Salva o tempo gráfico que vai ser usando com os dados analisados (envia para o backend)
  ----------------------------------------------------------------------------------------------*/
  const handleClickTime = async (time) => {
    if (!time) return;
    // pega o tempo gráfico atualizado para garantir sincronia
    clearTimeout(timeoutRef.current);
    clearInterval(intervalRef.current);
    const result = await Swal.fire({
      title: 'Você quer mesmo alterar?',
      text: "O time frame será mudado!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      cancelButtonText: "Cancelar",
      confirmButtonText: "Sim, mudar!",
      customClass: {
        popup: 'fundo-preto',
        title: 'titulo-branco',
        content: 'texto-branco',
        confirmButton: 'botao-verde',
      }
    });
    if (result.isConfirmed) {
      try {
        const response = await axios.post(`${url}/api/timeframe`, {
          time: time
        });
        const data = response.data;
        setTimeCurrent(data.time);
        setActiveButton(data.time);
        handleGetPoints();
        graphicDataOne(symbol);
        getRsi(symbol);
        getVppr(symbol);

        Swal.fire({
          title: "Alterado!",
          text: "O time frame foi atualizado com sucesso!",
          icon: "success",
          customClass: {
            popup: 'fundo-preto',
            title: 'titulo-branco',
            content: 'texto-branco',
            confirmButton: 'botao-verde',
          }
        });

        /** Atualiza obeservação de mercado após trocar time frame*/
        const res = await axios.get(`${url}/api/update_market_observations`);
        if (res.data?.updated_symbols) {
          const successful = res.data.updated_symbols.filter(u => u.status === 'atualizado').length;
          console.log(`✅ ${successful} observações de mercado atualizadas após adicionar novo símbolo`);
        }

      } catch (error) {
        Swal.fire({
          title: "Erro!",
          text: "Não foi possível atualizar o timeframe.",
          icon: "error",
          customClass: {
            popup: 'fundo-preto',
            title: 'titulo-branco',
            content: 'texto-branco',
            confirmButton: 'botao-verde',
          }
        });
        console.error("Erro ao enviar timeframe:", error);
      }
    }
  };
  /**--------------------------------------------//------------------------------------------------
   * ////////////////////////////////////////////////////////////////////////////////////////////
   ----------------------------------------------//-------------------------------------------------*/
  /*--------------------------------------------------------------
     🔄Pega o tempo gráfico salvo no banco para uso no front end
  ----------------------------------------------------------------*/
  const handleGetTime = async () => {
    try {
      const response = await axios.get(`${url}/api/timeframe`);
      const data = response.data;

      if (data.time) {
        setActiveButton(data.time);
      }
    } catch (error) {
      console.error("Erro ao buscar timeframe:", error);
    }
  };
  /**-------------------------------//-----------------------------------
   * //////////////////////////////////////////////////////////////////
   ---------------------------------//----------------------------------*/
  /**######################################################################################################
   *                                       ###########
   ########################################################################################################*/
  /*#######################################################################################################
   *                                  PONTOS PIVÔS
    #######################################################################################################*/
  /*------------------------------------------------------------------
               Pega os pontos de pivot importantes
  --------------------------------------------------------------------*/
  const handleGetPoints = async () => {
    try {
      const response = await axios.get(`${url}/api/trend_clarifications`);
      const data = response.data;
      if (data) {
        setImportantPoints(data)
      }
    } catch (error) {
      console.error("Erro ao buscar ponto importante:", error);
    }
  }
  /**-----------------------------------//---------------------------------------------------------
   * /////////////////////////////////////////////////////////////////////////////////////////////
   -------------------------------------//---------------------------------------------------------*/
  /*-----------------------------------------------------------------------
                   Função para adicionar/remover pivôs
  --------------------------------------------------------------------------*/
  const togglePivot = (label, price) => {
    setSelectedPivots(prev => {
      const exists = prev.find(p => p.valor === price && p.texto === label);
      if (exists) {
        return prev.filter(p => !(p.valor === price && p.texto === label));
      } else {
        return [...prev, { valor: price, texto: label, cor: 'white' }];
      }
    });
  };
  /*---------------------------------//-----------------------------------------------------------------
    //////////////////////////////////////////////////////////////////////////////////////////////////
  -----------------------------------//-----------------------------------------------------------------*/
  /*#######################################################################################################
   *                                          #######
    #######################################################################################################*/


  /**############################################################################
   *                             INDICADORES
   ############################################################################*/
  /*---------------------------------------------------------------------------
                    Função para pegar dados do calculo rsi
  ------------------------------------------------------------------------------*/
  // Use uma estrutura de buffer circular em vez de array dinâmico
  const MAX_CANDLES_RSI = 2000;
  const rsiBufferRef = useRef(new Array(MAX_CANDLES_RSI));
  const bufferStartRsiRef = useRef(0);
  const bufferLengthRsiRef = useRef(0);

  // Função para adicionar candle ao buffer
  const addRsiToBuffer = (candle) => {
    const buffer = rsiBufferRef.current;
    const pos = (bufferStartRsiRef.current + bufferLengthRsiRef.current) % MAX_CANDLES_RSI;

    buffer[pos] = candle;

    if (bufferLengthRsiRef.current === MAX_CANDLES_RSI) {
      bufferStartRsiRef.current = (bufferStartRsiRef.current + 1) % MAX_CANDLES_RSI;
    } else {
      bufferLengthRsiRef.current++;
    }
  };

  // Função para obter array atual (chamada apenas quando necessário)
  const getCurrentRsi = () => {
    const result = [];
    const buffer = rsiBufferRef.current;
    for (let i = 0; i < bufferLengthRsiRef.current; i++) {
      result.push(buffer[(bufferStartRsiRef.current + i) % MAX_CANDLES_RSI]);
    }
    return result;
  };

  //-----------------------------------------------------------------------//
  const getRsi = async (symbol) => {
    if (!symbol || !modo || !period) {
      return;
    };

    try {
      const response = await axios.get(
        `${url}/api/rsi?period=${period}&symbol=${symbol}&modo=${modo}`
      );
      const data = response.data;
      if (!Array.isArray(data)) {
        console.warn("Dados do RSI não são um array:", data);
        return;
      }
      const len = data.length;
      // Pré-alocação (rápido e cache-friendly)
      let value = new Float64Array(len);
      let timestamps = new Uint32Array(len);

      // Processa em chunks para não travar a UI
      const CHUNK_SIZE = 5000;
      for (let i = 0; i < len; i += CHUNK_SIZE) {
        const end = Math.min(i + CHUNK_SIZE, len);

        // Permite que a UI atualize entre chunks
        await new Promise(resolve => setTimeout(resolve, 0));

        for (let j = i; j < end; j++) {
          const candle = data[j];
          value[j] = Number(candle.rsi_ma);
          timestamps[j] = new Date(candle.time.replace(' ', 'T')).getTime();
        }
      };

      setRsi(Array.from(value));
      setRsiTime(timestamps);

      fullDataRsiRef.current = data;
      indexRsiRef.current = 0;

      // Reseta buffer   
      bufferLengthRsiRef.current = 0;
      bufferStartRsiRef.current = 0;

      // Em modo realTimeMode, NÃO limpa dados anteriores (mantém histórico)
      // Em modo simulação, limpa para começar do zero
      if (modo !== "realTimeMode") {
        setRsiComplete([]);
      } else {
        // Em realTimeMode, mantém o buffer atual
        setRsiComplete(getCurrentRsi());
      }

    } catch (error) {
      console.error("Erro ao buscar dados do RSI", error);
    } finally {
      startIncrementalFeedRsi() // velocidade maior para evitar acúmulo de updates
    }
  };
  //-------------------------------------------------------------------------------------------------//
  // Motor incremental para alimentar os gráficos gradualmente, evitando travamentos e permitindo simulação fluida
  const startIncrementalFeedRsi = (speed = 5) => {
    if (modo === 'simulation') return; // incremental feed é apenas para real-time, simulação tem motor próprio
    // cancela qualquer execução anterior
    clearTimeout(timeoutRsiRef.current);

    if (intervalRsiRef.current?.clear) {
      intervalRsiRef.current.clear();
      intervalRsiRef.current = null;
    }

    // ⚡ Delta-tracking: se já processamos dados antes, pule os dados antigos
    if (modo === "realTimeMode" && lastProcessedTimestampRsiRef.current) {
      const lastTs = new Date(lastProcessedTimestampRsiRef.current).getTime();

      const startIdx = fullDataRsiRef.current.findIndex(
        candle => new Date(candle.time).getTime() > lastTs
      );
      if (startIdx === -1) {
        return;
      }
      indexRsiRef.current = startIdx;
      console.log(`🚀 Delta-tracking (RSI): pulando para índice ${startIdx}, processando apenas dados novos.`);
    } else {
      indexRsiRef.current = 0;
    }

    // Processa em batches para reduzir renders
    const BATCH_SIZE = speed;
    let frameId;

    const processBatch = () => {
      if (indexRsiRef.current >= fullDataRsiRef.current.length) {
        // 💾 Salva o último timestamp processado para próxima iteração
        if (fullDataRsiRef.current.length > 0) {
          lastProcessedTimestampRsiRef.current = fullDataRsiRef.current[fullDataRsiRef.current.length - 1].time;
          console.log("💾 Último timestamp processado (RSI):", lastProcessedTimestampRsiRef.current);
        }
        checkEndOfIncrement.current = true;
        console.log("checkEndOfIncrement", checkEndOfIncrement.current);

        console.log("✅ Fim da analise incremental: todos os dados foram processados.");
        return;
      }

      // Processa um lote de candles
      const endIdx = Math.min(
        indexRsiRef.current + BATCH_SIZE,
        fullDataRsiRef.current.length
      );

      // Adiciona todos ao buffer
      for (let i = indexRsiRef.current; i < endIdx; i++) {
        addRsiToBuffer(fullDataRsiRef.current[i]);
      }

      // Única atualização de estado para o lote
      setRsiComplete(getCurrentRsi());


      indexRsiRef.current = endIdx;

      // Agenda próximo lote
      if (indexRsiRef.current < fullDataRsiRef.current.length) {
        frameId = requestAnimationFrame(processBatch);
      }
    };
    // Inicia processamento
    frameId = requestAnimationFrame(processBatch);

    // Cleanup
    intervalRsiRef.current = {
      current: frameId,
      clear: () => cancelAnimationFrame(frameId)
    };
  };

  // --------------------------------////------------------------------------------//

  // --------------------------------////------------------------------------------//

  // --------------------------------////------------------------------------------///

  /*--------------------------------------------------------------------------
   * Função para pegar dados do calculo  vppr (Volume Price Pressure Ratio) 
   ---------------------------------------------------------------------------*/
  // Use uma estrutura de buffer circular em vez de array dinâmico
  const MAX_CANDLES = 2000;
  const vpprBufferRef = useRef(new Array(MAX_CANDLES));
  const bufferStartVpprRef = useRef(0);
  const bufferLengthVpprRef = useRef(0);

  // Função para adicionar candle ao buffer
  const addVpprToBuffer = (candle) => {
    const buffer = vpprBufferRef.current;
    const pos = (bufferStartVpprRef.current + bufferLengthVpprRef.current) % MAX_CANDLES;

    buffer[pos] = candle;

    if (bufferLengthVpprRef.current === MAX_CANDLES) {
      bufferStartVpprRef.current = (bufferStartVpprRef.current + 1) % MAX_CANDLES;
    } else {
      bufferLengthVpprRef.current++;
    }
  };

  // Função para obter array atual (chamada apenas quando necessário)
  const getCurrentVppr = () => {
    const result = [];
    const buffer = vpprBufferRef.current;
    for (let i = 0; i < bufferLengthVpprRef.current; i++) {
      result.push(buffer[(bufferStartVpprRef.current + i) % MAX_CANDLES]);
    }
    return result;
  };
  //-----------------------------------------------------------------------------------//
  const controllerRef = useRef(null);
  const getVppr = async (symbol) => {
    if (!symbol) return;

    if (controllerRef.current) controllerRef.current.abort();
    controllerRef.current = new AbortController();


    try {
      const { data } = await axios.get(
        `${url}/api/vppr`,
        {
          params: { symbol, modo },
          signal: controllerRef.current.signal
        }
      );

      if (!Array.isArray(data)) return;

      // Otimização: processa em chunks com TypedArrays
      const len = data.length;
      const value = new Float64Array(len);
      const timestamps = new Uint32Array(len);
      const ema = new Float64Array(len);

      // Processa em chunks para não travar a UI
      const CHUNK_SIZE = 5000;
      for (let i = 0; i < len; i += CHUNK_SIZE) {
        const end = Math.min(i + CHUNK_SIZE, len);

        // Permite que a UI atualize entre chunks
        await new Promise(resolve => setTimeout(resolve, 0));

        for (let j = i; j < end; j++) {
          const v = data[j];
          value[j] = Number(v.vppr);
          ema[j] = Number(v.vppr_ema);
          timestamps[j] = new Date(v.time.replace(' ', 'T')).getTime() / 1000;
        }
      }

      setVppr(value)
      setVpprTime(timestamps)
      setVpprEma(ema)


      // guarda tudo internamente
      fullDataVpprRef.current = data;
      indexVpprRef.current = 0;


      // Em modo realTimeMode, NÃO limpa dados anteriores (mantém histórico)
      // Em modo simulação, limpa para começar do zero
      if (modo !== "realTimeMode") {
        setVpprComplete([]);
      } else {
        setVpprComplete(getCurrentVppr());
      }

    } catch (error) {
      console.error("Erro ao buscar dados do VPPR", error);
    } finally {
      startIncrementalFeedVppr(5);
    }
  }

  // Motor incremental para alimentar os gráficos gradualmente, evitando travamentos e permitindo simulação fluida
  const startIncrementalFeedVppr = (speed = 5) => {
    if (modo === 'simulation') return; // incremental feed é apenas para real-time, simulação tem motor próprio
    try {
      intervalVpprRef.current?.clear?.();

      // ⚡ Delta-tracking: se já processamos dados antes, pule os dados antigos
      if (modo === "realTimeMode" && lastProcessedTimestampVpprRef.current) {
        const lastTs = new Date(lastProcessedTimestampVpprRef.current).getTime();

        const startIdx = fullDataVpprRef.current.findIndex(
          candle => new Date(candle.time).getTime() > lastTs
        );
        if (startIdx === -1) {
          console.log("✅ Nenhum dado novo para processar em modo real-time (VPPR).");
          return;
        }
        indexVpprRef.current = startIdx;
        console.log(`🚀 Delta-tracking (VPPR): pulando para índice ${startIdx}, processando apenas dados novos.`);
      } else {
        indexVpprRef.current = 0;
      }

      // Processa em batches para reduzir renders
      const BATCH_SIZE = speed;
      let frameId;

      const processBatch = () => {
        if (indexVpprRef.current >= fullDataVpprRef.current.length) {
          if (fullDataVpprRef.current.length > 0) {
            lastProcessedTimestampVpprRef.current =
              fullDataVpprRef.current[fullDataVpprRef.current.length - 1].time;
          }
          return;
        }

        const endIdx = Math.min(
          indexVpprRef.current + BATCH_SIZE,
          fullDataVpprRef.current.length
        );

        for (let i = indexVpprRef.current; i < endIdx; i++) {
          addVpprToBuffer(fullDataVpprRef.current[i]);
        }

        setVpprComplete(getCurrentVppr());

        indexVpprRef.current = endIdx;

        if (indexVpprRef.current < fullDataVpprRef.current.length) {
          frameId = requestAnimationFrame(processBatch);
        }
      };
      // Inicia processamento
      frameId = requestAnimationFrame(processBatch);

      // Cleanup
      intervalVpprRef.current = {
        current: frameId,
        clear: () => cancelAnimationFrame(frameId)
      };

    } catch (error) {
      console.error("Erro no feed incremental:", error);
    }
  };

  // No componente principal
  const workerVpprRef = useRef(null);

  useEffect(() => {
    workerVpprRef.current = new Worker('/candleWorkerVppr.js');
    workerVpprRef.current.onmessage = (e) => {
      const { type, data, lastTimestamp } = e.data;

      if (type === 'newData' && data.length > 0) {
        // Processa dados em batches no próximo frame
        requestAnimationFrame(() => {
          data.forEach(candle => addVpprToBuffer(candle));
          setVpprComplete(getCurrentVppr());
          lastProcessedTimestampVpprRef.current = lastTimestamp;
        });
      }
    };

    return () => workerVpprRef.current?.terminate();
  }, []);


  /**-------------------------------------------------------------------
   * //////////////////////////////////////////////////////////////////
   ----------------------------------------------------------------------*/
  /**############################################################################
   *                             ##############
   ############################################################################*/


  /**####################################################################
   *                       OBSERVAÇÂO DE MERCADO
   ######################################################################*/
  /**------------------------------------------------------------
   * Função para salvar observações de mercado no banco de dados
   --------------------------------------------------------------*/
  const [marketObservation, setMarketObservation] = useState([]);
  const [marketObservationComplete, setMarketObservationComplete] = useState([]);
  const saveMarketNotes = async () => {
    if (!addSymbol || !addSymbol.trim()) {
      console.warn("⏭️ Requisição ignorada: símbolo vazio");
      return;
    }

    try {
      const { data } = await axios.post(`${url}/api/market_observation`, {
        symbol: addSymbol.trim().toUpperCase(),
        total: 2000,
      });
      toast.current.show({
        severity: "success",
        summary: "Sucesso!",
        detail: `Símbolo adicionado: ${addSymbol}`,
        life: 5000
      });

      setAddSymbol('');
      correlation();
      getMarketObservation();

      // 🔄 Atualiza imediatamente todos os símbolos salvos
      try {
        const response = await axios.get(`${url}/api/update_market_observations`);
        if (response.data?.updated_symbols) {
          const successful = response.data.updated_symbols.filter(u => u.status === 'atualizado').length;
          console.log(`✅ ${successful} observações de mercado atualizadas após adicionar novo símbolo`);
        }
      } catch (updateError) {
        console.warn("⚠️ Erro ao atualizar observações de mercado:", updateError.response?.data || updateError.message);
      }
    } catch (error) {
      console.error("Erro:", error);
    }
  };
  /**----------------------------------------------------------------------------------------------------------------
   * ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
   -------------------------------------------------------------------------------------------------------------------*/
  /**----------------------------------------------------------------------------------
   *         Pega os dados para observação de mercado (APENAS OS MAIS RECENTES)
   * ----------------------------------------------------------------------------------*/
  const getMarketObservation = async () => {
    try {
      const response = await axios.get(`${url}/api/latest_market_observation`);
      setMarketObservation(response.data);
    } catch (error) {
      console.error("Erro ao buscar observações de mercado:", error);
    }
  };


  //Função para remover símbolo da observação de mercado
  const handleRemoveSymbol = async (symbol) => {
    if (!symbol) {
      return;
    };
    try {
      const response = await axios.post(`${url}/api/remove_symbol_market_observation`, {
        symbol: symbol
      });
      const data = response.data

      if (data) {
        setData(prev =>
          prev.filter(item => item.symbol !== symbol)
        );
        // ✅ Toast de sucesso
        toast.current.show({
          severity: "success",
          summary: "Modo",
          detail: `símbolo removido! ${symbol}`,
          life: 1500
        });
      }
      correlation(); // atualiza lista de correlação
    } catch (error) {
      // ❌ Toast de erro
      toast.current.show({
        severity: 'error',
        summary: '',
        detail: `Erro ao remover símbolo! ${symbol}`,
        life: 5000
      });
      console.error("Erro ao buscar observações de mercado:", error);
    }
  };
  /**-------------------------------------------------------------------------------
   * /////////////////////////////////////////////////////////////////////////////
   ---------------------------------------------------------------------------------*/
  /**---------------------------------------------------------------------------------
   *          Pega os dados para observação de mercado (DADOS COMPLETOS)
   -----------------------------------------------------------------------------------*/
  const getMarketObservationComplete = async (symbol) => {
    if (!symbol) return;
    try {
      const response = await axios.post(`${url}/api/get_market_observation`, {
        symbol: symbol
      });
      const data = response.data.data;
      setMarketObservationComplete(data);
    } catch (error) {
      console.error("Erro ao buscar observações de mercado:", error);
    }
  };
  const handleSave = () => {
    Swal.fire({
      title: 'Você vai Salvar',
      text: "As configurações do aplicativo!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      cancelButtonText: "Cancelar",
      confirmButtonText: "Sim, Salvar!",
      customClass: {
        popup: 'fundo-preto',
        title: 'titulo-branco',
        content: 'texto-branco',
        confirmButton: 'botao-verde',
      }
    }).then((result) => {
      if (result.isConfirmed) {
        Swal.fire({
          title: "Salvo!",
          text: "Configurações salvas.",
          icon: "success",
          customClass: {
            popup: 'fundo-preto',
            title: 'titulo-branco',
            content: 'texto-branco',
            confirmButton: 'botao-verde',
          }
        });
      }
    });
  };
  /**------------------------------------------------------------------------
   * //////////////////////////////////////////////////////////////////////
   --------------------------------------------------------------------------*/
  /**####################################################################
   *                          ################
   ######################################################################*/

  /**####################################################################
*                       CORRELAÇÃO DE MERCADO
######################################################################*/
  /**------------------------------------------------------------------------
   *                   Função para pegar correlação
   --------------------------------------------------------------------------*/
  const correlation = async () => {
    try {
      const response = await axios.get(`${url}/api/get_correlation`);
      const data = response.data;
      setDataCorrelation(data);
    } catch (error) {
      console.error("Erro ao buscar dados sobre correlações:", error);
    }
  };
  /**------------------------------------------------------------------------
    * //////////////////////////////////////////////////////////////////////
    --------------------------------------------------------------------------*/

  const assetCorrelation = async (symbol) => {
    try {
      const response = await axios.get(`${url}/api/get_symbols_with_correlation?symbol=${symbol}`);
      const data = response.data;
      setAssetCorrelationData(data);
    } catch (error) {
      console.log("Erro ao buscar dados sobre correlações do ativo:", error)
    }
  };


  /**####################################################################
   *                          ################
   ######################################################################*/
  /**------------------------------------------------------------------------
   *                   Função para remover Chaves de api
   --------------------------------------------------------------------------*/
  const handleRemove = () => {
    Swal.fire({
      title: 'Você querer Remover',
      text: "A chave?",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      cancelButtonText: "Cancelar",
      confirmButtonText: "Sim, Remover!",
      customClass: {
        popup: 'fundo-preto',
        title: 'titulo-branco',
        content: 'texto-branco',
        confirmButton: 'botao-verde',
      }
    }).then((result) => {
      if (result.isConfirmed) {
        Swal.fire({
          title: "A chave foi removida",
          text: "Com sucesso!",
          icon: "success",
          customClass: {
            popup: 'fundo-preto',
            title: 'titulo-branco',
            content: 'texto-branco',
            confirmButton: 'botao-verde',
          }
        });
      }
    })
  };
  /**---------------------------------------------------------------------
   * ////////////////////////////////////////////////////////////////////
   ------------------------------------------------------------------------*/

  /**-----------------------------------------------------------------------
   *               Mudar tema e salvar no localStorage
   --------------------------------------------------------------------------*/
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark' || 'very-dark-theme';
    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, []);
  useEffect(() => {
    if (theme === 'clear-theme') {
      document.body.classList.remove('dark');
      document.body.classList.remove('very-dark-theme');
      document.body.classList.add('clear-theme');

    } else if (theme === 'dark') {
      document.body.classList.remove('clear-theme');
      document.body.classList.remove('very-dark-theme');
      document.body.classList.add('dark');

    } else if (theme === 'very-dark-theme') {
      document.body.classList.remove('clear-theme');
      document.body.classList.remove('dark');
      document.body.classList.add('very-dark-theme');
    }

    localStorage.setItem('theme', theme);
  }, [theme]);
  /**--------------------------------------------------------------------
   * ///////////////////////////////////////////////////////////////////
   ----------------------------------------------------------------------*/
  /*#######################################################################
              🎯logica de compra e venda início🎯 OPERAÇÃO REAL
  ########################################################################*/


  /*#######################################################################
                          🎯logica de compra e venda início🎯 OPERAÇÃO
  ########################################################################*/

  // Estado para armazenar o último topo anterior
  const [ultimoTopoAnterior, setUltimoTopoAnterior] = useState(null);
  const [ultimoPivoAnterior, setUltimoPivoAnterior] = useState(null);
  const [ultimoPivoAtual, setultimoPivoAtual] = useState(null);
  const [ultimoPivoSec, setUltimoPivoSec] = useState(null);
  const [penultimoValor, setPenultimoValor] = useState([]);
  const [rallyPivot, setRallyPivot] = useState([]);
  const [rallyPivotSec, setRallyPivotSec] = useState([]);
  const [ultimoPivoAnteriorRally, setUltimoPivoAnteriorRally] = useState(null);
  const [ultimoPivoAnteriorRallySec, setUltimoPivoAnteriorRallySec] = useState(null);
  const [retestPoints, setRetestPoints] = useState([]);
  const [currentTrend, setCurrentTrend] = useState("");
  const [trendFound, setTrendFound] = useState(null);
  const [trendPivotToRetest, setTrendPivotToRetest] = useState([]);
  const [enteringTheTrendUpdate, setEnteringTheTrendUpdate] = useState(null);
  const [rallySecExitUpdate, setRallySecExitUpdate] = useState([]);

  // variaveis para evitar reprocessamento
  const lastTrendRetestIdRef = useRef(null);
  const lastTrendExitIdRef = useRef(null);
  const lastRallyRetestIdRef = useRef(null);
  const lastRallyRetestIdPrimaryRef = useRef(null);
  const lastRallyExitIdRef = useRef(null);
  const lastSecondaryExitIdRef = useRef(null);
  const lastBreakoutIdRef = useRef(null);
  const canExecuteRallyRef = useRef(false);
  const canExecuteReactionRef = useRef(false);
  const canExecuteReactionSecRef = useRef(false);
  const canExecuteRallySecRef = useRef(false);


  const movements = useMemo(() => {
    if (modo === "realTimeMode") {
      return dadosPrice;
    }
    return simulationValueDataComplete;
  }, [dadosPrice, simulationValueDataComplete, modo]);


  useEffect(() => {
    // dados de classificação simulados 
    if (!movements || movements.length === 0) return;

    // variaveis e constantes de controle
    let naturalReaction = null;
    let naturalReactionSec = null;
    let rallySecundaria = null;

    //1 identificar o ultimo topo de alta que deu origem a um movimento reação natural 
    const identifyHighTop = (movements) => {
      let ultimoTopoAlta = null;
      let ultimoFundoBaixa = null;
      let encontrouReacaoNatural = false;

      for (let i = 0; i < movements.length; i++) {
        const movement = movements[i];
        const type = movement.tipo;

        // Busca tendência atual.
        if (type.includes('Tendência Alta (compra)')) {
          setCurrentTrend("Tendência Alta");
        };
        if (type.includes('Tendência Baixa (venda)')) {
          setCurrentTrend("Tendência Baixa");
        };
        // Busca reações e rally atual
        if (type.includes('Reação Natural')) {
          canExecuteReactionRef.current = true
          canExecuteRallyRef.current = false
          naturalReactionSec = null;
        };
        if (type.includes('Rally Natural')) {
          canExecuteRallyRef.current = true
          canExecuteReactionRef.current = false
        };
        if (type.includes('Rally secundário')) {
          canExecuteReactionSecRef.current = false
          canExecuteRallySecRef.current = true
          naturalReaction = null;
        };
        if (type.includes('Reação secundária')) {
          canExecuteRallySecRef.current = false
          canExecuteReactionSecRef.current = true
        };

        // Encontra a Reação secundária
        if (type.includes('Reação secundária')) {
          naturalReactionSec = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          }
          continue;
        };
      };

      for (let i = movements.length - 1; i >= 0; i--) {
        const movement = movements[i];
        const type = movement.tipo;

        // Verificar se é uma Reação Natural (pode ser "Reação Natural (Alta)" ou "Reação Natural (fundo)")
        if (type.includes('Reação Natural') && !encontrouReacaoNatural) {
          naturalReaction = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          }
          encontrouReacaoNatural = true;
          continue;
        };
        // Quando já encontrou uma reação natural, procura o último topo de alta
        if (encontrouReacaoNatural && type.includes('Tendência Alta')) {
          ultimoTopoAlta = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          };
          setRetestPoints([]) // reseta os pontos
          break;
        };
        // Quando já encontrou uma reação natural, procura o último fundo de baixa
        if (encontrouReacaoNatural && type.includes('Tendência Baixa')) {
          ultimoFundoBaixa = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          };
          setRetestPoints([]) // reseta os pontos
          break;
        }
      };
      return { ultimoTopoAlta, ultimoFundoBaixa };
    };


    /**----------------------------------------------------------------------
     *                    Encontra o pivô rally Reteste
     ------------------------------------------------------------------------*/
    const identifyRetestRally = (movements) => {
      let encontrouRallyNatural = false;
      let ultimoPivoRally = false;
      let naturalRally = null;
      let rallySecundarioOrigem = null;
      let encontrouRallySecundaria = false;
      let ultimoPivoRallySec = false;
      let encontrouRallyNaturalParaSec = false;
      let encontrouRallyNaturalSec_retest = false;
      let reacaoSecundaria = false;
      let pivotReactionSec = null;

      for (let i = movements.length - 1; i >= 0; i--) {
        const movement = movements[i];
        const type = movement.tipo;

        // Encontra o ultimo rally natural
        if (!encontrouRallyNatural && type.includes('Rally Natural')) {
          naturalRally = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          }
          encontrouRallyNatural = true;
          continue;
        };
        if (encontrouRallyNatural && type.includes('Reação Natural')) {
          ultimoPivoRally = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          };
          setRetestPoints([]) // reseta os pontos
          break;
        };
        // encontrar Rally secundário
        if (!encontrouRallySecundaria && type.includes('Rally secundário')) {
          rallySecundaria = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          };
          setRetestPoints([]) // reseta os pontos
          encontrouRallySecundaria = true;
          continue;
        };
        // depois que encontrar acha o ultimo Reação secundária (que vai ser o pivo)
        if (!encontrouRallyNaturalParaSec && type.includes('Reação secundária')) {
          pivotReactionSec = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          };
          setRetestPoints([]) // reseta os pontos
          encontrouRallyNaturalParaSec = true;
          continue;
        }
        // depois que encontrar acha o ultimo Reação secundária (que vai ser o pivo)
        if (!encontrouRallyNaturalSec_retest && type.includes('Reação secundária')) {
          pivotReactionSec = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          };
          setRetestPoints([]) // reseta os pontos
          encontrouRallyNaturalParaSec = true;
          continue;
        };
      };
      for (let i = movements.length - 1; i >= 0; i--) {
        const movement = movements[i];
        const type = movement.tipo;
        // Verificar se é uma Rally Natural (pode ser "Rally Natural(Alta)" ou "Rally Natural (fundo)")
        if (encontrouRallyNaturalParaSec && type.includes('Rally Natural')) {
          ultimoPivoRallySec = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          };
          setRetestPoints([])
          break;
        };
      };
      for (let i = movements.length - 1; i >= 0; i--) {
        const movement = movements[i];
        const type = movement.tipo;
        //(pode ser "Rally secundário (Alta)" ou "Rally secundário (fundo)")
        if (encontrouRallyNaturalSec_retest && type.includes('Rally secundário')) {
          ultimoPivoRallySec = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          };
          setRetestPoints([])
          break;
        };
      };
      // percorre de trás para frente
      for (let i = movements.length - 1; i >= 0; i--) {
        const movement = movements[i];
        const type = movement.tipo;
        // 1️⃣ acha a reação secundária mais recente
        if (!reacaoSecundaria && type.includes('Reação secundária')) {
          reacaoSecundaria = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          };
          continue;
        }
        // 2️⃣ depois disso, acha o primeiro rally secundário anterior
        if (reacaoSecundaria && type.includes('Rally secundário')) {
          rallySecundarioOrigem = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          };
          setRetestPoints([])
          break;
        }
      }
      return { naturalRally, ultimoPivoRally, ultimoPivoRallySec, rallySecundarioOrigem };
    }
    /**--------------------------------------------------------------------------------
    * ///////////////////////////////////////////////////////////////////////////////
     ----------------------------------------------------------------------------------*/


    /**---------------------------------------------------------------------------------
     *          Encontra o rompimento de pivô histórico de tendência
     -----------------------------------------------------------------------------------*/
    const identifyBreakoutTrend = (movements) => {
      let enteringTheTrend = [];

      for (let i = 0; i < movements.length; i++) {
        const movement = movements[i];
        const type = movement.tipo;

        // Primeiro ponto da Tendência Alta
        if (type.includes('Tendência Alta (compra)')) {
          enteringTheTrend = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          };
          setRetestPoints([])
          continue;
        }
        // Primeiro ponto da Tendência Baixa
        if (type.includes('Tendência Baixa (venda)')) {
          enteringTheTrend = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            limite: movement.limite,
            index: i
          };
          setRetestPoints([])
          continue;
        }
      }
      return { enteringTheTrend };
    };
    /**-----------------------------------------------------------------------------------
     * //////////////////////////////////////////////////////////////////////////////////
     -------------------------------------------------------------------------------------*/

    // Passas os objetos encontrados
    const { ultimoTopoAlta, ultimoFundoBaixa } = identifyHighTop(movements);
    let { naturalRally, ultimoPivoRally, ultimoPivoRallySec, rallySecundarioOrigem } = identifyRetestRally(movements);
    const { enteringTheTrend } = identifyBreakoutTrend(movements);

    let ultimoTopo = null;
    let rallyPivo = null;
    let rally = null;
    let rallySec = null;
    let trend = null;
    let rallySecExit = null;

    /**---------------------------------------------------
     *  Verifica se o valor existe e passa para variável 
     -----------------------------------------------------*/
    if (ultimoTopoAlta) {
      ultimoTopo = ultimoTopoAlta;
    };
    if (ultimoFundoBaixa) {
      ultimoTopo = ultimoFundoBaixa;
    };
    if (naturalRally) {
      rally = naturalRally;
    };
    if (ultimoPivoRally) {
      rallyPivo = ultimoPivoRally;
    };
    if (ultimoPivoRallySec) {
      rallySec = ultimoPivoRallySec;
    };
    if (enteringTheTrend) {
      trend = enteringTheTrend;
    };
    if (rallySecundarioOrigem) {
      rallySecExit = rallySecundarioOrigem
    };
    /**---------------------------------------------------
     * //////////////////////////////////////////////////
     -----------------------------------------------------*/

    /**----------------------------------------------------
     * Verificar se é um novo topo (diferente do anterior)
     ------------------------------------------------------*/
    if (ultimoTopo) {
      const isNovoTopo = !ultimoTopoAnterior ||
        ultimoTopo.closePrice !== ultimoTopoAnterior.closePrice ||
        ultimoTopo.index !== ultimoTopoAnterior.index;
      if (isNovoTopo) {
        // Atualiza array de penúltimos valores, acumulando
        setPenultimoValor((prev) => [...prev, ultimoTopo]);
        // Atualizar o estado com o novo topo
        setUltimoTopoAnterior(ultimoTopo);
      } else {
        console.log('Topo já identificado anteriormente - ignorando repetição');
      }
    } else {
      console.log('Nenhum topo de alta antecedendo reação natural foi encontrado');
    };
    /**----------------------------------------------------
     * ///////////////////////////////////////////////////
     ------------------------------------------------------*/

    /**------------------------------------------------------------------------
     * Verificar se é um novo pivo que deu origem rally(diferente do anterior)
     --------------------------------------------------------------------------*/
    if (rallyPivo) {
      const isNovoRally = !ultimoPivoAnteriorRally ||
        rallyPivo.closePrice !== ultimoPivoAnteriorRally.closePrice ||
        rallyPivo.index !== ultimoPivoAnteriorRally.index;
      if (isNovoRally) {
        // Atualiza array de penúltimos valores, acumulando
        setRallyPivot((prev) => [...prev, rallyPivo]);
        // Atualizar o estado com o novo topo
        setUltimoPivoAnteriorRally(rallyPivo);
      };
    };
    /**------------------------------------------------------------------------
     * ///////////////////////////////////////////////////////////////////////
     --------------------------------------------------------------------------*/

    /**----------------------------------------------------------------------------
     * Verificar se é um novo pivo que deu origem reação sec(diferente do anterior)
     -------------------------------------------------------------------------------*/
    if (rallySec) {
      const isNovoRallySec = !ultimoPivoAnteriorRallySec ||
        rallySec.closePrice !== ultimoPivoAnteriorRallySec.closePrice ||
        rallySec.index !== ultimoPivoAnteriorRallySec.index;
      // Atualiza array de penúltimos valores, acumulando
      if (isNovoRallySec) {
        setRallyPivotSec((prev) => [...prev, rallySec]);
        setUltimoPivoAnteriorRallySec(rallySec);
      };
    };
    /**----------------------------------------------------------------------------
     * ///////////////////////////////////////////////////////////////////////////
     -------------------------------------------------------------------------------*/
    /**-----------------------------------------------------------------------
     *               Verificar se é novo pivô de tendência
     -------------------------------------------------------------------------*/
    if (trend) {
      const isNewTrend = !trendFound ||
        trend.closePrice !== trendFound.closePrice ||
        trend.index !== trendFound.index;
      // Atualiza array de valores, acumulando
      if (isNewTrend) {
        setTrendPivotToRetest(prev => [...prev, trend]);
        setTrendFound(trend);
      };
    };
    /**-----------------------------------------------------------------------
     * /////////////////////////////////////////////////////////////////////
     -------------------------------------------------------------------------*/


    /**--------------------------------------------------------------------------
     *                            Pega os pivôs
     ----------------------------------------------------------------------------*/
    // reteste de pivo para saída
    const TrendPivot = penultimoValor[penultimoValor.length - 1];

    //2 fazer a lógica de reteste proximo ao pivo anterior ao atual pivô ...[anterior,atual]
    const pivo = penultimoValor[penultimoValor.length - 2];

    // reteste de pivo de rally
    const pivoRally = rallyPivot[rallyPivot.length - 2];

    const pivoRallyPrimary = rallyPivot[rallyPivot.length - 1];

    // reteste de pivo rally secundário
    const pivoRallySec = rallyPivotSec[rallyPivotSec.length - 1];

    // rompimento de tendência
    let pivotBreak = trendPivotToRetest[trendPivotToRetest.length - 1];
    /**---------------------------------------------------------------------------------
     * ////////////////////////////////////////////////////////////////////////////////
     ------------------------------------------------------------------------------------*/


    /**-------------------------------------------------------------------------------
     *           Verifica se o pivô é repetido e iguinora se for repetido
     ---------------------------------------------------------------------------------*/
    if (pivo) {
      const isNovoPivo = !ultimoPivoAnterior ||
        pivo.closePrice !== ultimoPivoAnterior.closePrice ||
        pivo.index !== ultimoPivoAnterior.index;
      if (isNovoPivo) {
        setUltimoPivoAnterior(pivo); // atualiza trava
      } else {
        console.log("ultimoPivoAnterior-ignorando repetição");
      };
    };

    if (TrendPivot) {
      const isNovoPivo = !ultimoPivoAtual ||
        TrendPivot.closePrice !== ultimoPivoAtual.closePrice ||
        TrendPivot.index !== ultimoPivoAtual.index;
      if (isNovoPivo) {
        setultimoPivoAtual(TrendPivot)
      } else {
        console.log("TrendPivot-ignorando repetição");
      };
    };

    if (pivoRallySec) {
      const isNovoPivoSec = !ultimoPivoSec ||
        pivoRallySec.closePrice !== ultimoPivoSec.closePrice ||
        pivoRallySec.index !== ultimoPivoSec.index;
      if (isNovoPivoSec) {
        setUltimoPivoSec(pivoRallySec)
      }
      else {
        console.log("ultimoPivoSec-ignorando repetição");
      };
    };

    if (pivotBreak) {
      const isNewTrend = !enteringTheTrendUpdate ||
        pivotBreak.closePrice !== enteringTheTrendUpdate.closePrice ||
        pivotBreak.index !== enteringTheTrendUpdate.index;
      if (isNewTrend) {
        setEnteringTheTrendUpdate(pivotBreak)
      } else {
        console.log("enteringTheTrendUpdate-ignorando repetição");
      };
    };

    if (rallySecExit) {
      const isNewRallysec = !rallySecExitUpdate ||
        rallySecExit.closePrice !== rallySecExitUpdate.closePrice ||
        rallySecExit.index !== rallySecExitUpdate.index;
      if (isNewRallysec) {
        setRallySecExitUpdate(rallySecExit)
      } else {
        console.log("rallySecExit-ignorando repetição");
      };
    };
    /**----------------------------------------------------------------------------------
     * /////////////////////////////////////////////////////////////////////////////////
     ------------------------------------------------------------------------------------*/


    /**Função auxiliar para gerar id para unica execução */
    function buildEventId(pivo, reaction) {
      if (!pivo || !reaction) return null;
      return `${pivo.closeTime}-${reaction.closeTime}`;
    };

    // ===============================
    //  RETESTE DE TENDÊNCIA
    // ===============================
    if (pivo && naturalReaction && canExecuteReactionRef.current) {
      const limite = pivo.limite;
      const tolerance = limite / 3;
      const high = pivo.closePrice + tolerance;
      const low = pivo.closePrice - tolerance;
      const lowBuy = pivo.closePrice - (tolerance * 2);
      const highBuy = pivo.closePrice + (tolerance * 2);

      const buyPoint = pivo.closePrice + limite / 2;
      const sellPoint = pivo.closePrice - limite / 2;

      const eventId = buildEventId(pivo, naturalReaction);
      if (eventId && lastTrendRetestIdRef.current !== eventId) {
        lastTrendRetestIdRef.current = eventId;
        // 🟢 RETESTE DE COMPRA
        if (
          ultimoTopoAlta &&
          currentTrend === "Tendência Alta" &&
          naturalReaction.closePrice >= lowBuy &&
          naturalReaction.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivo", value: pivo.closePrice },
            { name: "time", value: naturalReaction.closeTime },
            { name: "buy", value: buyPoint },
            { name: "stop", value: sellPoint },
            { name: "type", value: "ENTRY_BUY_TREND" }
          ]);
        };

        // 🔴 RETESTE DE VENDA
        if (
          ultimoFundoBaixa &&
          currentTrend === "Tendência Baixa" &&
          naturalReaction.closePrice >= low &&
          naturalReaction.closePrice <= highBuy
        ) {
          setRetestPoints([
            { name: "pivo", value: pivo.closePrice },
            { name: "time", value: naturalReaction.closeTime },
            { name: "sell", value: sellPoint },
            { name: "stop", value: buyPoint },
            { name: "type", value: "ENTRY_SELL_TREND" }
          ]);
        };
      };
    };

    // ===============================
    // SAÍDA DE TENDÊNCIA
    // ===============================
    if (TrendPivot && naturalRally && canExecuteRallyRef.current) {
      const limite = TrendPivot.limite;
      const tolerance = limite / 3;
      const high = TrendPivot.closePrice + tolerance;
      const low = TrendPivot.closePrice - tolerance;
      const sellExit = TrendPivot.closePrice - limite / 2;
      const buyExit = TrendPivot.closePrice + limite / 2;

      const eventId = buildEventId(TrendPivot, naturalRally);
      if (eventId && lastTrendExitIdRef.current !== eventId) {
        lastTrendExitIdRef.current = eventId;
        // 🟢 SAÍDA DE COMPRA
        if (
          currentTrend === "Tendência Alta" &&
          naturalRally.closePrice >= low &&
          naturalRally.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivot", value: TrendPivot.closePrice },
            { name: "time", value: naturalRally.closeTime },
            { name: "buyExit", value: buyExit },
            { name: "type", value: "EXIT_BUY_TREND" }
          ]);
        };
        // 🔴 SAÍDA DE VENDA
        if (
          currentTrend === "Tendência Baixa" &&
          naturalRally.closePrice >= low &&
          naturalRally.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivot", value: TrendPivot.closePrice },
            { name: "time", value: naturalRally.closeTime },
            { name: "sellExit ", value: sellExit },
            { name: "type", value: "EXIT_SELL_TREND" }
          ]);
        };
      };
    };

    // ======================================================================
    // RETEST NO PIVO DE RALLY EM UMA REAÇÃO NATURAL (pullback pós-breakout)
    // ======================================================================

    if (pivoRallyPrimary && naturalReaction && canExecuteReactionRef.current) {
      const limite = pivoRallyPrimary.limite;
      const tolerance = limite / 3;
      const high = pivoRallyPrimary.closePrice + tolerance;
      const low = pivoRallyPrimary.closePrice - tolerance;
      const buyPoint = pivoRallyPrimary.closePrice + limite / 2;
      const sellPoint = pivoRallyPrimary.closePrice - limite / 2;


      const eventId = buildEventId(pivoRallyPrimary, naturalReaction);
      if (eventId && lastRallyRetestIdRef.current !== eventId) {
        lastRallyRetestIdRef.current = eventId;
        // 🟢 Compra rally
        if (
          currentTrend === "Tendência Alta" &&
          naturalReaction.closePrice >= low &&
          naturalReaction.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivot", value: pivoRallyPrimary.closePrice },
            { name: "time", value: naturalReaction.closeTime },
            { name: "buy", value: buyPoint },
            { name: "stop", value: sellPoint },
            { name: "type", value: "ENTRY_BUY_RALLY" }
          ]);
        };
        // 🔴 Venda rally
        if (
          currentTrend === "Tendência Baixa" &&
          naturalReaction.closePrice >= low &&
          naturalReaction.closePrice <= high

        ) {
          setRetestPoints([
            { name: "pivot", value: pivoRallyPrimary.closePrice },
            { name: "time", value: naturalReaction.closeTime },
            { name: "sell", value: sellPoint },
            { name: "stop", value: buyPoint },
            { name: "type", value: "ENTRY_SELL_RALLY" }
          ]);
        };
      };
    };

    // ======================================================================
    // RETEST NO PIVO DE RALLY EM UMA REAÇÃO SECUNDÁRIA (pullback pós-breakout)
    // ======================================================================
    if (pivoRallyPrimary && naturalReactionSec && canExecuteReactionSecRef.current) {
      const limite = pivoRallyPrimary.limite;
      const tolerance = limite / 3;
      const high = pivoRallyPrimary.closePrice + tolerance;
      const low = pivoRallyPrimary.closePrice - tolerance;
      const buyPoint = pivoRallyPrimary.closePrice + limite / 2;
      const sellPoint = pivoRallyPrimary.closePrice - limite / 2;

      const eventId = buildEventId(pivoRallyPrimary, naturalReactionSec);
      if (eventId && lastRallyRetestIdRef.current !== eventId) {
        lastRallyRetestIdRef.current = eventId;
        // 🟢 Compra rally
        if (
          currentTrend === "Tendência Alta" &&
          naturalReactionSec.closePrice <= high &&
          naturalReactionSec.closePrice >= low
        ) {
          setRetestPoints([
            { name: "pivot", value: pivoRallyPrimary.closePrice },
            { name: "time", value: naturalReactionSec.closeTime },
            { name: "buy", value: buyPoint },
            { name: "stop", value: sellPoint },
            { name: "type", value: "ENTRY_BUY_RALLY_SEC" }
          ]);
        };
        // 🔴 Venda rally
        if (
          currentTrend === "Tendência Baixa" &&
          naturalReactionSec.closePrice <= high &&
          naturalReactionSec.closePrice >= low
        ) {
          setRetestPoints([
            { name: "pivot", value: pivoRallyPrimary.closePrice },
            { name: "time", value: naturalReactionSec.closeTime },
            { name: "sell", value: sellPoint },
            { name: "stop", value: buyPoint },
            { name: "type", value: "ENTRY_SELL_RALLY_SEC" }
          ]);
        };
      };
    };

    // ===============================
    // RETEST NO PIVO DE RALLY EM UMA 
    // REAÇÃO SECUNDÁRIA
    // ===============================

    if (pivoRally && naturalReactionSec && canExecuteReactionSecRef.current) {
      const limite = pivoRally.limite;
      const tolerance = limite / 3;
      const high = pivoRally.closePrice + tolerance;
      const low = pivoRally.closePrice - tolerance;
      const buyPoint = pivoRally.closePrice + limite / 2;
      const sellPoint = pivoRally.closePrice - limite / 2;

      const eventId = buildEventId(pivoRallyPrimary.closePrice, naturalReactionSec);
      if (eventId && lastRallyRetestIdPrimaryRef.current !== eventId) {
        lastRallyRetestIdPrimaryRef.current = eventId;
        // 🟢 Comprar de retest
        if (
          currentTrend === "Tendência Alta" &&
          naturalReactionSec.closePrice <= high &&
          naturalReactionSec.closePrice >= low
        ) {
          setRetestPoints([
            { name: "pivot", value: pivoRally.closePrice },
            { name: "time", value: naturalReactionSec.closeTime },
            { name: "buy", value: buyPoint },
            { name: "stop", value: sellPoint },
            { name: "type", value: "ENTRY_BUY_RALLY_SEC" }
          ]);
        };
        // 🔴 Venda de retest
        if (
          currentTrend === "Tendência Baixa" &&
          naturalReactionSec.closePrice >= low &&
          naturalReactionSec.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivot", value: pivoRally.closePrice },
            { name: "time", value: naturalReactionSec.closeTime },
            { name: "sell", value: sellPoint },
            { name: "stop", value: buyPoint },
            { name: "type", value: "ENTRY_SELL_RALLY_SEC" }
          ]);
        };
      };
    };

    // ===============================
    // SAÍDA REAÇÃO SECUNDÁRIA
    // ===============================
    if (pivoRallySec && rallySecundaria && canExecuteRallySecRef.current) {
      const limite = pivoRallySec.limite;
      const tolerance = limite / 3;
      const highExit = pivoRallySec.closePrice + tolerance;
      const lowExit = pivoRallySec.closePrice - tolerance;
      const sellExit = pivoRallySec.closePrice - limite / 2;
      const buyExit = pivoRallySec.closePrice + limite / 2;


      const eventId = buildEventId(pivoRallySec, rallySecundaria);
      if (eventId && lastSecondaryExitIdRef.current !== eventId) {
        lastSecondaryExitIdRef.current = eventId;

        // 🟢
        if (
          rallySecundaria &&
          currentTrend === "Tendência Alta" &&
          rallySecundaria.closePrice <= highExit &&
          rallySecundaria.closePrice >= lowExit) {
          setRetestPoints([
            { name: "pivo", value: pivoRallySec.closePrice },
            { name: "time", value: rallySecundaria.closeTime },
            { name: "stop", value: sellExit },
            { name: "type", value: "EXIT_BUY_SEC" }
          ]);
        };
        // 🔴
        if (rallySecundaria &&
          currentTrend === "Tendência Baixa" &&
          rallySecundaria.closePrice >= lowExit &&
          rallySecundaria.closePrice <= highExit) {
          setRetestPoints([
            { name: "pivo", value: pivoRallySec.closePrice },
            { name: "time", value: rallySecundaria.closeTime },
            { name: "stop", value: buyExit },
            { name: "type", value: "EXIT_SELL_SEC" }
          ]);
        };
      };
    };

    if (rallySecExit && rallySecundaria && canExecuteRallySecRef.current) {
      const limite = rallySecExit.limite;
      const tolerance = limite / 3;
      const highExit = rallySecExit.closePrice + tolerance;
      const lowExit = rallySecExit.closePrice - tolerance;
      const sellExit = rallySecExit.closePrice - limite / 2;
      const buyExit = rallySecExit.closePrice + limite / 2;


      const eventId = buildEventId(rallySecExit, rallySecundaria);
      if (eventId && lastRallyExitIdRef.current !== eventId) {
        lastRallyExitIdRef.current = eventId;
        // 🟢 Saída de compra de retest
        if (
          rallySecundaria &&
          currentTrend === "Tendência Alta" &&
          rallySecundaria.closePrice <= highExit &&
          rallySecundaria.closePrice >= lowExit) {
          setRetestPoints([
            { name: "pivo", value: rallySecExit.closePrice },
            { name: "time", value: rallySecundaria.closeTime },
            { name: "stop", value: sellExit },
            { name: "type", value: "EXIT_BUY_SEC" }
          ]);
        };
        // 🔴 Saída de venda de retest
        if (rallySecundaria &&
          currentTrend === "Tendência Baixa" &&
          rallySecundaria.closePrice >= lowExit &&
          rallySecundaria.closePrice <= highExit) {
          setRetestPoints([
            { name: "pivo", value: rallySecExit.closePrice },
            { name: "time", value: rallySecundaria.closeTime },
            { name: "stop", value: buyExit },
            { name: "type", value: "EXIT_SELL_SEC" }
          ]);
        };
      };
    };

    // ===============================
    //          ROMPIMENTO 
    // ===============================
    if (pivotBreak) {
      const limite = pivotBreak.limite;
      const pivotId = pivotBreak.closeTime;
      const type = pivotBreak.tipo;
      const sellExit = pivotBreak.closePrice - limite / 2;
      const buyExit = pivotBreak.closePrice + limite / 2;

      const pivoBuy = pivotBreak.closePrice - (limite / 2);
      const pivoSell = pivotBreak.closePrice + (limite / 2);

      if (lastBreakoutIdRef.current !== pivotId) {
        lastBreakoutIdRef.current = pivotId;
        // 🟢 Rompimento de pivo compra
        if (
          currentTrend === "Tendência Alta" &&
          type === "Tendência Alta (compra)") {
          setRetestPoints([
            { name: "pivo", value: pivoBuy },
            { name: "time", value: pivotBreak.closeTime },
            { name: "buy", value: pivotBreak.closePrice },
            { name: "stop", value: sellExit },
            { name: "type", value: "pivotBreak-buy" }
          ]);
        };
        // 🔴 Rompimento de pivo venda
        if (
          currentTrend === "Tendência Baixa" &&
          type === "Tendência Baixa (venda)") {
          setRetestPoints([
            { name: "pivo", value: pivoSell },
            { name: "time", value: pivotBreak.closeTime },
            { name: "Sel", value: pivotBreak.closePrice },
            { name: "stop", value: buyExit },
            { name: "type", value: "pivotBreak-sell" }
          ]);
        };
      };
    };
  },
    [movements]);
  //console.log("COMPRA OU VENDA >>", retestPoints);
  /*######################################### ##############################
                               🎯#########🎯
    ########################################################################*/

  /*#####################################################################
                   🎯logica de confirmação usando vppr 🎯
    #####################################################################*/
  const [signalsVppr, setSignalsVppr] = useState('');


  const movementsVppr = useMemo(() => {
    if (modo === "realTimeMode") {
      return vpprComplete;
    }
    return simulationValueDataCompleteVppr;
  }, [modo, vpprComplete, simulationValueDataCompleteVppr]);


  useEffect(() => {
    if (!movementsVppr || movementsVppr.length === 0) return;

    let vpprSignals = [];
    let vpprPowerSignalsBuy = false;
    let vpprPowerSignalsSell = false;

    for (let i = 0; i < movementsVppr.length; i++) {
      const current = movementsVppr[i];

      const percentage = current.vppr_ema * 0.2; // 20% de distância da média móvel
      const bandsUp = current.vppr_ema + percentage;
      const bandsLow = current.vppr_ema - percentage;

      const vppr = current.vppr;
      const vpprEma = current.vppr_ema;

      // Sinais de força do VPPR (com base na direção do VPPR)
      if (current.vppr > 0) {
        vpprPowerSignalsBuy = true;
      } else if (current.vppr < 0) {
        vpprPowerSignalsSell = true;
      }

      // Sinais de tendência do VPPR (com base na posição do VPPR em relação à média móvel e às bandas)
      if (vpprPowerSignalsBuy && vppr > vpprEma) {
        vpprSignals = "trend-buy"
      } else if (vpprPowerSignalsSell && vppr > bandsUp) {
        vpprSignals = "trend-buy"
      }

      if (vpprPowerSignalsSell && vppr < vpprEma) {
        vpprSignals = "trend-sell"
      } else if (vpprPowerSignalsBuy && vppr < bandsLow) {
        vpprSignals = "trend-sell"
      }
    };

    setSignalsVppr(vpprSignals);
  }, [movementsVppr]);
  console.log("SignalsVppr", signalsVppr);

  /*#####################################################################
                                🎯########🎯
    #####################################################################*/


  /*#####################################################################
                   🎯logica de entrada e saída usando AMRSI 🎯
    #####################################################################*/
  const [signalsAmrsiSell, setSignalsAmrsiSell] = useState([]);/*(sobrecompra-parcial)*/
  const [signalsAmrsiBuy, setSignalsAmrsiBuy] = useState([]);/*(sobrevenda-parcial)*/
  const [signalsAmrsiSellReentry, setSignalsAmrsiSellReentry] = useState([]);/*(sobrevenda-reentrada)*/
  const [signalsAmrsiBuyReentry, setSignalsAmrsiBuyReentry] = useState([]);/*(sobrevenda-reentrada)*/


  const movementsAmrsi = useMemo(() => {
    if (modo === "realTimeMode") {
      return rsiComplete;
    }
    return simulationValueDataCompleteRsi;
  }, [modo, rsiComplete, simulationValueDataCompleteRsi]);

  useEffect(() => {
    if (!movementsAmrsi || movementsAmrsi.length === 0) return;

    const amRsiSignalBuy = [];
    const amRsiSinalSell = [];

    const amRsiSignalBuyReentry = [];
    const amRsiSinalSellReentry = [];

    let wasOverbought = false;
    let wasOversold = false;

    let overboughtReentry = false;
    let oversoldReentry = false;

    for (let i = 0; i < movementsAmrsi.length; i++) {
      const movement = movementsAmrsi[i];

      // the API may return amrsi, rsi_ma or rsi – use whichever is available
      const amrsi = movement.amrsi ?? movement.rsi_ma ?? movement.rsi;
      if (amrsi == null) continue; // skip missing values

      /* ---------- SOBRECOMPRA PARCIAL ---------- */
      // 1️⃣ entra em sobrecompra
      if (amrsi >= 80) {
        wasOverbought = true;
      }

      // 2️⃣ início da correção → venda
      if (wasOverbought && amrsi <= 70 && currentTrend === "Tendência Alta") {
        amRsiSinalSell.push({
          index: i,
          signal: "amrsi-partial-sell",
          amrsi,
          trend: currentTrend,
          date: movement.time,
        });
        wasOverbought = false; // reseta após sinal
      }

      /* ---------- SOBREVenda PARCIAL---------- */
      // 3️⃣ entra em sobrevenda
      if (amrsi <= 20) {
        wasOversold = true;
      }

      // 4️⃣ início da correção → compra
      if (wasOversold && amrsi >= 30 && currentTrend === "Tendência Baixa") {
        amRsiSignalBuy.push({
          index: i,
          signal: "amrsi-partial-buy",
          amrsi,
          trend: currentTrend,
          date: movement.time,

        });
        wasOversold = false; // reseta após sinal
      }

      /* ---------- SOBRECOMPRA REENTRADA---------- */
      if (amrsi >= 70) {
        overboughtReentry = true;
      }
      if (overboughtReentry && amrsi <= 65 && currentTrend === "Tendência Baixa") {
        amRsiSinalSellReentry.push({
          index: i,
          signal: "amrsi-Reentry-sell",
          amrsi,
          trend: currentTrend,
          date: movement.time,
        });
        overboughtReentry = false; // reseta após sinal
      }

      /* ---------- SOBREVENDA REENTRADA---------- */
      if (amrsi <= 30) {
        oversoldReentry = true;
      }
      if (oversoldReentry && amrsi >= 35 && currentTrend === "Tendência Alta") {
        amRsiSignalBuyReentry.push({
          index: i,
          signal: "amrsi-Reentry-buy",
          amrsi,
          trend: currentTrend,
          date: movement.time,
        });
        oversoldReentry = false; // reseta após sinal
      }
    }
    /**Guarda dados na variável de estado (SOBREVenda PARCIAL) */
    setSignalsAmrsiSell(amRsiSinalSell);
    setSignalsAmrsiBuy(amRsiSignalBuy);
    /**Guarda dados na variável de estado (SOBREVENDA REENTRADA) */
    setSignalsAmrsiSellReentry(amRsiSinalSellReentry);
    setSignalsAmrsiBuyReentry(amRsiSignalBuyReentry);

  }, [movementsAmrsi]);

  /*#####################################################################
                          🎯############### 🎯
    #####################################################################*/
  /*#####################################################################
                  🎯filtra pontos de entrada 🎯
#####################################################################*/

  const [newConfirmBuyEntry, setNewConfirmBuyEntry] = useState([]);
  const [newConfirmSellEntry, setNewConfirmSellEntry] = useState([]);
  const [newExitBuy, setNewExitBuy] = useState([]);
  const [newExitSell, setNewExitSell] = useState([]);

  useEffect(() => {
    if (!retestPoints || retestPoints.length === 0) return;

    const dataPriceCurrent = simulationCandleComplete.length > 0
      ? simulationCandleComplete
      : candlesComplete;

    if (!dataPriceCurrent || dataPriceCurrent.length === 0) return;


    // Itera sobre todos os preços da simulação para verificar entradas
    const newBuy = [];
    const newSell = [];
    const exitBuy = [];
    const exitSell = [];



    // Converte array de {name, value} para objeto único
    const pointObj = retestPoints.reduce((obj, item) => {
      obj[item.name] = item.value;
      return obj;
    }, {});



    // Verifica para cada preço na simulação se atingiu o ponto de entrada ou saída
    dataPriceCurrent.forEach((currentPrice, index) => {
      const prevPrice = dataPriceCurrent[index - 1];
      if (
        prevPrice >= pointObj.buy &&
        (pointObj.type === "ENTRY_BUY_TREND" ||
          pointObj.type === "ENTRY_BUY_RALLY" ||
          pointObj.type === "ENTRY_BUY_RALLY_SEC") &&
        signalsVppr === "trend-buy"
      ) {
        // Adiciona apenas se não já confirmado
        if (!newBuy.some(entry => entry.time === pointObj.time)) {
          newBuy.push({ ...pointObj, index });
        }
      } else if (
        prevPrice <= pointObj.sell &&
        (pointObj.type === "ENTRY_SELL_TREND" ||
          pointObj.type === "ENTRY_SELL_RALLY" ||
          pointObj.type === "ENTRY_SELL_RALLY_SEC") &&
        signalsVppr === "trend-sell"
      ) {
        // Adiciona apenas se não já confirmado
        if (!newSell.some(entry => entry.time === pointObj.time)) {
          newSell.push({ ...pointObj, index });
        }
      }
      else if (signalsVppr === "trend-buy" && pointObj.type === "pivotBreak-buy") {
        if (!newBuy.some(entry => entry.time === pointObj.time)) {
          newBuy.push({ ...pointObj, index });
        }
      }
      else if (signalsVppr === "trend-sell" && pointObj.type === "pivotBreak-sell") {
        if (!newSell.some(entry => entry.time === pointObj.time)) {
          newSell.push({ ...pointObj, index });
        }
      }

      //////////////////////////-----------//-------------///////////////////////

      if (
        pointObj.type === "EXIT_BUY_TREND" ||
        pointObj.type === "EXIT_BUY_SEC" &&
        prevPrice > currentPrice <= pointObj.stop
      ) {
        if (!exitBuy.some(entry => entry.time === pointObj.time)) {
          exitBuy.push({ ...pointObj, index });
        }
      }
      else if (
        pointObj.type === "EXIT_SELL_TREND" ||
        pointObj.type === "EXIT_SELL_SEC" &&
        prevPrice < currentPrice >= pointObj.stop
      ) {
        if (!exitSell.some(entry => entry.time === pointObj.time)) {
          exitSell.push({ ...pointObj, index });
        }
      }
    });


    // Acumula os novos confirmados sem duplicatas
    setNewConfirmBuyEntry(newBuy);
    setNewConfirmSellEntry(newSell);

    // Saídas de operações
    setNewExitBuy(exitBuy);
    setNewExitSell(exitSell);

  }, [retestPoints, signalsVppr, simulationCandleValue, candlesComplete]);

  console.log("newConfirmBuyEntry:", newConfirmBuyEntry)
  console.log("NewConfirmSellEntry:", newConfirmSellEntry);
  console.log("NewExitBuy", newExitBuy);
  console.log("NewExitSell", newExitSell);



  /*#####################################################################
                          🎯############### 🎯
    #####################################################################*/
  /*#####################################################################
                      🎯ENVIA OS DADOS PARA BACKTESTE 🎯
#####################################################################*/
  const backtest = async () => {
    if (modo !== "simulation") {
      return;
    }
    if (!symbol) {
      console.warn("Símbolo não encontrado para salvar backtest");
      return;
    }

    try {
      const response = await axios.post(`${url}/api/save_backtest_results`, {},
        {
          params: {
            symbol: symbol,
            modo: modo,
            signalsVppr,
            signalsAmrsiSell,
            signalsAmrsiBuy,
            signalsAmrsiSellReentry,
            signalsAmrsiBuyReentry,
          }
        });
      console.log("Backtest salvo com sucesso:", response.data);
    }
    catch (error) {
      console.error("Erro ao salvar backtest:", error);
    }
  }

  /*#####################################################################
                          🎯############### 🎯
    #####################################################################*/





  /**========================================================================
   *        Limpa todos os tempos limite e intervalos na desmontagem: 
   * ========================================================================*/
  useEffect(() => {
    isPausedRef.current = isPaused;
    isPausedVpprRef.current = isPausedVppr;
    isPausedRsiRef.current = isPausedRsi;
  }, [isPaused, isPausedRsi, isPausedVppr]);


  useEffect(() => {
    if (realTime === "realTimeMode") {
      clearTimeout(simulationTimeoutRef.current);
      clearTimeout(simulationTimeoutSyncRef.current);
      clearTimeout(simulationRsiTimeoutRef.current);
      clearTimeout(simulationVpprTimeoutRef.current);
      clearTimeout(simulationCandleTimeoutRef.current);

      clearTimeout(timeoutRsiRef.current);
      clearTimeout(intervalVpprRef.current);
      clearTimeout(intervalRsiRef.current);
      clearTimeout(intervalRef.current);
      offsetRefPrimary.current = 0;
      offsetRefRsi.current = 0;
      offsetRefVppr.current = 0;
      offsetRefCandle.current = 0;
      setSimulationCandleComplete([]);
      setSimulationCandleValue([]);
      setSimulationCandleLabel([]);
      // Permite reutilizar delta-tracking em próximas chamadas de modo real-time
      // (não limpa os refs para manter histórico entre API calls)
    } else {
      // Ao sair do modo real-time, limpa os timestamp refs para próxima vez que entrar
      lastProcessedTimestampRef.current = null;
      lastProcessedTimestampRsiRef.current = null;
      lastProcessedTimestampVpprRef.current = null;
      offsetRefVppr.current = 0;
      if (simulationControllerRef.current) {
        simulationControllerRef.current.abort();
      }
      setSimulationValueData([]);
      setSimulationLabelData([]);
      setSimulationValueDataRsi([]);
      setSimulationLabelDataRsi([]);
      setSimulationValueDataVppr([]);
      setSimulationLabelDataVppr([]);
    }
  }, [realTime]);

  /**Limpeza de temporizador/intervalo e desmontagem segura 🚿 */
  useEffect(() => {
    return () => {
      clearTimeout(simulationTimeoutSyncRef.current);
      clearTimeout(simulationTimeoutRef.current);
      clearTimeout(simulationRsiTimeoutRef.current);
      clearTimeout(simulationVpprTimeoutRef.current);
      clearTimeout(simulationCandleTimeoutRef.current);
      clearTimeout(timeoutRsiRef.current);
      if (simulationControllerRef.current) {
        simulationControllerRef.current.abort();
      }
    }
  }, []);
  /**========================================================================
   * ///////////////////////////////////////////////////////////////////////
   * ========================================================================*/

  useEffect(() => {
    async function loadData() {
      try {
        const savedSymbol = await getSymbol();
        if (savedSymbol) {
          await Promise.all([
            LoadGraphicDataOne(savedSymbol),
            handleGetTime(),
            handleGetPoints(),
            getDateSimulation(),
            saveMarketNotes(),
            getMarketObservation(),
            getMarketObservationComplete(),
            correlation(),
            assetCorrelation(savedSymbol),
          ], [savedSymbol]);
        } else {
          console.warn("Nenhum símbolo salvo encontrado!");
        }
      } catch (error) {
        console.error("Erro ao carregar os dados iniciais:", error);
      }
    }
    loadData();

    /*=============================
        Executa a cada 15 minutos
      =============================*/

    const timeframeToMs = (tf) => {
      if (!tf) return 15 * 60 * 1000;
      const s = String(tf).trim();
      const m = s.match(/^(\d+)\s*([mhd])$/i);
      if (!m) return 15 * 60 * 1000;
      const value = parseInt(m[1], 10);
      const unit = m[2].toLowerCase();
      switch (unit) {
        case 'm':
          return value * 60 * 1000;
        case 'h':
          return value * 60 * 60 * 1000;
        case 'd':
          return value * 24 * 60 * 60 * 1000;
        default:
          return 15 * 60 * 1000;
      }
    };


    // always clear existing schedules when re-evaluating
    clearTimeout(timeoutRef.current);
    clearInterval(intervalRef.current);

    if (realTime === "realTimeMode") {
      const intervalMs = timeframeToMs(timeCurrent);

      if (!intervalMs || Number.isNaN(intervalMs) || intervalMs <= 0) {
        console.warn('timeframe inválido:', timeCurrent);
      } else {
        const now = Date.now();
        // Próximo múltiplo exato do timeframe
        const nextTick = Math.ceil(now / intervalMs) * intervalMs;

        let delay = nextTick - now;
        if (delay < 0) delay = 0;

        // pequeno buffer (9s) para garantir candle fechado; remova se não quiser buffer
        const bufferMs = 9000;
        delay += bufferMs;

        console.log(`⏳ Próxima atualização em ${Math.round(delay / 1000)} segundos (intervalo ${intervalMs}ms)`);

        // Salva ids em refs já usados no código para permitir clearTimeout/clearInterval
        timeoutRef.current = setTimeout(() => {
          updateAllData();
          intervalRef.current = setInterval(() => {
            updateAllData();
          }, intervalMs);
        }, delay);
      }
    }

    async function updateAllData() {
      if (!symbol) {
        console.warn("⚠️ updateAllData ignorado: symbol vazio");
        return;
      }
      try {
        // 🔄 Atualiza todas as observações de mercado salvos (não bloqueia o resto)
        axios.get(`${url}/api/update_market_observations`)
          .then(res => {
            if (res.data?.updated_symbols) {
              const successful = res.data.updated_symbols.filter(u => u.status === 'atualizado').length;
              console.log(`✅ ${successful} observações atualizadas`);
            }
          })
          .catch(err => console.warn("⚠️ Erro ao atualizar observações:", err.message));
        await Promise.all([
          graphicCandles(),
          graphicDataOne(symbol),
          handleGetPoints(),
          saveMarketNotes(),
          getMarketObservation(),
          getRsi(symbol),
          getVppr(symbol),
          correlation(),
          assetCorrelation(symbol),

        ]);
        console.log("✅ Dados atualizados em", new Date().toLocaleTimeString());
      } catch (error) {
        console.error("Erro ao atualizar dados:", error);
      }
    }
    ;
  }, [symbol, realTime, timeCurrent]);
  /*======================================================================
    /////////////////////////////////////////////////////////////////////
    ======================================================================*/


  const contextValue = {
    handleSave,
    handleRemove,
    atr,
    dadosPrice,
    theme,
    setTheme,
    handleSearch,
    inputRefMain,
    symbol,
    handleClickTime,
    activeButton,
    importantPoints,
    togglePivot,
    selectedPivots,
    setRealTime,
    realTime,
    simulationLabelData,
    simulationValueData,
    isPaused,
    setIsPaused,
    isPausedRef,
    simulationValueDataComplete,
    dateSimulationStart,
    setDateSimulationStart,
    dateSimulationEnd,
    setDateSimulationEnd,
    dateSimulation,
    setDays,
    days,
    showDaysInput,
    setShowDaysInput,
    daysValue,
    setDaysValue,
    rsi,
    rsiTime,
    rsiComplete,
    simulationValueDataRsi,
    simulationLabelDataRsi,
    vppr,
    vpprTime,
    vpprEma,
    simulationLabelDataVppr,
    simulationValueDataVppr,
    simulationValueDataVpprEma,
    windowSize,
    setWindowSize,
    marketObservation,
    marketObservationComplete,
    getMarketObservationComplete,
    addSymbol,
    setAddSymbol,
    saveMarketNotes,
    setRemoveSymbol,
    data,
    setData,
    handleRemoveSymbol,
    isGlobalLoading, // global loader
    startGlobalLoading,
    stopGlobalLoading,
    runWithGlobalLoading,
    loadingSimulation,
    downloadedData,
    dataCorrelation,
    assetCorrelationData,
    simulationCandleComplete,
    candlesComplete,
    vpprComplete,
    backtest,
    graphicDataOne,
    timeCurrent,
  };

  return (
    <>
      <Toast ref={toast} position="bottom-right"
        className="custom-toast"
      />
      {/* Global loading overlay (single loader for all data fetches) */}
      {isGlobalLoading && (
        <div style={{ position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.35)', zIndex: 9999 }}>
          <div style={{ textAlign: 'center', color: '#fff' }}>
            <ProgressSpinner style={{ width: 64, height: 64 }} strokeWidth="6" />
            {checkEndOfIncrement && (
              <BsRobot style={{ display: 'flex', position: 'absolute', marginLeft: '50px' }} />
            )}

            <div style={{ marginTop: 12 }}>Updating data...</div>
          </div>
        </div>
      )}

      <AppContext.Provider value={contextValue}>
        {props.children}
      </AppContext.Provider>

    </>
  );
};

export default ContextApi;
