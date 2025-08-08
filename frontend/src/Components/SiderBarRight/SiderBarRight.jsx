import React, { useContext, useState } from 'react';
import './SiderBarRight.css';
import { useEffect } from 'react';
import { AppContext } from '../../ContextApi/ContextApi';

const SiderBarRight = () => {
    const [quantity, setQuantity] = useState(0.01);
    const [isOn, setIsOn] = useState(false);
    const [activeAlgorithm, setActiveAlgorithm] = useState('')
    const { setRealTime, realTime } = useContext(AppContext);

    const toggleSwitch = () => setIsOn(!isOn);
    useEffect(() => {
        if (isOn) {
            setActiveAlgorithm('Ativado')
        } else {
            setActiveAlgorithm('Desativado')
        }
    }, [isOn]);



    const handleBuy = () => {
        console.log(`Comprando ${quantity} unidade(s)`);
    };

    const handleSell = () => {
        console.log(`Vendendo ${quantity} unidade(s)`);
    };



    return (
        <div className="right-sidebar">
            <h3>Ordem Rápida</h3>

            <select
                className='accountSimulation'
                value={realTime}
                onChange={(e) => {
                    const modo = e.target.value;
                    setRealTime(modo);
                    localStorage.setItem("realTimeMode", modo);
                }}
            >
                <option value="simulation">Simulação</option>
                <option value="real">Real time</option>
            </select>

            <label>Quantidade:</label>
            <input
                type="number"
                step="0.01"
                min="0.01"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
            />

            <button className="buy-btn" onClick={handleBuy}>
                Comprar
            </button>

            <button className="sell-btn" onClick={handleSell}>
                Vender
            </button>

            <button className="sell-btn" onClick={handleSell}>
                Zerar
            </button>

            <div>
                <h3>Resultado: </h3>
                <div className='result'>
                    <p className='result-text'>R$ 2500,00</p>
                </div>
            </div>

            <div className='switch-container'>
                <label className="switch">
                    <input type="checkbox" checked={isOn} onChange={toggleSwitch} />
                    <span className="slider"></span>
                </label>
                <p>{activeAlgorithm}</p>
            </div>
        </div>
    );
};

export default SiderBarRight;
