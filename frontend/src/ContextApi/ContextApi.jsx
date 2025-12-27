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
  const [values, setValues] = useState([]);
  const [labels, setLabels] = useState([]);
  const [dadosPrice, setDadosPrice] = useState([]);
  const [valuesSecondary, setValuesSecondary] = useState([]);
  const [labelsSecondary, setLabelsSecondary] = useState([]);
  const [dadosPriceSecondary, setDadosPriceSecondary] = useState([]);
  const [dadosPriceKey, setDadosPriceKey] = useState([]);
  const [labelsKey, setLabelsKey] = useState([]);
  const [valuesKey, setValueKey] = useState([]);
  const inputRefMain = useRef(null);
  const inputRefSec = useRef(null);
  const [symbol, setSymbol] = useState("");
  const [symbolSec, setSymbolSec] = useState("");
  const toast = useRef(null);
  const [activeButton, setActiveButton] = useState('');
  const [importantPoints, setImportantPoints] = useState([]);
  const [selectedPivots, setSelectedPivots] = useState([]);
  const [importantPointsKey, setImportantPointsKey] = useState([]);
  const [selectedPivotsKey, setSelectedPivotsKey] = useState([]);
  const [realTime, setRealTime] = useState("");
  const modo = realTime;
  const [rsi, setRsi] = useState([]);
  const [rsiTime, setRsiTime] = useState([]);


  const [dateSimulationStart, setDateSimulationStart] = useState("")
  const [dateSimulationEnd, setDateSimulationEnd] = useState("")
  const [days, setDays] = useState('')
  const [showDaysInput, setShowDaysInput] = useState(false);
  const [daysValue, setDaysValue] = useState('');

  const [dateSimulationStartSec, setDateSimulationStartSec] = useState("")
  const [dateSimulationEndSec, setDateSimulationEndSec] = useState("")
  const [daysSec, setDaysSec] = useState('')
  const [showDaysInputSec, setShowDaysInputSec] = useState(false);
  const [daysValueSec, setDaysValueSec] = useState('');

  const [simulationLabelData, setSimulationLabelData] = useState([]);
  const [simulationValueData, setSimulationValueData] = useState([]);
  const [simulationLabelDataSec, setSimulationLabelDataSec] = useState([]);
  const [simulationValueDataSec, setSimulationValueDataSec] = useState([]);
  const [simulationLabelDataKey, setSimulationLabelDataKey] = useState([]);
  const [simulationValueDataKey, setSimulationValueDataKey] = useState([]);
  const [simulationLabelDataRsi, setSimulationLabelDataRsi] = useState([]);
  const [simulationValueDataRsi, setSimulationValueDataRsi] = useState([]);
  const [simulationLabelDataPrice, setSimulationLabelDataPrice] = useState([]);
  const [simulationValueDataPrice, setSimulationValueDataPrice] = useState([]);


  const [simulationValueDataComplete, setSimulationValueDataComplete] = useState([]);
  const [simulationValueDataCompleteSec, setSimulationValueDataCompleteSec] = useState([]);
  const [simulationValueDataCompleteKey, setSimulationValueDataCompleteKey] = useState([]);
  const [simulationValueDataCompleteRsi, setSimulationValueDataCompleteRsi] = useState([]);
  const [simulationValueDataCompletePrice, setSimulationValueDataCompletePrice] = useState([]);




  const simulationTimeoutRef = useRef(null);
  const [isPaused, setIsPaused] = useState(true);
  const isPausedRef = useRef(isPaused);


  const simulationSecTimeoutRef = useRef(null);
  const [isPausedSec, setIsPausedSec] = useState(false);
  const isPausedSecRef = useRef(isPausedSec);

  const simulationTimeoutSyncRef = useRef(null);
  const [isPausedKey, setIsPausedKey] = useState(false)
  const isPausedKeyRef = useRef(isPausedKey);

  const simulationRsiTimeoutRef = useRef(null);
  const [isPausedRsi, setIsPausedRsi] = useState(false);
  const isPausedRsiRef = useRef(isPausedRsi);

  const [isPausedPrice, setIsPausedPrice] = useState(false);
  const isPausedPriceRef = useRef(isPausedPrice)

  const toastShownRef = useRef(false);

  let offsetRefPrimary = 0;
  let offsetRefSecondary = 0;
  let offsetRefKey = 0;
  let offsetRefRsi = 0;
  let offsetRefPrice = 0;

  const period = 14; /* periodo do AMRSI */



  /*-----------------------------------------------
  Função para alternar entre simulação e real time 
  --------------------------------------------------*/
  const LoadGraphicDataOne = async (savedSymbol, savedSymbolSec) => {
    if (realTime === "real") {
      await graphicDataOne(savedSymbol);
      await graphicDataKey();
      await graphicDataSecondary(savedSymbolSec);
      await getRsi(savedSymbol)

      if (!toastShownRef.current) {
        toast.current.show({
          severity: "success",
          summary: "Modo",
          detail: "Conta real",
          life: 5000
        });
        toastShownRef.current = true;
      }
    }
    else if (realTime === "simulation") {
      await getRsi();
      await simulateStepSync(savedSymbol);
      toast.current.show({
        severity: "success",
        summary: "Modo",
        detail: "Simulação",
        life: 5000
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
  const simulateStepSync = async (symbolPrimary, symbolSecondary) => {
    // se não estiver em modo simulation, cancela
    if (realTime !== 'simulation' && dateSimulationStart !== 'Nada') {
      console.log("🛑 Simulação cancelada: modo não é 'simulation'");
      return;
    }

    // cancela timeout anterior (evita acumular)
    clearTimeout(simulationTimeoutSyncRef.current);

    try {
      // helper para buscar 1 candle por endpoint/offset
      const fetchOne = async (endpoint, offset) => {
        const resp = await axios.get(`${endpoint}?offset=${offset}&limit=1`);
        return (resp.data && resp.data.length) ? resp.data[0] : null;
      };

      // endpoints
      const epPrimary = `${url}/api/simulate_price_atr`;
      const epSecondary = `${url}/api/simulate_price_atr_sec`;
      const epKey = `${url}/api/simulate_price_atr_key`;
      const epRsi = `${url}/api/simulate_amrsi`;
      const epPriceCurrent = `${url}/api/simulate_current_price`;


      // checa pausa no primary antes de prosseguir
      if (isPausedRef.current) {
        console.log("⏸️ Simulação pausada (primary). Tentando novamente em 500ms...");
        simulationTimeoutSyncRef.current = setTimeout(() => simulateStepSync(symbolPrimary, symbolSecondary), 500);
        return;
      }

      // pega próximo candle do primary (driver)
      let candleP = await fetchOne(epPrimary, offsetRefPrimary);
      if (!candleP) {
        console.log("✅ Simulação finalizada (primary terminou)");
        return;
      }

      // data (somente parte data "YYYY-MM-DD" para sincronização por data)
      let dateP = candleP.closeTime;

      // registra o primary (use closeTime completo para label, para distinguir múltiplos)
      setSimulationValueData(prev => [...prev, parseFloat(candleP.closePrice)]);
      setSimulationLabelData(prev => [...prev, candleP.closeTime]);
      setSimulationValueDataComplete(prev => [...prev, candleP]);

      // avança o offset do primary para o próximo passo
      offsetRefPrimary += 1;

      // agora, processa todos os secondary até <= dateP
      while (true) {
        if (isPausedSecRef.current) {
          console.log("⏸️ Pausado durante processamento do secondary. Retomando depois...");
          simulationTimeoutSyncRef.current = setTimeout(() => simulateStepSync(symbolPrimary, symbolSecondary), 500);
          return;
        }

        let candleS = await fetchOne(epSecondary, offsetRefSecondary);
        if (!candleS) {
          break;
        }

        let dateS = candleS.closeTime;
        if (dateS > dateP) {
          // próximo é depois, para sem avançar
          break;
        }

        // registra o secondary
        setSimulationValueDataSec(prev => [...prev, parseFloat(candleS.closePrice)]);
        setSimulationLabelDataSec(prev => [...prev, candleS.closeTime]);
        setSimulationValueDataCompleteSec(prev => [...prev, candleS]);

        // avança para o próximo
        offsetRefSecondary += 1;
      }

      // agora, processa todos os key até <= dateP
      while (true) {
        if (isPausedKeyRef.current) {
          console.log("⏸️ Pausado durante processamento do key. Retomando depois...");
          simulationTimeoutSyncRef.current = setTimeout(() => simulateStepSync(symbolPrimary, symbolSecondary), 500);
          return;
        }

        let candleK = await fetchOne(epKey, offsetRefKey);

        if (!candleK) {
          break;
        }

        let dateK = candleK.closeTime;
        if (dateK > dateP) {
          // próximo é depois, para sem avançar
          break;
        }

        // registra o key
        setSimulationValueDataKey(prev => [...prev, parseFloat(candleK.closePrice)]);
        setSimulationLabelDataKey(prev => [...prev, candleK.closeTime]);
        setSimulationValueDataCompleteKey(prev => [...prev, candleK]);

        // avança para o próximo
        offsetRefKey += 1;
      }

      // agora, processa todos os RSI até <= dateP
      while (true) {
        if (isPausedRsiRef.current) {
          console.log("⏸️ Pausado durante processamento do RSI. Retomando depois...");
          simulationTimeoutSyncRef.current = setTimeout(() => simulateStepSync(symbolPrimary, symbolSecondary), 500);
          return;
        }

        let candleRsi = await fetchOne(epRsi, offsetRefRsi);
        if (!candleRsi) {
          break;
        }

        let dateRsi = candleRsi.time;
        if (dateRsi > dateP) {
          // próximo é depois, para sem avançar
          break;
        }

        // registra RSI
        const value = candleRsi.amrsi ?? candleRsi.rsi_ma ?? candleRsi.rsi;
        setSimulationValueDataRsi(prev => [...prev, parseFloat(value)]);
        setSimulationLabelDataRsi(prev => [...prev, candleRsi.time]);
        setSimulationValueDataCompleteRsi(prev => [...prev, candleRsi]);

        // avança para o próximo
        offsetRefRsi += 1;
      }

      while (true) {
        if (isPausedPriceRef.current) {
          console.log("⏸️ Pausado durante processamento do secondary. Retomando depois...");
          simulationTimeoutSyncRef.current = setTimeout(() => simulateStepSync(symbolPrimary, symbolSecondary), 500);
          return;
        }

        // pega próximo candle do preços completos atuais (driver)
        let candlePc = await fetchOne(epPriceCurrent, offsetRefPrice);
        if (!candlePc) {
          console.log("✅ Simulação finalizada (preços completos terminou)");
          return;
        }


        // data (somente parte data "YYYY-MM-DD" para sincronização por data)
        let datePc = candlePc.time;
        if (datePc > dateP) {
          // próximo é depois, para sem avançar
          break;
        }


        // registra o primary (use closeTime completo para label, para distinguir múltiplos)
        setSimulationValueDataPrice(prev => [...prev, parseFloat(candlePc.close)]);
        setSimulationLabelDataPrice(prev => [...prev, candlePc.time]);
        setSimulationValueDataCompletePrice(prev => [...prev, candlePc]);

        // avança o offset do primary para o próximo passo
        offsetRefPrice += 1;
      }


      // agenda próxima iteração (próximo primary + catch-up)
      simulationTimeoutSyncRef.current = setTimeout(() => {
        simulateStepSync(symbolPrimary, symbolSecondary);
      }, 300);

    } catch (error) {
      console.error("❌ Erro na simulateStepSync:", error);
      clearTimeout(simulationTimeoutSyncRef.current);
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
      await axios.post(
        `${url}/api/filter_price_key`,
        {}, // corpo vazio
        {
          params: {
            modo: modo,
            symbol: symbol,
            symbol_sec: symbolSec
          }
        }
      );

      getDateSimulation();

      // ✅ Toast de sucesso
      toast.current.show({
        severity: "success",
        summary: 'Sucesso!',
        detail: `Os dados para simular foram baixados!`,
        life: 5000
      });

      console.log("Resposta API:", response.data);
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

  /*-----------------------------------------------------------------
    2️⃣ Função para Selecionae datas para simulação do ativo Secundário
   -------------------------------------------------------------------*/
  const dateSimulationSec = async () => {
    try {
      const response = await axios.post(
        `${url}/api/update_klines_sec`,
        {}, // corpo vazio
        {
          params: {
            date_start: dateSimulationStartSec,
            date_end: dateSimulationEndSec,
            days: daysValueSec,
            symbol: symbolSec
          }
        }
      );

      // 🔹Chamada da API para enviar o modo para simular a classificação
      await axios.post(`${url}/api/filter_price_atr_second?symbol=${symbolSec}&modo=${modo}`);
      await axios.post(
        `${url}/api/filter_price_key`,
        {}, // corpo vazio
        {
          params: {
            modo: modo,
            symbol: symbol,
            symbol_sec: symbolSec
          }
        }
      );

      getDateSimulationSec()

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

  /*-------------------------------------------------
 2️⃣ Busca as datas da simulação do ativo Primária
 ---------------------------------------------------*/
  const getDateSimulationSec = async () => {
    try {
      const response = await axios.get(`${url}/api/get_date/simulation_sec`);
      const data = response.data;
      setDaysSec(data.days || '');
      setDateSimulationStartSec(data.days_start || '')
      setDateSimulationEndSec(data.days_end || '')

    } catch (error) {
      console.error("Erro na API para recuperar datas:", error);
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
  const graphicDataOne = async (symbolParam) => {
    // 🧹 Limpa dados da simulação
    clearTimeout(simulationTimeoutRef.current);
    try {
      const response = await axios.get(`${url}/api/filter_price_atr?symbol=${symbolParam}`);
      const data = response.data;
      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => {
        return p.closeTime.split(' ')[0];
      });

      setDadosPrice(data);
      setLabels(time);
      setValues(prices);

    } catch (error) {
      console.error("❌ Erro ao buscar dados em tempo real:", error);
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
      graphicDataKey();

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




  /*#####################################################################
                       2️⃣📈INICIO ATIVO SECUNDÁRIO📈2️⃣
  ########################################################################*/
  /*-------------------------------------------------
    2️⃣ Função para buscar dados do ativo Primária
   --------------------------------------------------*/
  const graphicDataSecondary = async (symbolSecParam) => {
    if (!symbolSecParam) return;

    try {
      const response = await axios.get(`${url}/api/filter_price_atr_second?symbol=${symbolSecParam}`);
      const data = response.data;

      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => {
        return p.closeTime.split(' ')[0];
      });

      setDadosPriceSecondary(data);
      setLabelsSecondary(time);
      setValuesSecondary(prices)
    } catch (error) {
      console.error("Erro na API para recuperar símbolos:", error);
    }
  }
  /*----------------------------------------------------------------
  🔍2️⃣Faz pequisa do simbolo envia para backend (do ativo primária)
  -----------------------------------------------------------------*/
  const handleSearchSec = async (event) => {
    event?.preventDefault();
    inputRefSec.current.focus();

    const symbol = inputRefSec.current.value.toUpperCase();
    if (!symbol) return;

    try {
      const response = await axios.get(`${url}/api/filter_price_atr_second?symbol=${symbol}`);
      const data = response.data;

      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => p.closeTime);

      setDadosPriceSecondary(data);
      setLabelsSecondary(time);
      setValuesSecondary(prices);
      setSymbolSec(symbol);
      graphicDataKey();

      // ✅ Toast de sucesso
      toast.current.show({
        severity: "success",
        summary: 'Busca realizada',
        detail: `Símbolo ${symbol} carregado com sucesso!`,
        life: 5000
      });

    } catch (error) {
      // ❌ Toast de erro
      toast.current.show({
        severity: 'error',
        summary: 'Erro na busca',
        detail: `Não foi possível buscar o símbolo: ${symbol}`,
        life: 5000
      });

      console.error('Erro ao buscar dados:', error);
    }
    inputRefSec.current.value = "";
  };
  /*------------------------------
  🔍2️⃣Busca o simbolo secundário
 --------------------------------*/
  const getSymbolSec = async () => {
    try {
      const response = await axios.get(url + "/api/last_symbol_second")
      const data = response.data;
      setSymbolSec(data.symbol);
      return data.symbol;
    } catch (error) {
      console.error("Erro na API para recuperar símbolos:", error);
    }
  };
  /*#####################################################################
                         2️⃣📈FIM ATIVO SECUNDÁRIO📈2️⃣
  ########################################################################*/




  /*#####################################################################
                       🔑INICIO ATIVO CHAVE🔑
  ########################################################################*/
  const graphicDataKey = async () => {
    try {
      const response = await axios.get(url + "/api/filter_price_key");
      const data = response.data;
      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => {
        return p.closeTime.split(' ')[0];
      });

      setDadosPriceKey(data);
      setLabelsKey(time);
      setValueKey(prices);

    } catch (error) {
      console.error("Erro na API:", error);
    }
  };
  /*#####################################################################
                          🔑FIM ATIVO SECUNDÁRIO🔑
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
        graphicDataSecondary(symbolSec)
        graphicDataKey()
        handleGetPoints()
        handleGetPointsKey()
        graphicDataOne(symbol)


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
  /*--------------------------------
    pega pontos de pivot importantes chaves
  ----------------------------------*/
  const handleGetPointsKey = async () => {
    try {
      const response = await axios.get(`${url}/api/trend_clarifications_key`);
      const data = response.data;
      if (data) {
        setImportantPointsKey(data);
      }
    } catch (error) {
      console.error("Erro ao buscar ponto importante:", error);
    }
  }
  /*------------------------------------------
   Função para adicionar/remover pivôs chaves
  --------------------------------------------*/
  const togglePivotKey = (label, price) => {
    setSelectedPivotsKey(prev => {
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
      const time = data.map(p => p.time.split(' ')[0]);
      setRsi([...value])
      setRsiTime([...time])
    } catch (error) {
      console.error("Erro ao buscar dados do RSI", error);
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
                        🎯logica de compra alta início🎯
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

  // variaveis para evitar reprocessamento
  const lastTrendRetestIdRef = useRef(null);
  const lastTrendExitIdRef = useRef(null);
  const lastRallyRetestIdRef = useRef(null);
  const lastRallyRetestIdPrimaryRef = useRef(null);
  const lastRallyExitIdRef = useRef(null);
  const lastSecondaryExitIdRef = useRef(null);
  const lastBreakoutIdRef = useRef(null);
  const lastBreakoutRetestIdRef = useRef(null);


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
          setCurrentTrend('Tendência Alta')
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
          setCurrentTrend('Tendência Baixa')
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
      let encontrouRallySecundaria = false;
      let ultimoPivoRallySec = false;
      let encontrouRallyNaturalParaSec = false;


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
        if (!encontrouRallyNaturalParaSec && type.includes('Rally Natural')) {
          ultimoPivoRallySec = {
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

        // Verificar se é uma Reação Natural (pode ser "Reação Natural (Alta)" ou "Reação Natural (fundo)")
        if (encontrouRallyNaturalParaSec && type.includes('Reação secundária')) {
          pivotReactionSec = {
            closePrice: movement.closePrice,
            closeTime: movement.closeTime,
            tipo: movement.tipo,
            atr: movement.atr,
            index: i
          }
          break;
        }
      }
      return { naturalRally, ultimoPivoRally, ultimoPivoRallySec };
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
          continue;
        }
      }

      return { enteringTheTrend };
    };






    const { ultimoTopoAlta, ultimoFundoBaixa } = identifyHighTop(movements);
    const { naturalRally, ultimoPivoRally, ultimoPivoRallySec } = identifyRetestRally(movements)
    const { enteringTheTrend } = identifyBreakoutTrend(movements);


    let ultimoTopo = null;
    let rally = null;
    let rallyPivo = null;
    let rallySec = null;
    let trend = null;



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
    const pivotBreak = trendPivotToRetest[trendPivotToRetest.length - 1];


    if (pivo) {
      const isNovoPivo = !ultimoPivoAnterior ||
        pivo.closePrice !== ultimoPivoAnterior.closePrice ||
        pivo.index !== ultimoPivoAnterior.index;

      if (isNovoPivo) {
        setUltimoPivoAnterior(pivo); // atualiza trava
      } else {
        console.log("Pivô repetido pivô Penultimo - ignorando >");
      }
    }

    if (TrendPivot) {
      const isNovoPivo = !ultimoPivoAtual ||
        TrendPivot.closePrice !== ultimoPivoAtual.closePrice ||
        TrendPivot.index !== ultimoPivoAtual.index;
      if (isNovoPivo) {
        console.log("NOVO pivô Atual >:", TrendPivot);
      } else {
        console.log("Pivô repetido pivô Atual - ignorando >");
      }
    }

    if (pivoRallySec) {
      const isNovoPivoSec = !ultimoPivoSec ||
        pivoRallySec.closePrice !== ultimoPivoSec.closePrice ||
        pivoRallySec.index !== ultimoPivoSec.index;
      if (isNovoPivoSec) {
        console.log("Pivô sec atual > ", pivoRallySec);
      }
      else {
        console.log("Pivô sec repetido pivô Atual - ignorando >");
      }
    }

    if (pivotBreak) {
      const isNewTrend = !enteringTheTrendUpdate ||
        pivotBreak.closePrice !== enteringTheTrendUpdate ||
        pivotBreak.index !== enteringTheTrendUpdate.index;
      if (isNewTrend) {
        console.log("Rompimento da tendência atual > ", pivotBreak);
      } else {
        console.log("Rompimento da tendência atual repetido - ignorando > ", pivotBreak);
      }
    }



    function buildEventId(pivo, reaction) {
      if (!pivo || !reaction) return null;
      return `${pivo.closeTime}-${reaction.closeTime}`;
    }

    // ===============================
    // 3) RETESTE DE TENDÊNCIA
    // ===============================
    if (pivo && naturalReaction) {
      const atr = pivo.atr;
      const tolerance = atr / 4;
      const high = pivo.closePrice + tolerance;
      const low = pivo.closePrice - tolerance;
      const buyPoint = pivo.closePrice + atr / 2;
      const sellPoint = pivo.closePrice - atr / 2;

      const eventId = buildEventId(pivo, naturalReaction);

      if (eventId && lastTrendRetestIdRef.current !== eventId) {
        lastTrendRetestIdRef.current = eventId;

        // 🟢 Compra
        if (
          ultimoTopoAlta &&
          naturalReaction.closePrice >= low &&
          naturalReaction.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivo", value: pivo },
            { name: "reaction", value: naturalReaction },
            { name: "buy", value: buyPoint },
            { name: "stop", value: sellPoint },
            { name: "type", value: "ENTRY_BUY_TREND" }
          ]);
        }

        // 🔴 Venda
        if (
          ultimoFundoBaixa &&
          naturalReaction.closePrice >= low &&
          naturalReaction.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivo", value: pivo },
            { name: "reaction", value: naturalReaction },
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
    if (TrendPivot && naturalRally) {
      const atr = TrendPivot.atr;
      const tolerance = atr / 4;
      const high = TrendPivot.closePrice + tolerance;
      const low = TrendPivot.closePrice - tolerance;
      const sellExit = TrendPivot.closePrice - atr / 2;
      const buyExit = TrendPivot.closePrice + atr / 2;

      const eventId = buildEventId(TrendPivot, naturalRally);

      if (eventId && lastTrendExitIdRef.current !== eventId) {
        lastTrendExitIdRef.current = eventId;

        // 🟢
        if (
          currentTrend === "Tendência Alta" &&
          naturalRally.closePrice >= low &&
          naturalRally.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivot", value: TrendPivot },
            { name: "reaction", value: naturalRally },
            { name: "buyExit", value: buyExit },
            { name: "type", value: "EXIT_BUY_TREND" }
          ]);
        }
        // 🔴
        if (
          currentTrend === "Tendência Baixa" &&
          naturalRally.closePrice >= low &&
          naturalRally.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivot", value: TrendPivot },
            { name: "reaction", value: naturalRally },
            { name: "sellExit ", value: sellExit },
            { name: "type", value: "EXIT_SELL_TREND" }
          ]);
        }
      }
    }

    // ===============================
    // RETESTE DE RALLY
    // ===============================

    if (pivoRally && naturalReaction) {
      const atr = pivoRally.atr;
      const tolerance = atr / 4;
      const high = pivoRally.closePrice + tolerance;
      const low = pivoRally.closePrice - tolerance;
      const buyPoint = pivoRally.closePrice + atr / 2;
      const sellPoint = pivoRally.closePrice - atr / 2;

      const eventId = buildEventId(pivoRally, naturalReaction);

      if (eventId && lastRallyRetestIdRef.current !== eventId) {
        lastRallyRetestIdRef.current = eventId;

        // 🟢
        if (
          currentTrend === "Tendência Alta" &&
          naturalReaction.closePrice >= low &&
          naturalReaction.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivot", value: pivoRally },
            { name: "reaction", value: naturalReaction },
            { name: "buy", value: buyPoint },
            { name: "stop", value: sellPoint },
            { name: "type", value: "ENTRY_BUY_RALLY" }
          ]);
        }
        // 🔴
        if (
          currentTrend === "Tendência Baixa" &&
          naturalReaction.closePrice >= low &&
          naturalReaction.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivot", value: pivoRally },
            { name: "reaction", value: naturalReaction },
            { name: "sell", value: sellPoint },
            { name: "stop", value: buyPoint },
            { name: "type", value: "ENTRY_SELL_RALLY" }
          ]);
        }
      }
    }

    // ===============================
    // SAÍDA DE RALLY
    // ===============================
    if (TrendPivot && naturalRally) {
      const atr = TrendPivot.atr;
      const tolerance = atr / 4;
      const high = TrendPivot.closePrice + tolerance;
      const low = TrendPivot.closePrice - tolerance;
      const sellExit = TrendPivot.closePrice - atr / 2;
      const buyExit = TrendPivot.closePrice + atr / 2;

      const eventId = buildEventId(TrendPivot, naturalRally);

      if (eventId && lastRallyExitIdRef.current !== eventId) {
        lastRallyExitIdRef.current = eventId;

        // 🟢
        if (
          currentTrend === "Tendência Alta" &&
          naturalRally.closePrice >= low &&
          naturalRally.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivot", value: TrendPivot },
            { name: "reaction", value: naturalRally },
            { name: "Stop Exit", value: sellExit },
            { name: "type", value: "EXIT_BUY_RALLY" }
          ]);
        }
        // 🔴
        if (
          currentTrend === "Tendência Baixa" &&
          naturalRally.closePrice >= low &&
          naturalRally.closePrice <= high
        ) {
          setRetestPoints([
            { name: "pivot", value: TrendPivot },
            { name: "reaction", value: naturalRally },
            { name: "Stop Exit", value: buyExit },
            { name: "type", value: "EXIT_SELL_RALLY" }
          ]);
        }
      }
    }

    // ===============================
    // RETEST NO PIVO DE RALLY EM UMA 
    // REAÇÃO SECUNDÁRIA
    // ===============================


    if (pivoRallyPrimary && naturalReactionSec) {
      const atr = pivoRallyPrimary.atr;
      const tolerance = atr / 3;
      const high = pivoRallyPrimary.closePrice + tolerance;
      const low = pivoRallyPrimary.closePrice - tolerance;
      const buyPoint = pivoRallyPrimary.closePrice + atr / 2;
      const sellPoint = pivoRallyPrimary.closePrice - atr / 2;

      const eventId = buildEventId(pivoRallyPrimary, naturalReactionSec);

      if (eventId && lastRallyRetestIdPrimaryRef.current !== eventId) {
        lastRallyRetestIdPrimaryRef.current = eventId;

        // 🟢
        if (
          currentTrend === "Tendência Alta" &&
          naturalReactionSec.closePrice <= high &&
          naturalReactionSec.closePrice >= low

        ) {
          setRetestPoints([
            { name: "pivot", value: naturalReactionSec },
            { name: "reactionSec", value: naturalReactionSec },
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
            { name: "pivot", value: pivoRally },
            { name: "reaction", value: naturalReactionSec },
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
    if (pivoRallySec && rallySecundaria) {
      const atr = pivoRallySec.atr; const tolerance = atr / 4;
      const highExit = pivoRallySec.closePrice + tolerance;
      const lowExit = pivoRallySec.closePrice - tolerance;
      const sellExit = pivoRallySec.closePrice - atr / 2;
      const buyExit = pivoRallySec.closePrice + atr / 2;

      const eventId = buildEventId(pivoRallySec, rallySecundaria);

      if (eventId && lastSecondaryExitIdRef.current !== eventId) {
        lastSecondaryExitIdRef.current = eventId;

        // 🟢
        if (rallySecundaria &&
          currentTrend === "Tendência Alta" &&
          rallySecundaria >= lowExit &&
          rallySecundaria <= highExit) {
          setRetestPoints([
            { name: "pivo", value: pivoRallySec },
            { name: "naturalReactionSec", value: rallySecundaria },
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
          { name: "pivo", value: pivoRallySec },
          { name: "naturalReactionSec", value: rallySecundaria },
          { name: "stop buy", value: buyExit },
          { name: "type", value: "Exit_sell_ReactionSec" }]);
        }
      }
    }

    // ===============================
    // ROMPIMENTO
    // ===============================
    if (pivotBreak) {
      const atr = pivotBreak.atr;
      const pivotId = pivotBreak.closeTime;
      const type = pivotBreak.tipo;
      const sellExit = pivotBreak.closePrice - atr;
      const buyExit = pivotBreak.closePrice + atr;


      if (lastBreakoutIdRef.current !== pivotId) {
        lastBreakoutIdRef.current = pivotId;

        // 🟢
        if (type === "Tendência Alta (compra)") {
          setRetestPoints([
            { name: "pivo", value: pivotBreak.closePrice },
            { name: "pivotBreak", value: pivotBreak },
            { name: "buy", value: pivotBreak.closePrice },
            { name: "stop", value: sellExit }]);
        }

        // 🔴
        if (type === "Tendência Baixa (venda)") {
          setRetestPoints([
            { name: "pivo", value: pivotBreak.closePrice },
            { name: "pivotBreak", value: pivotBreak },
            { name: "Sel", value: pivotBreak.closePrice },
            { name: "stop", value: buyExit }]);
        }
      }

    };


    // acabar de fazer o retest no primeiro pivot de tendencia
    if (pivotBreak && naturalReaction) {
      const type = pivotBreak.tipo;
      const atr = pivotBreak.atr;
      const tolerance = atr / 2;
      const pivotUp = pivotBreak.closePrice - tolerance
      const pivotLow = pivotBreak.closePrice + tolerance
      const highUp = pivotBreak.closePrice - tolerance;
      const highLow = pivotBreak.closePrice + tolerance;
      const low = pivotBreak.closePrice - atr;
      const sellPoint = low - tolerance * 4;
      const buyPoint = highUp + tolerance * 4;

      const eventId = buildEventId(pivotBreak, naturalReaction);

      if (eventId && lastBreakoutRetestIdRef.current !== eventId) {
        lastBreakoutRetestIdRef.current = eventId;
        // 🟢
        if (
          type === "Tendência Alta (compra)" &&
          naturalReaction.closePrice >= low &&
          naturalReaction.closePrice <= highUp
        ) {
          setRetestPoints([
            { name: "pivo", value: pivotUp },
            { name: "pivotBreakRetest", value: pivotBreak },
            { name: "buy", value: pivotBreak.closePrice },
            { name: "stop", value: sellPoint }
          ]);
        }
        // 🔴
        if (
          type === "Tendência Baixa (venda)" &&
          naturalReaction.closePrice >= low &&
          naturalReaction.closePrice <= highLow
        ) {
          setRetestPoints([
            { name: "pivo", value: pivotLow },
            { name: "pivotBreakRetest", value: pivotBreak },
            { name: "sel", value: pivotBreak.closePrice },
            { name: "stop", value: buyPoint }
          ]);
        }
      }
    }

  },
    [
      simulationValueDataComplete,

    ]);
  console.log("Compra ou venda", retestPoints);




  useEffect(() => {
    if (realTime === "real") {
      clearTimeout(simulationTimeoutRef.current);
      offsetRefPrimary = 0;
      offsetRefSecondary = 0;
      offsetRefKey = 0;
      setSimulationValueData([]);
      setSimulationLabelData([]);
      setSimulationValueDataSec([]);
      setSimulationLabelDataSec([]);
      setSimulationValueDataKey([]);
      setSimulationLabelDataKey([]);

    }
  }, [realTime]);

  useEffect(() => {
    if (realTime === "real") {
      clearTimeout(simulationSecTimeoutRef.current);
      setSimulationLabelDataSec([]);
      setSimulationValueDataSec([]);
      offsetRefSecondary = 0;
      offsetRefPrimary = 0;
    }
  }, [realTime]);


  useEffect(() => {
    isPausedRef.current = isPaused;
  }, [isPaused]);
  useEffect(() => {
    isPausedSecRef.current = isPausedSec
  }, [isPausedSec]);



  useEffect(() => {
    async function loadData() {
      try {
        const savedSymbol = await getSymbol();
        const savedSymbolSec = await getSymbolSec();

        if (savedSymbol || savedSymbolSec) {
          await Promise.all([
            LoadGraphicDataOne(savedSymbol, savedSymbolSec),
            handleGetTime(),
            handleGetPoints(),
            handleGetPointsKey(),
            getDateSimulation(),
            getDateSimulationSec(),

          ], [savedSymbol, savedSymbolSec]);
        } else {
          console.warn("Nenhum símbolo salvo encontrado!");
        }
      } catch (error) {
        console.error("Erro ao carregar os dados iniciais:", error);
      }
    }
    loadData();

    /* Executa a cada uma hora */
    if (realTime === "real") {
      const now = new Date();
      const minutes = now.getMinutes();
      const seconds = now.getSeconds();
      const ms = now.getMilliseconds();

      // Quanto tempo falta até a próxima hora cheia
      const delay = ((61 - minutes) * 60 * 1000) - (seconds * 1000) - ms;
      console.log(`⏳ Atualização programada para daqui a ${Math.round(delay / 1000)} segundos`);

      setTimeout(() => {
        // Atualiza na hora cheia
        updateAllData();

        // Depois executa a cada 60 minutos
        setInterval(() => {
          updateAllData();
        }, 61 * 60 * 1000);
      }, delay);
    };

    async function updateAllData() {
      try {
        await Promise.all([
          graphicDataSecondary(symbolSec),
          graphicDataOne(symbol),
          graphicDataKey(),
          handleGetPoints(),
          handleGetPointsKey(),
        ]);
        console.log("✅ Dados atualizados em", new Date().toLocaleTimeString());
      } catch (error) {
        console.error("Erro ao atualizar dados:", error);
      }
    }
    ;
  }, [symbol, symbolSec, realTime]);


  const contextValue = {
    handleSave,
    handleRemove,
    values,
    labels,
    dadosPrice,
    dadosPriceSecondary,
    valuesSecondary,
    labelsSecondary,
    theme,
    setTheme,
    dadosPriceKey,
    labelsKey,
    valuesKey,
    handleSearch,
    inputRefMain,
    inputRefSec,
    handleSearchSec,
    symbol,
    symbolSec,
    handleClickTime,
    activeButton,
    importantPoints,
    togglePivot,
    selectedPivots,
    importantPointsKey,
    togglePivotKey,
    selectedPivotsKey,
    setRealTime,
    realTime,
    simulationLabelData,
    simulationValueData,
    isPaused,
    setIsPaused,
    isPausedRef,
    simulationLabelDataSec,
    simulationValueDataSec,
    isPausedSec,
    setIsPausedSec,
    simulationLabelDataKey,
    simulationValueDataKey,
    simulationValueDataComplete,
    simulationValueDataCompleteSec,
    simulationValueDataCompleteKey,
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
    showDaysInputSec,
    daysSec,
    daysValueSec,
    dateSimulationStartSec,
    setDateSimulationEndSec,
    setDateSimulationStartSec,
    dateSimulationEndSec,
    dateSimulationSec,
    setDaysValueSec,
    setShowDaysInputSec,
    rsi,
    rsiTime,
    simulationValueDataRsi,
    simulationLabelDataRsi,
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
