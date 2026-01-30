# 📈 Trading System – Algoritmo de Trading para Criptomoedas

Este projeto é um **Trading System algorítmico para criptomoedas**, desenvolvido como uma **aplicação desktop** utilizando **Electron** no frontend e uma arquitetura preparada para integração com **backends de análise de mercado**.

O foco do sistema é **análise de estrutura de mercado**, identificação de **tendências, rallies, reações e reversões**, com base em **movimentos de preço relativos ao ATR (Average True Range)** — uma abordagem inspirada diretamente no **sistema clássico de Jesse Livermore**, adaptado para lógica algorítmica moderna, evitando indicadores mágicos e privilegiando a leitura estrutural do preço.

---

## 🧠 Conceito do Algoritmo

O algoritmo parte de uma premissa simples e poderosa:

> O mercado se move em **estruturas**, não em sinais isolados.

Em vez de depender apenas de indicadores tradicionais, o sistema classifica o preço em **estados de mercado**, como:

* Tendência de alta / baixa
* Rally natural
* Reação natural
* Reação secundária
* Pontos de reversão confirmados

Esses estados são definidos com base em:

* Variação de preço
* ATR como unidade de medida do movimento
* Pontos de referência (pivôs, rallies e fundos)

O resultado é um modelo mais **interpretável**, **auditável** e **adaptável**.

---

## 🖥️ Arquitetura do Projeto

O projeto é dividido em três camadas principais:

* **Frontend (Vite + Electron)**

  * Interface gráfica desktop
  * Visualização de preços e estados do mercado
  * Controles de simulação e execução

* **Electron (Main Process)**

  * Gerenciamento da aplicação desktop
  * Comunicação entre UI e serviços locais

* **Backend (externo via proxy)**

  * Implementado em **Python**
  * Fonte de dados de mercado
  * Cálculo de ATR e classificação dos movimentos
  * Simulação e backtest

---

## 🛠️ Tecnologias Utilizadas

### Backend (Python)

* **Python**
* Lógica de classificação estrutural do mercado
* Cálculo de ATR e pontos de referência
* APIs de dados (ex: Binance ou base local)

### Frontend / Desktop

* **Electron** – aplicação desktop multiplataforma
* **Vite** – build rápido do frontend
* **JavaScript (CommonJS)**
* **PrimeReact** – componentes de UI
* **Node.js** – runtime
* **Proxy HTTP** para backend local

---

## 📦 Scripts Disponíveis

```
npm run start     # Inicia o frontend (Vite)
npm run electron  # Inicia apenas o Electron
npm run dev       # Frontend + Electron simultaneamente
npm run build     # Build de produção
```

---

## 🔌 Integração com Backend

O frontend se comunica com um backend através de proxy:

```
http://localhost:5000
```

Esse backend pode fornecer:

* Dados de candles (Binance, banco local ou simulação)
* Cálculo de ATR
* Classificação de estados do mercado
* Modo simulação (backtest visual)

Isso mantém o sistema **desacoplado** e fácil de evoluir.

---

## 📊 Funcionalidades Principais

* Visualização de preços em tempo real ou simulado
* Classificação automática do estado do mercado
* Simulação candle a candle (backtest)
* Detecção de possíveis reversões de tendência
* Base para alertas e estratégias automáticas

---

## 🧪 Modo Simulação

O sistema permite rodar o mercado em **modo simulado**, reproduzindo candles históricos de forma gradual.

Isso possibilita:

* Testar o algoritmo visualmente
* Validar transições de estado
* Analisar comportamento do mercado sem risco financeiro

---

## 📂 Estrutura de Pastas (simplificada)

```
tradingsystem/
├── electron/
│   └── main.js
├── src/
│   ├── components/
│   ├── services/
│   ├── contexts/
│   └── views/
├── dist/
├── package.json
└── vite.config.js
```

---

## 🚀 Possíveis Evoluções

* Execução automática de ordens (paper trade)
* Integração com corretoras (Binance, Bybit, etc.)
* Sistema de alertas por estado de mercado
* Otimização automática de parâmetros
* Machine Learning para validação de padrões
* Painel estatístico de performance

---

## 📚 Referência Teórica

O modelo de leitura de mercado deste sistema é fortemente inspirado nos princípios de **Jesse Livermore**, especialmente:

* Identificação de tendências primárias
* Importância dos rallies e reações naturais
* Confirmação de movimentos antes da tomada de decisão
* Respeito à estrutura do mercado acima de previsões

Esses conceitos foram traduzidos para regras explícitas, estados de mercado e validações quantitativas baseadas em ATR.

---

## ⚠️ Aviso Importante

Este projeto **não é uma recomendação de investimento**.

O sistema foi desenvolvido para **estudo, análise e experimentação**, e qualquer uso em ambiente real deve ser feito com cautela, gerenciamento de risco e validação extensiva.

---

## 📜 Licença

Este projeto está licenciado sob a **ISC License**.

---

## 🧩 Consideração Final

Trading algorítmico não é sobre prever o futuro — é sobre **reagir corretamente a estruturas que já existem**.

Este projeto busca transformar leitura de mercado em **código explícito**, algo que pode ser estudado, testado, criticado e melhorado continuamente.
