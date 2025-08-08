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
  const simulationTimeoutRef = useRef(null);
  const [isPaused, setIsPaused] = useState(false);
  const isPausedRef = useRef(isPaused);


  let offset = 0;
  const limit = 10;



  console.log("💾 Modo salvo:", realTime);

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
      await graphicDataOneSimulate(symbolParam);
    } else {
      console.warn("Modo inválido:", realTime);
    }
  };


  const graphicDataOne = async (symbolParam) => {
    console.log("Modo --:", realTime);

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


  const graphicDataOneSimulate = async (symbolParam) => {
    if (realTime !== 'simulation') {
      console.log("❌ Ignorando graphicDataOneSimulate: modo não é simulação, modo atual:", realTime);
      return;
    }
    try {
      const modo = realTime;

      await axios.get(`${url}/api/update_klines?symbol=${symbolParam}&modo=${modo}`);
      const response = await axios.get(`${url}/api/simulate_price_atr?offset=${offset}&limit=${limit}`);
      const data = response.data;

      if (data.length === 0) {
        console.log("✅ Simulação finalizada");
        return;
      }

      const exibirDados = (index) => {
        if (realTime !== 'simulation') {
          console.log("🛑 Modo mudou durante a simulação, encerrando...");
          return;
        }

        if (index >= data.length) {
          offset += limit;
          simulationTimeoutRef.current = setTimeout(() => {
            graphicDataOneSimulate(symbolParam);
          }, 100);
          return;
        }

        const candle = data[index];

        if (!isPausedRef.current) {
          console.log("🕒 Simulando:", candle.closeTime, candle.closePrice);
          setSimulationValueData(prev => [...prev, parseFloat(candle.closePrice)]);
          setSimulationLabelData(prev => [...prev, candle.closeTime.split(' ')[0]]);

          simulationTimeoutRef.current = setTimeout(() => exibirDados(index + 1), 100);
        } else {
          // Pausado: tenta de novo o mesmo index após delay
          console.log("⏸️ Pausado...");
          simulationTimeoutRef.current = setTimeout(() => exibirDados(index), 100);
        }

      };

      exibirDados(0);
    } catch (error) {
      console.error("❌ Erro ao buscar dados de simulação:", error);
      clearTimeout(simulationTimeoutRef.current);
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
    try {
      const response = await axios.get(`${url}/api/filter_price_atr_second?symbol=${symbolSecParam}`);
      const data = response.data;

      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => {
        // p.closeTime está como "27/05/2025 13:00:00"
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
      setSimulationValueData([]);
      setSimulationLabelData([]);
      offset = 0; // reinicia para caso volte pra simulação depois
    }
  }, [realTime]);


  useEffect(() => {
    isPausedRef.current = isPaused;
  }, [isPaused]);



  useEffect(() => {
    async function loadData() {
      try {
        const savedSymbol = await getSymbol();
        const savedSymbolSec = await getSymbolSec();

        if (savedSymbol || savedSymbolSec) {
          await Promise.all([
            LoadGraphicDataOne(savedSymbol),
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

    const interval = setInterval(async () => {
      try {
        await Promise.all([
          graphicDataSecondary(symbolSec),
          graphicDataKey(),
          handleGetPoints(),
          handleGetPointsKey(),
        ]);
      } catch (error) {
        console.error("Erro ao atualizar dados no intervalo:", error);
      }
    }, 60000);

    return () => clearInterval(interval);
  }, [symbol, symbolSec, realTime]); // Adicione realTime como dependência


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
    isPausedRef
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
