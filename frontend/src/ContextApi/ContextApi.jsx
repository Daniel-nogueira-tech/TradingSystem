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
  const [simulationLabelData, setSimulationLabelData] = useState([]);
  const [simulationValueData, setSimulationValueData] = useState([]);
  const [simulationLabelDataSec, setSimulationLabelDataSec] = useState([]);
  const [simulationValueDataSec, setSimulationValueDataSec] = useState([]);
  const [simulationLabelDataKey, setSimulationLabelDataKey] = useState([]);
  const [simulationValueDataKey, setSimulationValueDataKey] = useState([]);
  const simulationTimeoutRef = useRef(null);
  const [isPaused, setIsPaused] = useState(false);
  const isPausedRef = useRef(isPaused);
  const modo = realTime;

  const simulationSecTimeoutRef = useRef(null);
  const [isPausedSec, setIsPausedSec] = useState(false);
  const isPausedSecRef = useRef(isPausedSec);

  const simulationTimeoutSyncRef = useRef(null);
  const [isPausedKey, setIsPausedKey] = useState(false)
  const isPausedKeyRef = useRef(isPausedKey);


  let offsetRefPrimary = 0;
  let offsetRefSecondary = 0;
  let offsetRefKey = 0
  const limitPrimary = 10;
  const limitSecondary = 10;
  const limitKey = 10;



  /*=========================================
            1️⃣ Busca o simbolo Primario
   ========================================= */
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

  const LoadGraphicDataOne = async (symbolParam) => {
    console.log("LoadGraphicDataOne chamado com modo:", realTime, "e símbolo:", symbolParam);
    if (realTime === "real") {
      await graphicDataOne(symbolParam);
    } else if (realTime === "simulation") {
      await simulateStepSync(symbolParam);
    } else {
      console.warn("Modo inválido:", realTime);
    }
  };


  const simulateStepSync = async (symbolPrimary, symbolSecondary) => {
    // se não estiver em modo simulation, cancela
    if (realTime !== 'simulation') {
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

      // endpoints que você já usa
      const epPrimary = `${url}/api/simulate_price_atr`;
      const epSecondary = `${url}/api/simulate_price_atr_sec`;
      const epKey = `${url}/api/simulate_price_atr_key`;

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
        if (dateS > dateP) {
          // próximo é depois, para sem avançar
          break;
        }

        // registra o secondary
        setSimulationValueDataSec(prev => [...prev, parseFloat(candleS.closePrice)]);
        setSimulationLabelDataSec(prev => [...prev, candleS.closeTime]);

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
        if (dateK > dateP) {
          // próximo é depois, para sem avançar
          break;
        }

        // registra o key
        setSimulationValueDataKey(prev => [...prev, parseFloat(candleK.closePrice)]);
        setSimulationLabelDataKey(prev => [...prev, candleK.closeTime]);

        // avança para o próximo
        offsetRefKey += 1;
      }

      // agenda próxima iteração (próximo primary + catch-up)
      simulationTimeoutSyncRef.current = setTimeout(() => {
        simulateStepSync(symbolPrimary, symbolSecondary);
      }, 1000);

    } catch (error) {
      console.error("❌ Erro na simulateStepSync:", error);
      clearTimeout(simulationTimeoutSyncRef.current);
    }
  };


  const graphicDataOne = async (symbolParam) => {
    // 🧹 Limpa dados da simulação
    clearTimeout(simulationTimeoutRef.current);
    setSimulationValueData([]);
    setSimulationLabelData([]);

    try {
      const response = await axios.get(`${url}/api/filter_price_atr?symbol=${symbolParam}`);
      const data = response.data;

      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => p.closeTime.split(' ')[0]);

      setDadosPrice(data);
      setLabels(time);
      setValues(prices);

    } catch (error) {
      console.error("❌ Erro ao buscar dados em tempo real:", error);
    }
  };




  // faz pequisa do simbolo envia para backend
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
  /*================================================================================== */

  /*=========================================
            1️2️⃣ Busca o simbolo secundario
   ========================================= */
  const getSymbolSec = async (event) => {
    event?.preventDefault();
    try {
      const response = await axios.get(url + "/api/last_symbol_second")
      const data = response.data;
      setSymbolSec(data.symbol);
      return data.symbol;
    } catch (error) {
      console.error("Erro na API para recuperar símbolos:", error);
    }
  };

  const graphicDataSecondary = async (symbolSecParam) => {
    if (!symbolSecParam) return;

    // 🧹 Limpa dados da simulação
    clearTimeout(simulationSecTimeoutRef.current);
    setSimulationValueDataSec([]);
    setSimulationLabelDataSec([]);
    try {
      const response = await axios.get(`${url}/api/filter_price_atr_second?symbol=${symbolSecParam}`);
      const data = response.data;

      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => {
        return p.closeTime.split(' ')[0]; // Vai pegar só "27/05/2025"
      });


      setDadosPriceSecondary(data);
      setLabelsSecondary(time);
      setValuesSecondary(prices)
    } catch (error) {
      console.error("Erro na API para recuperar símbolos:", error);
    }
  }


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
  /*================================================================================== */


  /*=========================================
           1️2️⃣ Busca o simbolo Chave
  ========================================= */
  const graphicDataKey = async () => {
    try {
      const response = await axios.get(url + "/api/filter_price_key");
      const data = response.data;
      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => {
        // p.closeTime está como "27/05/2025 13:00:00"
        return p.closeTime.split(' ')[0];
      });


      setDadosPriceKey(data);
      setLabelsKey(time);
      setValueKey(prices);

    } catch (error) {
      console.error("Erro na API:", error);
    }
  };

  /*================================================================================== */

  /* manipula o tempo grafico */
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
        graphicDataOne(symbol)
        graphicDataSecondary(symbolSec)
        graphicDataKey()
        handleGetPoints()
        handleGetPointsKey()

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

  // 🔄 Pega o tempo gráfico salvo no banco
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


  // pega os pontos importantes
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


  // Função para adicionar/remover pivôs
  const togglePivot = (label, price, pivotName) => {
    setSelectedPivots(prev => {
      const exists = prev.find(p => p.valor === price && p.texto === label);
      if (exists) {
        return prev.filter(p => !(p.valor === price && p.texto === label));
      } else {
        return [...prev, { valor: price, texto: label, cor: 'white' }];
      }
    });
  };

  // pega pontos importantes chaves
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
      offsetRefSecondary = 0; // reinicia para caso volte pra simulação depois
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
            graphicDataSecondary(savedSymbolSec),
            graphicDataKey(),
            handleGetTime(),
            handleGetPoints(),
            handleGetPointsKey(),
          ]);
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
    graphicDataOne,
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
    simulationValueDataKey
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
