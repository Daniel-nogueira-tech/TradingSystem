import React, { createContext, useEffect, useState } from 'react';
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

          ]);

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
    setTheme
  };

  return (
    <AppContext.Provider value={contextValue}>
      {props.children}
    </AppContext.Provider>
  );
};

export default ContextApi;
