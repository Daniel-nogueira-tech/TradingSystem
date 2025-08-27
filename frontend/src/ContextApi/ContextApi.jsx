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


  const [simulationValueDataComplete, setSimulationValueDataComplete] = useState([]);
  const [simulationValueDataCompleteSec, setSimulationValueDataCompleteSec] = useState([]);
  const [simulationValueDataCompleteKey, setSimulationValueDataCompleteKey] = useState([]);
  const [simulationValueDataCompleteRsi, setSimulationValueDataCompleteRsi] = useState([]);


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

  const toastShownRef = useRef(false);

  let offsetRefPrimary = 0;
  let offsetRefSecondary = 0;
  let offsetRefKey = 0
  let offsetRefRsi = 0

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
    let dateP = candleP.closeTime.split(' ')[0];

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

      let dateS = candleS.closeTime.split(' ')[0];
      if (dateS >= dateP) {
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

      let dateK = candleK.closeTime.split(' ')[0];
      if (dateK >= dateP) {
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

      let dateRsi = candleRsi.time.split(' ')[0];
      if (dateRsi >= dateP) {
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
  console.log(daysSec);
  
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
    simulationLabelDataRsi


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
