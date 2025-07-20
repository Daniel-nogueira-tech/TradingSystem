import React, { createContext, use, useEffect, useRef, useState } from 'react';
import Swal from 'sweetalert2';
import axios from 'axios';

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



  const graphicDataOne = async () => {
    try {
      const response = await axios.get(url + "/api/filter_price_atr")
      const data = response.data;
      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => p.closeTime);

      setDadosPrice(data);
      setLabels(time);
      setValues(prices);
    } catch (error) {
      console.error("Erro ao buscar dados da API:", error);
    }
  }

  const graphicDataSecondary = async () => {
    try {
      const response = await axios.get(url + "/api/filter_price_atr_secondy")
      const data = response.data;
      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => p.closeTime);

      setDadosPriceSecondary(data);
      setLabelsSecondary(time);
      setValuesSecondary(prices)

    } catch (error) {

    }
  }

  const graphicDataKey = async () => {
    try {
      const response = await axios.get(url + "/api/filter_price_key");
      const data = response.data;
      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => p.closeTime);

      setDadosPriceKey(data);
      setLabelsKey(time);
      setValueKey(prices);

    } catch (error) {
      console.error("Erro na API:", error);
    }
  };


  const handleSearch = async () => {
   inputRefMain.current.focus();

    const symbol = inputRefMain.current.value.toUpperCase();
    if (!symbol) return;

    try {
      const response = await axios.get(`${url}/api/filter_price_atr?symbol=${symbol}`);
      const data = response.data;

      // Exemplo: adaptando conforme seu backend retorna
      // Ajuste as propriedades conforme a resposta JSON
      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => p.closeTime);

      setLabels(time);
      setValues(prices);
      setDadosPrice(data);

      console.log('Dados atualizados:', { time, prices });
    } catch (error) {
      console.error('Erro ao buscar dados:', error);
    }
    inputRefMain.current.value = "";

  };


  const handleSearchSec = async () => {
   inputRefSec.current.focus();

    const symbol = inputRefSec.current.value.toUpperCase();
    if (!symbol) return;

    try {
      const response = await axios.get(`${url}/api/filter_price_atr_secondy?symbol=${symbol}`);
      const data = response.data;

      // Exemplo: adaptando conforme seu backend retorna
      // Ajuste as propriedades conforme a resposta JSON
      const prices = data.map(p => parseFloat(p.closePrice));
      const time = data.map(p => p.closeTime);

      setDadosPriceSecondary(data);
      setLabelsSecondary(time);
      setValuesSecondary(prices)

      console.log('Dados atualizados:', { time, prices });
    } catch (error) {
      console.error('Erro ao buscar dados:', error);
    }
    inputRefSec.current.value = "";

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
    // Aqui você pode salvar no localStorage, enviar pro backend, etc.
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
    async function loadData() {
      try {
        await Promise.all(
          [
            graphicDataOne(),
            graphicDataSecondary(),
            graphicDataKey(),
            handleSearchSec(),

          ]);
        // Atualiza a cada 60 segundos (60000 ms)
        const interval = setInterval(() => {
          graphicDataKey();

        }, 60000);
        // Limpa o intervalo quando desmontar
        return () => clearInterval(interval);

      } catch (error) {
        console.error("Erro ao carregar os dados iniciais:", error);
      }
    }
    loadData();
  }, []);

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
  };

  return (
    <AppContext.Provider value={contextValue}>
      {props.children}
    </AppContext.Provider>
  );
};

export default ContextApi;
