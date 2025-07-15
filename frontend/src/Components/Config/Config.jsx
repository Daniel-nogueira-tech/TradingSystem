import React, { useState } from 'react';
import './Config.css';
import Swal from 'sweetalert2';
import { useContext } from 'react';
import { AppContext } from '../../ContextApi/ContextApi';
import { useEffect } from 'react';


const Config = () => {
  const { handleSave, handleRemove,theme,setTheme } = useContext(AppContext);
  const [notifications, setNotifications] = useState(true);
  const [language, setLanguage] = useState('pt-BR');
  const [currency, setCurrency] = useState('BRL');

    // pega o tema do localStorage e exibe para o usuario
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, []);


  // funcao para mudar tema e salvar no localStorage
  useEffect(() => {
    if (theme === 'clear-theme') {
      document.body.classList.add('clear-theme');
      document.body.classList.remove('dark');
    } else {
      document.body.classList.remove('clear-theme');
      document.body.classList.add('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

    const keyApi = {
    'key': '6fgh65hf654h4dfgg5656gh5655gf5fdg54f5gj5gkj5jkl665sdfr6ds26g26'
  }



  return (
    <div className="config-main-primary">
      <div className="config-main">
        <h2>Configurações do Aplicativo</h2>

        <div className="config-group">
          <label>Tema:</label>
          <select value={theme} onChange={(e) => setTheme(e.target.value)}>
            <option value="dark">Dark</option>
            <option value="clear-theme">Soft dark</option>
          </select>
        </div>

        <div className="config-group">
          <label>Notificações de Preço:</label>
          <input className='checkbox'
            type="checkbox"
            checked={notifications}
            onChange={() => setNotifications(!notifications)}
          />
        </div>

        <div className="config-group">
          <label>Idioma:</label>
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="pt-BR">Português (BR)</option>
            <option value="en-US">Inglês (US)</option>
            <option value="es-ES">Espanhol</option>
          </select>
        </div>

        <div className="config-group">
          <label>Moeda Padrão:</label>
          <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
            <option value="BRL">Real (BRL)</option>
            <option value="USD">Dólar (USD)</option>
            <option value="EUR">Euro (EUR)</option>
          </select>
        </div>

        <button className="save-button" onClick={handleSave}>
          Salvar Configurações
        </button>
      </div>

      {/* Chave de api */}
      <div className="config-main">
        <h2>Configurar chave api</h2>

        <div className="config-group">
          <label>Chave:</label>
          <div className='config-input' >
            <input type="text" placeholder='Digite sua chave' />
          </div>
        </div>

        <button className="save-button" onClick={handleSave}>
          Salvar Chave
        </button>
      </div>


      {/* Chave de api */}
      <div className="config-main">
        <h2>Remover chave</h2>

        <div className="config-group">
          <label>Chave:</label>
          <p className='config-input-key'>
            {keyApi.key
              ? '•'.repeat(keyApi.key.length - 4) + keyApi.key.slice(-4)
              : 'Nenhuma chave cadastrada'}

          </p>

        </div>
        <button className="save-button" id='remover-button' onClick={handleRemove}>
          Remover Chave
        </button>
      </div>
    </div>
  );
};

export default Config;
