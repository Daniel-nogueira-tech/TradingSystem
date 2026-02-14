import React, { createContext, useEffect, useRef, useState } from 'react';
import Swal from 'sweetalert2';
import axios from 'axios';
import { Toast } from 'primereact/toast';

import 'primereact/resources/themes/lara-dark-indigo/theme.css';

import 'primereact/resources/primereact.min.css';




export const AppContext = createContext();

const ContextApi = (props) => {
  const url = "http://localhost:5000";
  const [theme, setTheme] = useState(() => { return localStorage.getItem('theme') || 'dark'; });
  const [windowSize, setWindowSize] = useState(1000);
  const [values, setValues] = useState([]);
  const [labels, setLabels] = useState([]);
  const [atr, setAtr] = useState([]);
  const [dadosPrice, setDadosPrice] = useState([]);
  const inputRefMain = useRef(null);
  const [symbol, setSymbol] = useState("");
  const toast = useRef(null);
  const [activeButton, setActiveButton] = useState('');
  const [importantPoints, setImportantPoints] = useState([]);
  const [selectedPivots, setSelectedPivots] = useState([]);
  const [realTime, setRealTime] = useState(() => {
    return localStorage.getItem("realTimeMode") || "simulation";
  });
  const modo = realTime;
  const [rsi, setRsi] = useState([]);
  const [rsiTime, setRsiTime] = useState([]);
  const [vppr, setVppr] = useState([]);
  const [vpprTime, setVpprTime] = useState([]);
  const [vpprEma, setVpprEma] = useState([]);
  const [addSymbol, setAddSymbol] = React.useState('');// nova variável de estado para armazenar o símbolo a ser adicionado
  const [removeSymbol, setRemoveSymbol] = React.useState('') // remover simbolos
  const [data, setData] = React.useState([]);

  const [dateSimulationStart, setDateSimulationStart] = useState("")
  const [dateSimulationEnd, setDateSimulationEnd] = useState("")
  const [days, setDays] = useState('')
  const [showDaysInput, setShowDaysInput] = useState(false);
  const [daysValue, setDaysValue] = useState('');

  /*Variaveis para atualizar graficos*/
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

  const simulationControllerRef = useRef(null);

  const toastShownRef = useRef(false);

  const offsetRefPrimary = useRef(0);
  const offsetRefRsi = useRef(0);
  const offsetRefVppr = useRef(0);


  const period = 14; /* periodo do AMRSI */


  /*-----------------------------------------------
  Função para alternar entre simulação e real time 
  --------------------------------------------------*/

  const LoadGraphicDataOne = async (savedSymbol) => {
    if (realTime === "realTimeMode") {
      await graphicDataOne(savedSymbol);
      await getRsi(savedSymbol);
      await getVppr(savedSymbol);

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
      await getVppr()
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



  /*#####################################################################
                           1️⃣💰INICIA SIMULAÇÃO💰1️⃣
  ######################################################################### */
  /*-------------------------------------------------
    1️⃣ Busca as datas da simulação do ativo Primária
   ---------------------------------------------------*/
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
  /*---------------------------------------------
    Função para simulação pega os dados fatiados
   -----------------------------------------------*/

  const simulateStepSync = async (symbolPrimary) => {
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

      // agenda próxima iteração (próximo Vppr + catch-up)
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




  /*-----------------------------------------------------------------
    1️⃣ Função para Selecionae datas para simulação do ativo Primária
   -------------------------------------------------------------------*/
  const dateSimulation = async () => {
    try {
      const response = await axios.post(
        `${url}/api/update_klines`,
        {}, // corpo vazio
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

      // ✅ Toast de sucesso
      toast.current.show({
        severity: "success",
        summary: 'Sucesso!',
        detail: `Os dados para simular foram baixados!`,
        life: 5000
      });

    } catch (error) {
      // ❌ Toast de erro
      toast.current.show({
        severity: 'error',
        summary: 'Erro',
        detail: `Não é possível baixar dados para simular`,
        life: 5000
      });
      console.error("Erro na API de atualização de datas:", error.response?.data || error.message);
    }
  }

  /*#####################################################################
                           1️⃣💰FIM DA SIMULAÇÃO💰1️⃣
  ########################################################################*/




  /*#####################################################################
                         1️⃣📈INICIO ATIVO PRIMÁRIA📈1️⃣
  ########################################################################*/
  /*-------------------------------------------------
    1️⃣ Função para buscar dados do ativo Primária
   --------------------------------------------------*/
  const graphicDataOne = async (symbol) => {
    // 🧹 Limpa dados da simulação
    clearTimeout(simulationTimeoutRef.current);
    try {
      const response = await axios.get(`${url}/api/filter_price_atr?symbol=${symbol}`);
      const data = response.data;

      if (!Array.isArray(data) || data.length === 0) return;

      const len = data.length;

      // Pré-alocação (rápido e cache-friendly)
      const prices = new Float64Array(len);
      const labelsArr = new Array(len);

      for (let i = 0; i < len; i++) {
        const candle = data[i];
        prices[i] = Number(candle.closePrice);
        labelsArr[i] = candle.closeTime;
      }

      const atrLast = Number(data[len - 1].limite);

      // 🔥 commits de estado
      setValues(prices);
      setLabels(labelsArr);
      setAtr(atrLast);
      setDadosPrice(data);

    } catch (error) {
      console.error("❌ Erro ao buscar dados:", error);
    }
  };



  /*----------------------------------------------------------------
    🔍1️⃣ Faz pequisa do simbolo envia para backend (do ativo primária)
    -----------------------------------------------------------------*/
  const handleSearch = async (event) => {
    event?.preventDefault();
    inputRefMain.current.focus();

    const searchedSymbol = inputRefMain.current.value.toUpperCase();
    if (!searchedSymbol) return;

    try {
      const response = await axios.get(`${url}/api/filter_price_atr?symbol=${searchedSymbol}`);
      const data = response.data;

      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => p.closeTime);

      setLabels(time);
      setValues(prices);
      setDadosPrice(data);
      setSymbol(searchedSymbol);

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
  /*----------------------------
    🔍1️⃣ Busca o simbolo Primária
   ------------------------------*/
  const getSymbol = async () => {
    try {
      const response = await axios.get(url + "/api/last_symbol")
      const data = response.data;
      setSymbol(data.symbol);
      return data.symbol;
    } catch (error) {
      console.error("Erro na API para recuperar símbolos:", error);
    }
  };
  /*#####################################################################
                         1️⃣📈FIM ATIVO PRIMÁRIA📈1️⃣
  ########################################################################*/


  /*------------------------------------------------------------------------------
    🗓 Salva o tempo grafico que vai ser usando como dados (envia para o backend)
  --------------------------------------------------------------------------------*/
  const handleClickTime = async (time) => {
    if (!time) return;
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

      } catch (error) {
        Swal.fire({
          title: "Erro!",
          text: "Não foi possível atualizar o timeframe.",
          icon: "error"
        });
        console.error("Erro ao enviar timeframe:", error);
      }
    }
  };
  /*-------------------------------------------------------------
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
  /*------------------------------------
    pega os pontos de pivot importantes
  --------------------------------------*/
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
  /*------------------------------------
    Função para adicionar/remover pivôs
  --------------------------------------*/
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


  /*------------------------------------------
 Função para pegar dados do calculo rsi
--------------------------------------------*/
  const getRsi = async (symbol) => {

    try {
      const response = await axios.get(
        `${url}/api/rsi?period=${period}&symbol=${symbol}&modo=${modo}`
      );
      const data = response.data;
      if (!Array.isArray(data)) {
        console.warn("Dados do RSI não são um array:", data);
        return;
      }

      const value = data.map(p => parseFloat(p.rsi_ma));
      const time = data.map(p => p.time.split(' '));
      setRsi([...value])
      setRsiTime([...time])
    } catch (error) {
      console.error("Erro ao buscar dados do RSI", error);
    }
  };

  /*--------------------------------------------------------------------
 Função para pegar dados do calculo  vppr (Volume Price Pressure Ratio) 
-------------------------------------------------------------------------*/
  let controller;
  const getVppr = async (symbol) => {
    if (controller) controller.abort();
    controller = new AbortController();

    try {
      const { data } = await axios.get(
        `${url}/api/vppr`,
        {
          params: { symbol, modo },
          signal: controller.signal
        }
      );

      if (!Array.isArray(data)) return;

      const value = [];
      const time = [];
      const ema = [];

      for (const p of data) {
        value.push(+p.vppr);
        ema.push(+p.vppr_ema);
        time.push(p.time.split(' ')[0]);
      }
      setVppr(value)
      setVpprTime(time)
      setVpprEma(ema)

    } catch (error) {
      console.error("Erro ao buscar dados do VPPR", error);
    }
  }
  /**------------------------------------------------------------
   * Função para salvar observações de mercado no banco de dados
   --------------------------------------------------------------*/
  const [marketObservation, setMarketObservation] = useState([]);
  const saveMarketNotes = async () => {
    if (!addSymbol || !addSymbol.trim()) {
      console.warn("⏭️ Requisição ignorada: símbolo vazio");
      return;
    }

    try {
      const { data } = await axios.post(`${url}/api/market_observation`, {
        symbol: addSymbol.trim().toUpperCase(),
        total: 2000
      });

      toast.current.show({
        severity: "success",
        summary: "Sucesso!",
        detail: `Símbolo adicionado: ${addSymbol}`,
        life: 5000
      });

      setAddSymbol('');
      getMarketObservation(); // Atualiza a lista de observações após adicionar
      
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
  /**=========================================
   * pega os dados para observação de mercado
   * =========================================*/
  const getMarketObservation = async () => {
    try {
      const response = await axios.get(`${url}/api/latest_market_observation`);
      setMarketObservation(response.data);
    } catch (error) {
      console.error("Erro ao buscar observações de mercado:", error);
    }
  };
  const handleRemoveSymbol = async (symbol) => {
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
  }


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



  /*#####################################################################
                        🎯logica de compra e venda início🎯
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


  useEffect(() => {
    // dados de classificação simulados 
    const movements = simulationValueDataComplete;


    // variaveis e constantes de controle
    let naturalReaction = null;
    let pivotReactionSec = null;
    let naturalReactionSec = null;
    let rallySecundaria = null



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
        }
        if (type.includes('Tendência Baixa (venda)')) {
          setCurrentTrend("Tendência Baixa");
        }
        // Busca reações e rally atual
        if (type.includes('Reação Natural')) {
          canExecuteReactionRef.current = true
          canExecuteRallyRef.current = false
        }

        if (type.includes('Rally Natural')) {
          canExecuteRallyRef.current = true
          canExecuteReactionRef.current = false
        }

        if (type.includes('Rally secundário')) {
          canExecuteReactionSecRef.current = false
          canExecuteRallySecRef.current = true
        }
        if (type.includes('Reação secundária')) {
          canExecuteRallySecRef.current = false
          canExecuteReactionSecRef.current = true
        }




        // Encontra a Reação secundária
        if (type.includes('Reação secundária')) {
          naturalReactionSec = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            atr: movement.atr,
            index: movements.length - 1 - i
          }
          continue;
        }
      }



      for (let i = movements.length - 1; i >= 0; i--) {
        const movement = movements[i];
        const type = movement.tipo;


        // Verificar se é uma Reação Natural (pode ser "Reação Natural (Alta)" ou "Reação Natural (fundo)")
        if (type.includes('Reação Natural') && !encontrouReacaoNatural) {
          naturalReaction = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            atr: movement.atr,
            index: i
          }
          encontrouReacaoNatural = true;
          continue;
        }

        // Quando já encontrou uma reação natural, procura o último topo de alta
        if (encontrouReacaoNatural && type.includes('Tendência Alta')) {
          ultimoTopoAlta = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            atr: movement.atr,
            index: i
          };
          setRetestPoints([]) // reseta os pontos
          break;
        }
        // Quando já encontrou uma reação natural, procura o último fundo de baixa
        if (encontrouReacaoNatural && type.includes('Tendência Baixa')) {
          ultimoFundoBaixa = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            atr: movement.atr,
            index: i
          };
          setRetestPoints([]) // reseta os pontos
          break;
        }

      }

      return { ultimoTopoAlta, ultimoFundoBaixa };
    };


    // Encontra o pivô rally
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


      for (let i = movements.length - 1; i >= 0; i--) {
        const movement = movements[i];
        const type = movement.tipo;


        // Encontra o ultimo rally natural
        if (!encontrouRallyNatural && type.includes('Rally Natural')) {
          naturalRally = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            atr: movement.atr,
            index: i
          }
          encontrouRallyNatural = true;
          continue;
        }

        if (encontrouRallyNatural && type.includes('Reação Natural')) {
          ultimoPivoRally = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            atr: movement.atr,
            index: i
          };
          setRetestPoints([]) // reseta os pontos
          break;
        }

        // encontrar Rally secundário
        if (!encontrouRallySecundaria && type.includes('Rally secundário')) {
          rallySecundaria = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            atr: movement.atr,
            index: i
          };
          setRetestPoints([]) // reseta os pontos
          encontrouRallySecundaria = true;
          continue;
        }

        // depois que encontrar acha o ultimo Reação secundária (que vai ser o pivo)
        if (!encontrouRallyNaturalParaSec && type.includes('Reação secundária')) {
          pivotReactionSec = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            atr: movement.atr,
            index: i
          };
          setRetestPoints([]) // reseta os pontos
          encontrouRallyNaturalParaSec = true;
          continue;
        }


        //////
        // depois que encontrar acha o ultimo Reação secundária (que vai ser o pivo)
        if (!encontrouRallyNaturalSec_retest && type.includes('Reação secundária')) {
          pivotReactionSec = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            atr: movement.atr,
            index: i
          };
          setRetestPoints([]) // reseta os pontos
          encontrouRallyNaturalParaSec = true;
          continue;
        }
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
            atr: movement.atr,
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
            atr: movement.atr,
            index: i
          };
          setRetestPoints([])
          break;
        }
      }


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
            atr: movement.atr,
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
            atr: movement.atr,
            index: i
          };
          setRetestPoints([])
          break;
        }
      }



      return { naturalRally, ultimoPivoRally, ultimoPivoRallySec, rallySecundarioOrigem };
    }


    // Encontra o tendencia
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
            atr: movement.atr,
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
            atr: movement.atr,
            index: i
          };
          setRetestPoints([])
          continue;
        }
      }

      return { enteringTheTrend };
    };








    const { ultimoTopoAlta, ultimoFundoBaixa } = identifyHighTop(movements);
    let { naturalRally, ultimoPivoRally, ultimoPivoRallySec, rallySecundarioOrigem } = identifyRetestRally(movements)
    const { enteringTheTrend } = identifyBreakoutTrend(movements);


    let ultimoTopo = null;
    let rallyPivo = null;
    let rally = null;
    let rallySec = null;
    let trend = null;
    let rallySecExit = null;



    if (ultimoTopoAlta) {
      ultimoTopo = ultimoTopoAlta;
    }
    if (ultimoFundoBaixa) {
      ultimoTopo = ultimoFundoBaixa;
    }
    if (naturalRally) {
      rally = naturalRally;
    }
    if (ultimoPivoRally) {
      rallyPivo = ultimoPivoRally;
    }
    if (ultimoPivoRallySec) {
      rallySec = ultimoPivoRallySec;
    }

    if (enteringTheTrend) {
      trend = enteringTheTrend;
    }
    if (rallySecundarioOrigem) {
      rallySecExit = rallySecundarioOrigem
    }



    // Verificar se é um novo topo (diferente do anterior)
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
    }


    // Verificar se é um novo pivo que deu origem rally(diferente do anterior)
    if (rallyPivo) {
      const isNovoRally = !ultimoPivoAnteriorRally ||
        rallyPivo.closePrice !== ultimoPivoAnteriorRally.closePrice ||
        rallyPivo.index !== ultimoPivoAnteriorRally.index;
      if (isNovoRally) {
        // Atualiza array de penúltimos valores, acumulando
        setRallyPivot((prev) => [...prev, rallyPivo]);
        // Atualizar o estado com o novo topo
        setUltimoPivoAnteriorRally(rallyPivo);
      }
    }

    // Verificar se é um novo pivo que deu origem reação sec(diferente do anterior)
    if (rallySec) {
      const isNovoRallySec = !ultimoPivoAnteriorRallySec ||
        rallySec.closePrice !== ultimoPivoAnteriorRallySec.closePrice ||
        rallySec.index !== ultimoPivoAnteriorRallySec.index;
      // Atualiza array de penúltimos valores, acumulando
      if (isNovoRallySec) {
        setRallyPivotSec((prev) => [...prev, rallySec]);
        setUltimoPivoAnteriorRallySec(rallySec); // ✅ salva o rally real
      };
    }

    // Verificar se é uma nova tendência
    if (trend) {
      const isNewTrend = !trendFound ||
        trend.closePrice !== trendFound.closePrice ||
        trend.index !== trendFound.index;
      // Atualiza array de valores, acumulando
      if (isNewTrend) {
        setTrendPivotToRetest(prev => [...prev, trend]);
        setTrendFound(trend);
      }
    }




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


    if (pivo) {
      const isNovoPivo = !ultimoPivoAnterior ||
        pivo.closePrice !== ultimoPivoAnterior.closePrice ||
        pivo.index !== ultimoPivoAnterior.index;

      if (isNovoPivo) {
        setUltimoPivoAnterior(pivo); // atualiza trava
      } else {
        console.log("ultimoPivoAnterior-ignorando repetição");
      }
    }

    if (TrendPivot) {
      const isNovoPivo = !ultimoPivoAtual ||
        TrendPivot.closePrice !== ultimoPivoAtual.closePrice ||
        TrendPivot.index !== ultimoPivoAtual.index;
      if (isNovoPivo) {
        setultimoPivoAtual(TrendPivot)
      } else {
        console.log("TrendPivot-ignorando repetição");

      }
    }

    if (pivoRallySec) {
      const isNovoPivoSec = !ultimoPivoSec ||
        pivoRallySec.closePrice !== ultimoPivoSec.closePrice ||
        pivoRallySec.index !== ultimoPivoSec.index;
      if (isNovoPivoSec) {
        setUltimoPivoSec(pivoRallySec)
      }
      else {
        console.log("ultimoPivoSec-ignorando repetição");
      }
    }

    if (pivotBreak) {
      const isNewTrend = !enteringTheTrendUpdate ||
        pivotBreak.closePrice !== enteringTheTrendUpdate.closePrice ||
        pivotBreak.index !== enteringTheTrendUpdate.index;
      if (isNewTrend) {
        setEnteringTheTrendUpdate(pivotBreak)
      } else {
        console.log("enteringTheTrendUpdate-ignorando repetição");
      }
    }

    if (rallySecExit) {
      const isNewRallysec = !rallySecExitUpdate ||
        rallySecExit.closePrice !== rallySecExitUpdate.closePrice ||
        rallySecExit.index !== rallySecExitUpdate.index;
      if (isNewRallysec) {
        setRallySecExitUpdate(rallySecExit)
      } else {
        console.log("rallySecExit-ignorando repetição");
      }
    }


    /**Função auxiliar para gerar id para unica execução */
    function buildEventId(pivo, reaction) {
      if (!pivo || !reaction) return null;
      return `${pivo.closeTime}-${reaction.closeTime}`;
    }


    // ===============================
    //  RETESTE DE TENDÊNCIA
    // ===============================
    if (pivo && naturalReaction && canExecuteReactionRef.current) {
      const atr = pivo.atr;
      const tolerance = atr / 3.5;
      const high = pivo.closePrice + tolerance;
      const low = pivo.closePrice - tolerance;
      const lowBuy = pivo.closePrice - (tolerance * 2);
      const highBuy = pivo.closePrice + (tolerance * 2);

      const buyPoint = pivo.closePrice + atr / 2;
      const sellPoint = pivo.closePrice - atr / 2;

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
        }

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
        }
      }
    }

    // ===============================
    // SAÍDA DE TENDÊNCIA
    // ===============================
    if (TrendPivot && naturalRally && canExecuteRallyRef.current) {
      const atr = TrendPivot.atr;
      const tolerance = atr / 3;
      const high = TrendPivot.closePrice + tolerance;
      const low = TrendPivot.closePrice - tolerance;
      const sellExit = TrendPivot.closePrice - atr / 2;
      const buyExit = TrendPivot.closePrice + atr / 2;

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
        }
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
        }
      }
    }


    // ======================================================================
    // RETEST NO PIVO DE RALLY EM UMA REAÇÃO NATURAL (pullback pós-breakout)
    // ======================================================================
    if (pivoRallyPrimary && naturalReaction && canExecuteReactionRef.current) {
      const atr = pivoRallyPrimary.atr;
      const tolerance = atr / 3;
      const high = pivoRallyPrimary.closePrice + tolerance;
      const low = pivoRallyPrimary.closePrice - tolerance;
      const buyPoint = pivoRallyPrimary.closePrice + atr / 2;
      const sellPoint = pivoRallyPrimary.closePrice - atr / 2;

      const eventId = buildEventId(pivoRallyPrimary, naturalReaction);

      if (eventId && lastRallyRetestIdRef.current !== eventId) {
        lastRallyRetestIdRef.current = eventId;

        // 🟢 Compra rally
        if (
          currentTrend === "Tendência Alta" &&
          naturalReaction.closePrice <= high &&
          naturalReaction.closePrice >= low
        ) {
          setRetestPoints([
            { name: "pivot", value: pivoRallyPrimary.closePrice },
            { name: "time", value: naturalReaction.closeTime },
            { name: "buy", value: buyPoint },
            { name: "stop", value: sellPoint },
            { name: "type", value: "ENTRY_BUY_RALLY" }
          ]);
        }
        // 🔴 Venda rally

        if (
          currentTrend === "Tendência Baixa" &&
          naturalReaction.closePrice <= high &&
          naturalReaction.closePrice >= low
        ) {
          setRetestPoints([
            { name: "pivot", value: pivoRallyPrimary.closePrice },
            { name: "time", value: naturalReaction.closeTime },
            { name: "sell", value: sellPoint },
            { name: "stop", value: buyPoint },
            { name: "type", value: "ENTRY_SELL_RALLY" }
          ]);
        }
      }
    }


    // ===============================
    // RETEST NO PIVO DE RALLY EM UMA 
    // REAÇÃO SECUNDÁRIA
    // ===============================
    if (pivoRally && naturalReactionSec && canExecuteReactionSecRef.current) {
      const atr = pivoRally.atr;
      const tolerance = atr / 3;
      const high = pivoRally.closePrice + tolerance;
      const low = pivoRally.closePrice - tolerance;
      const buyPoint = pivoRally.closePrice + atr / 2;
      const sellPoint = pivoRally.closePrice - atr / 2;

      const eventId = buildEventId(pivoRallyPrimary.closePrice, naturalReactionSec);

      if (eventId && lastRallyRetestIdPrimaryRef.current !== eventId) {
        lastRallyRetestIdPrimaryRef.current = eventId;

        // 🟢
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
        }
        // 🔴
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
        }
      }
    }


    // ===============================
    // SAÍDA REAÇÃO SECUNDÁRIA
    // ===============================
    if (pivoRallySec && rallySecundaria && canExecuteRallySecRef.current) {
      const atr = pivoRallySec.atr;
      const tolerance = atr / 3;
      const highExit = pivoRallySec.closePrice + tolerance;
      const lowExit = pivoRallySec.closePrice - tolerance;
      const sellExit = pivoRallySec.closePrice - atr / 2;
      const buyExit = pivoRallySec.closePrice + atr / 2;


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
            { name: "type", value: "Exit_Buy_ReactionSec" }
          ]);
        }
        // 🔴
        if (rallySecundaria &&
          currentTrend === "Tendência Baixa" &&
          rallySecundaria.closePrice >= lowExit &&
          rallySecundaria.closePrice <= highExit) {
          setRetestPoints([
            { name: "pivo", value: pivoRallySec.closePrice },
            { name: "time", value: rallySecundaria.closeTime },
            { name: "stop", value: buyExit },
            { name: "type", value: "Exit_sell_ReactionSec" }
          ]);
        }
      }
    };

    if (rallySecExit && rallySecundaria && canExecuteRallySecRef.current) {
      const atr = rallySecExit.atr;
      const tolerance = atr / 3;
      const highExit = rallySecExit.closePrice + tolerance;
      const lowExit = rallySecExit.closePrice - tolerance;
      const sellExit = rallySecExit.closePrice - atr / 2;
      const buyExit = rallySecExit.closePrice + atr / 2;


      const eventId = buildEventId(rallySecExit, rallySecundaria);

      if (eventId && lastRallyExitIdRef.current !== eventId) {
        lastRallyExitIdRef.current = eventId;

        // 🟢
        if (
          rallySecundaria &&
          currentTrend === "Tendência Alta" &&
          rallySecundaria.closePrice <= highExit &&
          rallySecundaria.closePrice >= lowExit) {
          setRetestPoints([
            { name: "pivo", value: rallySecExit.closePrice },
            { name: "time", value: rallySecundaria.closeTime },
            { name: "stop", value: sellExit },
            { name: "type", value: "Exit_Buy_ReactionSec" }
          ]);
        }
        // 🔴
        if (rallySecundaria &&
          currentTrend === "Tendência Baixa" &&
          rallySecundaria.closePrice >= lowExit &&
          rallySecundaria.closePrice <= highExit) {
          setRetestPoints([
            { name: "pivo", value: rallySecExit.closePrice },
            { name: "time", value: rallySecundaria.closeTime },
            { name: "stop", value: buyExit },
            { name: "type", value: "Exit_sell_ReactionSec" }
          ]);
        }
      }
    };

    // ===============================
    // ROMPIMENTO 
    // ===============================
    if (pivotBreak) {
      const atr = pivotBreak.atr;
      const pivotId = pivotBreak.closeTime;
      const type = pivotBreak.tipo;
      const sellExit = pivotBreak.closePrice - atr;
      const buyExit = pivotBreak.closePrice + atr;

      const pivoBuy = pivotBreak.closePrice - (atr / 2);
      const pivoSell = pivotBreak.closePrice + (atr / 2);


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
        }

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
        }
      }
    };


  },
    [
      simulationValueDataComplete,
    ]);
  console.log("Compra ou venda", retestPoints);


  /*#####################################################################
                        🎯logica de confirmação usando vppr 🎯
########################################################################*/
  const [signalsVppr, setSignalsVppr] = useState([]);/**Entrada pela média */
  const [signalsPowerVppr, setSignalsPowerVppr] = useState([]);/**Entrada acima do ponto Zero*/

  useEffect(() => {
    const movementsVppr = simulationValueDataCompleteVppr;
    if (!movementsVppr?.length) return;

    const vpprSignals = [];
    const vpprPowerSignals = [];

    for (let i = 0; i < movementsVppr.length; i++) {
      const current = movementsVppr[i];

      const percentage = current.vppr_ema * 0.1;
      const bandsUp = current.vppr_ema + percentage;
      const bandsLow = current.vppr_ema - percentage;

      if (current.vppr > bandsUp) {
        vpprSignals.push({
          index: i,
          signal: "buy",
          vppr: current.vppr,
          vppr_ema: current.vppr_ema,
        });
      } else if (current.vppr < bandsLow) {
        vpprSignals.push({
          index: i,
          signal: "sell",
          vppr: current.vppr,
          vppr_ema: current.vppr_ema,
        });
      }

      if (current.vppr > 0) {
        vpprPowerSignals.push({
          index: i,
          signal: "buy power",
          vppr: current.vppr,
          vppr_ema: current.vppr_ema,
        });
      } else if (current.vppr < 0) {
        vpprPowerSignals.push({
          index: i,
          signal: "sell power",
          vppr: current.vppr,
          vppr_ema: current.vppr_ema,
        });
      }
    }
    setSignalsVppr(vpprSignals);
    setSignalsPowerVppr(vpprPowerSignals);

  }, [simulationValueDataCompleteVppr]);


  /*#####################################################################
                        🎯logica de entrada e saída usando AMRSI 🎯
########################################################################*/
  const [signalsAmrsiSell, setSignalsAmrsiSell] = useState([]);/*(sobrecompra-parcial)*/
  const [signalsAmrsiBuy, setSignalsAmrsiBuy] = useState([]);/*(sobrevenda-parcial)*/

  const [signalsAmrsiSellReentry, setSignalsAmrsiSellReentry] = useState([]);/*(sobrevenda-reentrada)*/
  const [signalsAmrsiBuyReentry, setSignalsAmrsiBuyReentry] = useState([]);/*(sobrevenda-reentrada)*/

  useEffect(() => {
    const movementAmrsi = simulationValueDataCompleteRsi;
    if (!movementAmrsi?.length) return;

    const amRsiSignalBuy = [];
    const amRsiSinalSell = [];

    const amRsiSignalBuyReentry = [];
    const amRsiSinalSellReentry = [];

    let wasOverbought = false;
    let wasOversold = false;

    let overboughtReentry = false;
    let oversoldReentry = false;


    for (let i = 0; i < movementAmrsi.length; i++) {
      const { amrsi } = movementAmrsi[i];

      /* ---------- SOBRECOMPRA PARCIAL ---------- */
      // 1️⃣ entra em sobrecompra
      if (amrsi >= 80) {
        wasOverbought = true;
      }

      // 2️⃣ início da correção → venda
      if (wasOverbought && amrsi <= 70) {
        amRsiSinalSell.push({
          index: i,
          signal: "amrsi-partial-sell",
          amrsi,
        });
        wasOverbought = false; // reseta após sinal
      }

      /* ---------- SOBREVenda PARCIAL---------- */
      // 3️⃣ entra em sobrevenda
      if (amrsi <= 20) {
        wasOversold = true;
      }

      // 4️⃣ início da correção → compra
      if (wasOversold && amrsi >= 30) {
        amRsiSignalBuy.push({
          index: i,
          signal: "amrsi-partial-buy",
          amrsi,
        });
        wasOversold = false; // reseta após sinal
      }


      /* ---------- SOBRECOMPRA REENTRADA---------- */
      if (amrsi >= 70) {
        overboughtReentry = true;
      }
      if (overboughtReentry && amrsi <= 65) {
        amRsiSinalSellReentry.push({
          index: i,
          signal: "amrsi-Reentry-sell",
          amrsi,
        });
        overboughtReentry = false; // reseta após sinal
      }


      /* ---------- SOBREVENDA REENTRADA---------- */
      if (amrsi <= 30) {
        oversoldReentry = true;
      }
      if (oversoldReentry && amrsi >= 35) {
        amRsiSignalBuyReentry.push({
          index: i,
          signal: "amrsi-Reentry-buy",
          amrsi,
        });
        oversoldReentry = false; // reseta após sinal
      }
    }
    /**Guarda dados na variável de estado (SOBREVenda PARCIAL) */
    setSignalsAmrsiSell(amRsiSinalSell);
    setSignalsAmrsiBuy(amRsiSignalBuy);
    /**Guarda dados na variável de estado (SOBREVENDA REENTRADA) */
    setSignalsAmrsiSellReentry(amRsiSinalSellReentry);
    setSignalsAmrsiBuyReentry(amRsiSignalBuyReentry)

  }, [simulationValueDataCompleteRsi]);



  /**========================================================================
   * limpeza que limpa todos os tempos limite e intervalos na desmontagem: 
   * ========================================================================*/
  useEffect(() => {
    isPausedRef.current = isPaused;
  }, [isPaused]);

  useEffect(() => {
    isPausedRsiRef.current = isPausedRsi;
  }, [isPausedRsi]);

  useEffect(() => {
    isPausedVpprRef.current = isPausedVppr;
  }, [isPausedVppr]);

  useEffect(() => {
    if (realTime === "realTimeMode") {
      clearTimeout(simulationTimeoutRef.current);
      clearTimeout(simulationTimeoutSyncRef.current);
      offsetRefPrimary.current = 0;
      offsetRefRsi.current = 0;
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
      if (simulationControllerRef.current) {
        simulationControllerRef.current.abort();
      }
    }
  }, []);





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
            getMarketObservation()
          ], [savedSymbol]);
        } else {
          console.warn("Nenhum símbolo salvo encontrado!");
        }
      } catch (error) {
        console.error("Erro ao carregar os dados iniciais:", error);
      }
    }
    loadData();



    /*----------------------------
      Executa a cada 15 minutos
    ------------------------------*/
    if (realTime === "realTimeMode") {
      const now = new Date();
      const minutes = now.getMinutes();
      const seconds = now.getSeconds();
      const ms = now.getMilliseconds();

      const nextQuarter = Math.ceil(minutes / 15) * 15;
      const minutesToWait = nextQuarter === 60 ? 60 - minutes : nextQuarter - minutes;

      let delay =
        (minutesToWait * 60 * 1000) -
        (seconds * 1000) -
        ms;

      // ⏱️ atraso extra de 30 segundos
      delay += 30 * 1000;

      console.log(
        `⏳ Atualização programada para daqui a ${Math.round(delay / 1000)} segundos`
      );

      setTimeout(() => {
        updateAllData();
        setInterval(() => {
          updateAllData();
        }, 15 * 60 * 1000);

      }, delay);
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
          graphicDataOne(symbol),
          handleGetPoints(),
          saveMarketNotes(),
          getMarketObservation(),
          getRsi(symbol),
          getVppr(symbol),
        ]);
        console.log("✅ Dados atualizados em", new Date().toLocaleTimeString());
      } catch (error) {
        console.error("Erro ao atualizar dados:", error);
      }
    }
    ;
  }, [symbol, realTime]);


  const contextValue = {
    handleSave,
    handleRemove,
    values,
    labels,
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
    addSymbol,
    setAddSymbol,
    saveMarketNotes,
    setRemoveSymbol,
    data,
    setData,
    handleRemoveSymbol
  };

  return (

    <>
      <Toast ref={toast} position="bottom-right"
        className="custom-toast"
      />
      <AppContext.Provider value={contextValue}>
        {props.children}
      </AppContext.Provider>
    </>
  );
};

export default ContextApi;
